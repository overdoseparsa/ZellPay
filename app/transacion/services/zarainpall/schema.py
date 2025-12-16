from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import uuid4, UUID
import json




"""
Prepare and validate incoming transaction payload.

Args:
    data (Dict[str, Any]): Raw transaction payload containing:
        - order_id (str | int): Unique order identifier
        - user_id (UUID, optional): User identifier (generated if missing)
        - gateway_id (str | int): Payment gateway ID
        - amount (str | int): Transaction amount
        - currency (str, optional): Currency code (default: IRR)
        - description (str): Transaction description
        - authority_code (str): Payment authority code from provider
        - ref_id (str, optional): Reference ID (initially empty)
        - meta (dict | list | str, optional): Additional metadata
        - idempotency_key (str, optional): Key used to prevent duplicate transactions

Returns:
    Tuple[int, UUID]: A tuple containing:
        - status code (0 meaning success)
        - transaction UUID assigned to the record
"""


class TransactionData(BaseModel):
    order_id: str
    user_id: UUID = Field(default_factory=uuid4)
    gateway_id: int
    amount: int
    currency: str = "IRR"
    description: str
    authority_code: str
    ref_id: Optional[str] = ""
    meta: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None

    # هنگام خروجی dict همه چیز str می‌شود
    def dict(self, *args, **kwargs):
        original = super().dict(*args, **kwargs)
        converted = {}

        for k, v in original.items():
            if v is None:
                converted[k] = None
            elif isinstance(v, (dict, list)):
                converted[k] = json.dumps(v, ensure_ascii=False)
            else:
                converted[k] = str(v)
        return converted
