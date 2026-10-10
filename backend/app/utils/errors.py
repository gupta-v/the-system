"""Domain errors raised by core/services and mapped to HTTP responses in app/main.py."""


class DomainError(Exception):
    """Base class. `message` is shown to the Player as a System notice."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFound(DomainError):
    status_code = 404


class Conflict(DomainError):
    status_code = 409


class Unauthorized(DomainError):
    status_code = 401


class InvalidAction(DomainError):
    status_code = 422
