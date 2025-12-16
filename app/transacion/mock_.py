"""
Mock provider for Zarinpal-like API to eliminate network side effects during tests.

This module mirrors the signature of provider.send_request_zarinpall and returns a
deterministic, success-shaped response while echoing back request inputs for assertions.
"""

from typing import Dict, Any, Optional
from logging import getLogger
import time
import hashlib
import os

logger = getLogger(__name__)

DEFAULT_TIMEOUT = 5


def _generate_mock_authority(prefix: str = "A") -> str:
    """Generate a stable-looking mock authority code."""
    seed = f"{time.time_ns()}:{os.getpid()}"
    digest = hashlib.sha256(seed.encode()).hexdigest()
    # Zarinpal authorities are long; keep shape similar but clearly mock
    return f"{prefix}{digest[:31]}"


def send_request_zarinpall_mock(
    ZP_API_REQUEST: Optional[str] = None,
    MERCHANT: Optional[str] = None,
    callbackURL: Optional[str] = None,
    amount: Optional[str] = None,
    description: Optional[str] = None,
    email: Optional[str] = None,
    mobile: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Return a mock success response and echo the request fields for testing.

    Args mirror provider.send_request_zarinpall. All validations are relaxed by design
    to avoid side effects and external dependencies during tests.
    """
    # Build request echo
    metadata = kwargs.get("metadata") or {}
    if email or mobile:
        metadata = {**metadata, **({"email": email} if email else {}), **({"mobile": mobile} if mobile else {})}

    request_echo: Dict[str, Any] = {
        "amount": int(amount) if isinstance(amount, str) and amount.isdigit() else amount,
        "callback_url": callbackURL,
        "referrer_id": kwargs.get("referrer_id") or kwargs.get("referrer") or kwargs.get("reference_id"),
        "description": description,
        "metadata": metadata or {},
    }
    print("zarinpall mock request" , request_echo)
    # Compose fixed success-shaped response
    response: Dict[str, Any] = {
        "status": "success",
        "data": {
            "code": 100,
            "message": "Success",
            "authority": _generate_mock_authority("A"),
            "fee_type": "Merchant",
            "fee": 100,
            # Include the request echo inside data for easy assertions
            "request": request_echo,
        },
        "errors": [],
    }

    logger.info("Returning mock Zarinpal request response (no side effects)")
    logger.debug("Mock response payload: %s", response)
    return response


def main():
    response = send_request_zarinpall_mock()
    print(
        response
    )

if __name__ =='__main__':
    main()