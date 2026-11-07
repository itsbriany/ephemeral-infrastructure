"""Approved workload profiles; public requests never supply infrastructure definitions."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApplicationProfile:
    application_id: str
    display_name: str
    container_port: int
    health_path: str
    cpu_units: int
    memory_mib: int
    session_minutes: int
    max_lifetime_minutes: int

    def __post_init__(self) -> None:
        if not self.application_id or not self.application_id.replace("-", "").isalnum():
            raise ValueError("application_id must contain letters, numbers, or hyphens")
        if not self.health_path.startswith("/"):
            raise ValueError("health_path must begin with '/'")
        if self.session_minutes <= 0:
            raise ValueError("session_minutes must be positive")
        if self.max_lifetime_minutes < self.session_minutes:
            raise ValueError("max_lifetime_minutes cannot be shorter than the session")


HELLO_ENVIRONMENT = ApplicationProfile(
    application_id="hello-environment",
    display_name="Hello Environment",
    container_port=8080,
    health_path="/health",
    cpu_units=256,
    memory_mib=512,
    session_minutes=15,
    max_lifetime_minutes=30,
)

APPLICATION_CATALOG: dict[str, ApplicationProfile] = {
    HELLO_ENVIRONMENT.application_id: HELLO_ENVIRONMENT,
}
