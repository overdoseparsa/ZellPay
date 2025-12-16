from abc import ABC, abstractmethod

from typing import (
    Dict,
    Any,
    Optional,

)

from logging import getLogger
from handler import RequestZarinpallHandeler , AbstractTransactionHandler


from exceptions import RequestPayloadError

logger = getLogger(__name__)



class RequestPayloadError(BaseException):
    """
    Raised when the payment request payload is invalid or cannot be processed.
    """

    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.payload = payload or {}

        logger.error(f"RequestPayloadError: {self.message} | Payload: {self.payload}")

    def __str__(self) -> str:
        return f"RequestPayloadError(message={self.message}, payload={self.payload})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert error details to dictionary for API response or logging."""
        return {
            "error": "RequestPayloadError",
            "message": self.message,
            "payload": self.payload,
        }
