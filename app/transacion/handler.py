from abc import ABC , abstractmethod
from typing import (
    Dict,
    Any,
    Optional,
    Tuple
)
from uuid import UUID , uuid4
from logging import getLogger

from psycopg import IsolationLevel 
from psycopg.errors import IntegrityError
from psycopg.connection import  Connection

from uuid import UUID
import json

# from app.models.interface import RedisManager , PostgresDatabaseManager
from test11 import *


logger = getLogger(__name__)

class AbstractTransactionHandler(ABC):
    """ AbstractHandler mixin for transaction operations"""
    parse = [

    ]
    def __init__(self,
                data , 
                DatabaseManager:PostgresDatabaseManager,
                CacheManager,
                ):
    

        self.pyload = self.validate_transaction_payload(data)
        self.db_manager = DatabaseManager
        self.cache_manager = CacheManager


    def save_transaction(self, data: Dict[str, Any]) -> Tuple[int, UUID]:
        pass 
        
    def validate_transaction_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate transaction payload data.
        
        Args:
            data: Transaction data dictionary
        
        Returns:
            bool: True if valid, False otherwise
        """
        raise NotImplementedError("validate_transaction_payload must be implemented")
    
    
    @abstractmethod
    def save_in_cache(self ,
                transaction_data:Dict[str,Any] ,
                transaction_uuid : UUID | str

                )->None:
        
        """
        In This Case we use cache add Transaction
        """



class AbstractCacheHandler(ABC):
    @abstractmethod
    def cache_transaction(self):
        pass
    
class RedisHandler: 
    """Manages transaction caching in Redis"""
    
    def __init__(self, redis_manager: RedisManager , cache_ttl=3600):
        self.redis_manager = redis_manager
        self.cache_ttl = cache_ttl  # 1 hour
    
    def cache_transaction(self, transaction_uuid: str, transaction_data: Dict[str, Any]) -> bool:
        """Cache transaction data in Redis"""
        try: # TODO create cahce with auto key and values 
            print('start cache')
            with self.redis_manager.get_client() as client:
                cache_key = f"transaction:{str(transaction_uuid)}" # TODO check the amout is smiliar from transaction
                client.hset(cache_key, mapping=transaction_data)
                client.expire(cache_key, self.cache_ttl)
                logger.info(f"Transaction cached: {transaction_uuid}")
                return True
        except Exception as e:
            logger.error(f"Failed to cache transaction {transaction_uuid}: {e}")
            return False
    

class RequestZarinpallHandeler(AbstractTransactionHandler):
    """
    Database repository implementation for transaction operations.
    Uses connection pool for efficient database access.
    """



    def save_transaction(self,
                         data: Dict[str, Any],
                         evant: Dict[str, Any]
                         ) -> Tuple[int, UUID]:
        
        """
        Save transaction to database. if we need zarain pall or from some others 
        
        Args:
            data: Transaction data dictionary containing:
                - order_id: Order identifier (required)
                - user_id: User UUID (required)
                - gateway_id: Payment gateway ID (required)
                - amount: Transaction amount (required)
                - currency: Currency code (required, default: 'IRR')
                - description: Transaction description (required)
                - authority_code: Payment authority code (required)
                - ref_id: Reference ID (optional, default: '')
                - meta: Additional metadata (optional, default: {})
                - idempotency_key: Idempotency key (optional)
        
        Returns:
            Tuple[int, UUID]: Status code (0 for success) and transaction UUID
        """

        try:  
            # TODO convert to the function or producer 
            transaction_data = {
                'order_id': str(data['order_id']),
                'user_id': uuid4(),
                'gateway_id': int(data['gateway_id']),
                'amount': int(data['amount']),
                'currency': str(data.get('currency', 'IRR')),
                'description': str(data['description']),
                'authority_code': str(data['authority_code']),
                'ref_id': str(data.get('ref_id', '')),
                'meta': str(data.get('meta', {})) if data.get('meta') else None, # TODO this is so slow in  Python
                'idempotency_key': data.get('idempotency_key')
            }

            with self.db_manager.Connection(
                IsolationLevel.SERIALIZABLE ,  
                row_factory='dict'
                ) as conn:
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
                            %(meta)s::jsonb,
                            %(idempotency_key)s,
                            false,
                            false,
                            false
                        ) RETURNING transaction_uuid::text , order_id , user_id::text , gateway_id , amount , currency , description , authority_code , ref_id 
                    """, transaction_data) 
                    
                    result = cur.fetchone()
                    print("uuid resualt : " , result ,  )
                    print(
                        type(result['transaction_uuid'])
                    )
                    transaction_uuid = result['transaction_uuid'] if result else None
                    
                    if not transaction_uuid:
                        logger.error("Failed to get transaction UUID after insert")
                        conn.rollback() # dont save ransaction 
                        return (3, "Failed to get transaction UUID after insert",None)
                    

                    # self._log_transaction_event( # TODO add to the mongo db  
                    #     Cursor = cur , 
                    #     transaction_uuid=transaction_uuid,
                    #     old_status='new',
                    #     new_status='created',
                    #     event_source='payment_gateway',
                    #     payload={'action': 'transaction_created', 'data': str(transaction_data),'response_data':str(evant)},
                    #     provider_ip='0.0.0.0'  # Should be extracted from request
                    # ) , "Can Not Persit the log event"
                    
                    logger.info(f"Transaction saved successfully: {transaction_uuid}")

                    self.save_in_cache(
                        transaction_uuid=transaction_uuid , 
                        transaction_data=result ,
                    )
                    return (0, transaction_uuid,transaction_data['authority_code'])

        except IntegrityError as e:
            logger.error(f"Integrity error saving transaction: {e}")
            return (4, 'Integrity error saving transaction',None)
        except Exception as e:
            logger.error(f"Error saving transaction: {e}", exc_info=True)
            return (5, 'Error saving transaction',None)
        
    def save_in_cache(self ,
                transaction_data:Dict[str,Any] ,
                transaction_uuid : UUID | str

                )-> None:
        # dumps and serializer all data

        if self.RedisHandler.cache_transaction(
                transaction_uuid=transaction_uuid,
                transaction_data=transaction_data
            ):
            logger.info('Save Transacction Cache:')

        

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
    
