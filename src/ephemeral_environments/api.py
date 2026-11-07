"""Milestone 1 local HTTP API for the provider-neutral lifecycle contract."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from ephemeral_environments.application_profiles import (
    APPLICATION_CATALOG,
    ApplicationProfile,
)
from ephemeral_environments.environment import EnvironmentRecord
from ephemeral_environments.lifecycle import EnvironmentStatus
from ephemeral_environments.provisioner import FakeProvisioner
from ephemeral_environments.repository import (
    EnvironmentNotFound,
    IdempotencyConflict,
    InMemoryEnvironmentRepository,
)
from ephemeral_environments.service import ApplicationNotApproved, EnvironmentService


def _to_camel(name: str) -> str:
    first, *rest = name.split("_")
    return first + "".join(word.capitalize() for word in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)


class ApplicationResponse(ApiModel):
    application_id: str
    display_name: str
    session_minutes: int
    max_lifetime_minutes: int

    @classmethod
    def from_profile(cls, profile: ApplicationProfile) -> "ApplicationResponse":
        return cls.model_validate(profile, from_attributes=True)


class CreateEnvironmentRequest(ApiModel):
    application_id: str = Field(min_length=1, max_length=64)


class EnvironmentResponse(ApiModel):
    environment_id: str
    application_id: str
    status: EnvironmentStatus
    created_at: datetime
    updated_at: datetime
    ready_at: datetime | None
    destroyed_at: datetime | None
    endpoint: str | None

    @classmethod
    def from_record(cls, record: EnvironmentRecord) -> "EnvironmentResponse":
        return cls.model_validate(record, from_attributes=True)


def create_app(*, step_delay_seconds: float = 0.05) -> FastAPI:
    repository = InMemoryEnvironmentRepository()
    provisioner = FakeProvisioner(repository, step_delay_seconds=step_delay_seconds)
    service = EnvironmentService(
        catalog=APPLICATION_CATALOG,
        repository=repository,
        provisioner=provisioner,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await provisioner.start()
        try:
            yield
        finally:
            await provisioner.stop()

    app = FastAPI(
        title="Ephemeral Environments Local API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.service = service
    app.state.repository = repository

    def service_for(request: Request) -> EnvironmentService:
        return request.app.state.service

    @app.get("/applications", response_model=list[ApplicationResponse])
    async def list_applications(request: Request) -> list[ApplicationResponse]:
        return [
            ApplicationResponse.from_profile(profile)
            for profile in service_for(request).list_applications()
        ]

    @app.post(
        "/environments",
        response_model=EnvironmentResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def create_environment(
        body: CreateEnvironmentRequest,
        request: Request,
        response: Response,
        idempotency_key: Annotated[
            str,
            Header(alias="Idempotency-Key", min_length=1, max_length=128),
        ],
    ) -> EnvironmentResponse:
        normalized_key = idempotency_key.strip()
        if not normalized_key:
            raise HTTPException(status_code=422, detail="Idempotency-Key cannot be blank")
        try:
            reservation = await service_for(request).create_environment(
                application_id=body.application_id,
                idempotency_key=normalized_key,
            )
        except ApplicationNotApproved as error:
            raise HTTPException(status_code=422, detail="Application is not approved") from error
        except IdempotencyConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

        response.headers["Idempotency-Replayed"] = str(not reservation.created).lower()
        return EnvironmentResponse.from_record(reservation.record)

    @app.get("/environments/{environment_id}", response_model=EnvironmentResponse)
    async def get_environment(environment_id: str, request: Request) -> EnvironmentResponse:
        try:
            record = await service_for(request).get_environment(environment_id)
        except EnvironmentNotFound as error:
            raise HTTPException(status_code=404, detail="Environment not found") from error
        return EnvironmentResponse.from_record(record)

    @app.delete(
        "/environments/{environment_id}",
        response_model=EnvironmentResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def terminate_environment(environment_id: str, request: Request) -> EnvironmentResponse:
        try:
            record = await service_for(request).terminate_environment(environment_id)
        except EnvironmentNotFound as error:
            raise HTTPException(status_code=404, detail="Environment not found") from error
        return EnvironmentResponse.from_record(record)

    return app


app = create_app()
