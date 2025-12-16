from typing import Dict, Any, Optional
from uuid import UUID
from psycopg import IntegrityError

def insert_transaction_to_db(conn, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Insert a transaction into the database and return the resulting row.

    Args:
        conn: Database connection object.
        transaction_data: Dictionary containing transaction fields.

    Returns:
        Dict with inserted transaction info, or None if failed.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO transactions (
                    order_id,
                    user_id,
                    gateway_id,
                    amount,
                    currency,
                    description,
                    authority_code,
                    ref_id,
                    meta,
                    idempotency_key,
                    is_done,
                    is_added_wallet,
                    is_refund
                ) VALUES (
                    %(order_id)s,
                    %(user_id)s,
                    %(gateway_id)s,
                    %(amount)s,
                    %(currency)s,
                    %(description)s,
                    %(authority_code)s,
                    %(ref_id)s,
                    %(meta)s::s,
                    %(idempotency_key)s,
                    false,
                    false,
                    false
                ) RETURNING transaction_uuid::text, order_id, user_id::text, gateway_id, amount, currency, description, authority_code, ref_id
            """, transaction_data)
            
            result = cur.fetchone()
            if not result:
                conn.rollback()
                return None
            return result
    except IntegrityError as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        raise e


import json
import logging

logger = logging.getLogger(__name__)

def cache_transaction(
    client: Any,
    transaction_uuid: str,
    transaction_data: Dict[str, Any],
    ttl: int = 3
) -> bool:
    """
    Cache transaction data in Redis using a hash.

    Args:
        client: Redis client instance
        transaction_uuid: UUID of the transaction
        transaction_data: Dictionary of transaction data
        ttl: Time to live in seconds (default: 3)

    Returns:
        bool: True if caching succeeded, False otherwise
    """
    try:
        cache_key = f"transaction:{transaction_uuid}"

        client.hset(cache_key, mapping=transaction_data)
        client.expire(cache_key, ttl)

        logger.info(f"Transaction cached: {transaction_uuid}")
        return True
    except Exception as e:
        logger.error(f"Failed to cache transaction {transaction_uuid}: {e}", exc_info=True)
        return False