def main():


    class TEST:
        def __init__(self):

            print('init_testing')
            self.config = DatabaseConfig()
            self.db_manger =  PostgresDatabaseManager(self.config)
            self.redis_manger = RedisManager(
                    RedisConfig(

                    )
                )

            self.transaction_redis = RedisHandler(
                    self.redis_manger
                )



                # TEST TIME OUT TRANSACTION 
                # TEST THE SAVE TRANSACTION IN MOCD AND CERTIAN SIDE EFFECT 
       
#         def action(self):
#             self.database_reposiroy = ZarinpallHandeler(
#                     self.db_manger , self.transaction_redis
#                 )

#             self.uuid = self.database_reposiroy.save_transaction(
#                 data = {'order_id': str(uuid4()),
#                 'user_id': '3',
#                 'gateway_id': '1',
#                 'amount': '1000',
#                 'currency': 'IR',
#                 'description':'FOR TEST',
#                 'authority_code': str(uuid4()),
#                 'idempotency_key': str(uuid4())}
#             )


    # test = TEST()
    # import time 
    # all_start = time.process_time()
    # for _ in range(1000):
    #     print( "*"*50)
    #     print(f"Index {_}")

    #     s_f_time = time.process_time()
    #     test.action()
    #     f_f_time = time.process_time()
    #     print(
    #         f'Index :{_} Time : {f_f_time-s_f_time}' 
    #     )
                
    #     all_finishd = time.process_time()
    # print("*"*10 , f'\n all end is' , {all_finishd - all_start })
    # test.action()

# if __name__ == '__main__':
#     main()