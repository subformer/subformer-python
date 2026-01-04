"""Exceptions for Subformer SDK."""

from typing import Any, Optional


class SubformerError(Exception):
    """Base exception for Subformer SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        data: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.data = data

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(SubformerError):
    """Raised when API authentication fails."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401, code="UNAUTHORIZED")


class NotFoundError(SubformerError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404, code="NOT_FOUND")


class RateLimitError(SubformerError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429, code="RATE_LIMIT_EXCEEDED")


class ValidationError(SubformerError):
    """Raised when request validation fails."""

    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(message, status_code=400, code="BAD_REQUEST", data=data)
