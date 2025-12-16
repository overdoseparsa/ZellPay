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



from abc import ABC, abstractmethod

from typing import (
    Dict,
    Any,
    Optional,
    Union,
    Tuple,
)

from uuid import UUID
from functools import wraps
from logging import getLogger



class RequestZarinpallHandeler(AbstractTransactionHandler):
    """
    Database repository implementation for transaction operations.
    Uses connection pool for efficient database access.
    """

        
    def validate_transaction_payload(self,data:Dict[str, Any])->bool:
        data = {
                'order_id': str(data['order_id']),
                'user_id': uuid4(), # we havt to create this micro service 
                'gateway_id': int(data['gateway_id']),
                'amount': int(data['amount']),
                'currency': str(data.get('currency', 'IRR')),
                'description': str(data['description']),
                'authority_code': str(data['authority_code']),
                'ref_id': str(data.get('ref_id', '')),
                'meta': str(data.get('meta', {})) if data.get('meta') else None, # TODO this is so slow in  Python
                'idempotency_key': data.get('idempotency_key')
            }
        transaction_data = TransactionData(**data)
        return transaction_data.dict()
    
    def save_transaction(self,
                         data: Dict[str, Any],
                         evant: Dict[str, Any]
                         ) -> Tuple[int, UUID]:
        

        self.pyload
        try:  
            with self.db_manager.Connection(
                IsolationLevel.SERIALIZABLE ,  # TODO refrence http://refreence
                    row_factory='dict'
                ) as conn:


                result= insert_transaction_to_db(
                    conn,
                    self.pyload
                )

                transaction_uuid = result['transaction_uuid'] if result else None
                    
                if not transaction_uuid:
                    logger.error("Failed to get transaction UUID after insert")
                    conn.rollback() # dont save ransaction 
                    return (3, "Failed to get transaction UUID after insert",None)
                    


                logger.info(f"Transaction saved successfully: {transaction_uuid}")

                with self.RedisManager.get_client() as client :
                    is_cache = cache_transaction(
                        client,
                        transaction_uuid=transaction_uuid,
                        transaction_data=self.pyload
                    )
                    if is_cache:
                        logger.info(f"Cached ! {transaction_uuid}")
                    
                return (0, transaction_uuid,transaction_data['authority_code'])
        
        except Exception as E:
            logger.error(f"Faild to save {E}")
            raise 

    
    def _check_authority_code(self, authority_code: str) -> Optional[Dict[str, Any]]:
        """Check if transaction with authority_code exists"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory='dict') as cur:
                    cur.execute("""
                        SELECT transaction_uuid
                        FROM transactions
                        WHERE authority_code = %s
                    """, (authority_code,))
                    
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error checking authority code: {e}")
            return None
    
    def _get_status_string(self, transaction: Dict[str, Any]) -> str:
        """Get status string from transaction data"""
        if transaction.get('is_refund'):
            return 'refunded'
        elif transaction.get('is_done'):
            if transaction.get('is_added_wallet'):
                return 'completed_and_added'
            return 'completed'
        return 'pending'
    
    def _log_transaction_event( # TODO convert this to the function  in  the postgresql
        self,
        Cursor : Connection  , 
        transaction_uuid: UUID, 
        old_status: str,
        new_status: str,
        event_source: str,
        payload: Dict[str, Any],
        provider_ip: str = '0.0.0.0'
    ) -> bool:
        """
        Log transaction event to transaction_event table.
        
        Args:
            transaction_uuid: Transaction UUID
            old_status: Previous status
            new_status: New status
            event_source: Source of the event
            payload: Event payload data
            provider_ip: IP address of provider (default: '0.0.0.0')
        
        Returns:
            bool: True if logged successfully
        """
        try:
            print("""
                    INSERT INTO transaction_event (
                            transaction_id,
                            old_status,
                            new_status,
                            event_source,
                            payload,
                            provider_ip
                        ) VALUES (
                            %s::uuid,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        ) RETURNING id
                    """,(
                        (transaction_uuid),
                        old_status,
                        new_status,
                        event_source,
                        f"{payload}",
                        provider_ip
                    ))
                    
            Cursor.execute("""
                    INSERT INTO transaction_event (
                            transaction_id,
                            old_status,
                            new_status,
                            event_source,
                            payload,
                            provider_ip
                        ) VALUES (
                            %s::uuid,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        ) RETURNING id
                    """,(
                        (transaction_uuid),
                        old_status,
                        new_status,
                        event_source,
                        f"{payload}",
                        provider_ip
                    ))
                    
            # result = Cursor.fetchone()
            # print('resualt is ' , result)


            result = Cursor.fetchone()
            print('resualt is ' , result)
            if result:
                logger.debug(f"Transaction event logged: {transaction_uuid} ({old_status} -> {new_status})")
                return True
            return False
                    
        except Exception as e:
            logger.error(f"Error logging transaction event: {e}", exc_info=True)
            return False