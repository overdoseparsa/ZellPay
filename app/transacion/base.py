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

# middleware 
# authintication 
# ratelimmit 
# Type validation 

class AbstractRequesTransaction(ABC):
    """Abstract base class for payment Request gateways"""

    def __init__(self,
                transaction_handler: RequestZarinpallHandeler=None, 
                context: Any = None,
                **config: Dict[str, Any]
                ):
        """
        Initialize payment gateway.
        
        Args:
            transaction_handler: TransactionMixin instance for database operations
            **config: Gateway configuration:
                - authorize: Authorization /merchant ID 
                - amount: Payment amount (string)
                - description: Payment description
                - currency: Currency code (optional)
                - metadata: Additional metadata (optional)
                - user_id: User UUID (required)
                - order_id: Order identifier (required)
                - gateway_id: Payment gateway ID (required)
                - idempotency_key: Idempotency key (optional)
        """


        self.transaction_handler = self._get_db_handler() or transaction_handler
        
        self.data = self.build_config()
        
        logger.info(f"{self.__class__.__name__} initialized successfully")

    @staticmethod
    def ensure_not_empty(value: Any, error_message: str = "Value cannot be empty")->None|Any:
        """
                Values must not empty 
        """
        if not value:
            logger.error(error_message)
        raise ValueError(error_message)
        
    authorize = ...
    db_handler = ... 

    def _get_db_handler(self)->Any:
        
        if not isinstance(self.db_handler, AbstractTransactionHandler):
            raise TypeError("transaction_handler must be an instance of TransactionMixin")
        
        return self.db_handler
    




    def build_config(self,config:Dict[str:Any],context=None ,**meta) -> Dict[str, Any]: 

        """
        Build configuration dictionary - can be overridden
        
        ```here You can change Your key Logic to save in real data transaction```
        """

        authorize = config.get('authorize') or self.get_authorization()

        description = config.get('description')

        amount = config.get('amount')

        config = {
            'order_id':config.get('order_id'),
            'authorize': authorize,
            'amount': amount,
            'description': description,
            'currency': config.get('currency', 'IRR'),
            'gateway_id':config.get('gateway_id'),
            **meta,
        }
        
        if meta := config.get('metadata'):
            config['metadata'] = meta
        
        # Base Validation 
        AbstractRequesTransaction.ensure_not_empty( # TODO add validation class mixin
            authorize,
            "Authorization not set for payment gateway"
            )

        AbstractRequesTransaction.ensure_not_empty(
            amount,
            f"Invalid amount: {amount}")

        AbstractRequesTransaction.ensure_not_empty(
            description
            ,"Description not provided")
        
        if context and (not 'context' in config):
            config['context']
        


        return self.validate_data(config)
    
    
    def validate_data(self,data:Any)->Any:
        """
        In Space You can specifyed Some Validation from your data Transactions 

        """
        return self.data




    
    
    @staticmethod
    def get_static_authorization() -> Optional[str]:
        """Get static authorization - can be overridden"""
        return None
    
    @classmethod
    def get_authorization(cls) -> Optional[str]:
        """Get authorization from class or static method"""
        if hasattr(cls, 'authorize') and cls.authorize:
            return cls.authorize
        static_auth = cls.get_static_authorization()
        return static_auth
    

   
    @abstractmethod
    def send_request(self, callback_url: Optional[str] = None, *args, **kwargs) -> Dict[str, Any]:
        """
        Send payment request to gateway.
        
        Note: In concrete implementations, call super().send_request() first
        before adding gateway-specific logic.
        
        Args:
            callback_url: Callback URL for payment confirmation
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments:
                - request: Custom request data
        
        Returns:
            Dict[str, Any]: Payment request response containing:
                - status: Request status
                - data: Response data with authority_code and payment URL
                - uuid: Transaction UUID
        """
        logger.info("Sending payment request")
        
        # Set custom request data if provided
        if 'request' in kwargs:
            self.set_context({"request":kwargs.get('request')})
        
        # Set callback URL
        if callback_url:
            self.callback_url = callback_url
        else:
            self.callback_url = self.get_default_callback_url()
        
        if not self.callback_url:
            logger.error("Callback URL not set")
            raise ValueError("Callback URL must be set")
        
        # Update configuration with callback URL
        
        self.data['callback_url'] = self.callback_url
        
        logger.debug(f"Payment request prepared with callback: {self.callback_url}")
    
    
    def get_default_callback_url(self) -> str:
        """Get default callback URL - must be implemented by subclasses"""
        raise NotImplementedError("get_default_callback_url must be implemented")


from mock_ import send_request_zarinpall_mock

class ZarinPallTransactionRequest(
    AbstractRequesTransaction
):
 
    def __init__(self, transaction_handler, **config):
        super().__init__(transaction_handler, **config)

    def build_config(self, **meta):
        config = super().build_config(**meta)
        
        if 'authorize' in config:
            config['authority_code'] = config.pop('authorize')
        
        return config
    
    def send_request(self, callback_url = None, *args, **kwargs):
        super().send_request(callback_url, *args, **kwargs)

        
        validate_data = self.data 

        response_zarinpall = send_request_zarinpall_mock(
            validate_data
        ) 

        # 2 : use the transaction_handler
        status , transaction_uuid , token_url = self.transaction_handler.save_transaction(
            data = validate_data , 
            evant = response_zarinpall
        )
        if status :
            return RequestPayloadError(
                str(transaction_uuid)
            )
        

        self._response = (transaction_uuid , token_url)
        
    
    @property
    def response(self):
        assert hasattr(self, '_response') , 'Must Send Request'
        transaction_uuid , token_url = self._response
        return {  
            "uuid": transaction_uuid , 
            "token": token_url,
        }
        

def main():
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
       
        def action(self):
            from uuid import uuid4
            self.database_reposiroy = RequestZarinpallHandeler(
                    self.db_manger , self.transaction_redis
                )
            self.Zarinpall_req = ZarinPallTransactionRequest(
                self.database_reposiroy  , ## must get from requests   

                authorize = str(uuid4()) , 
                description = 'hello' , 
                amount = '1000' ,
                order_id=23123,
                gateway_id=1 ,
                # authority_code = str(uuid4()) # must get from requests   

            )

            self.Zarinpall_req.send_request(
                callback_url='https://mysite.com/verify/'
            )

            

    test = TEST()
    test.action()
if __name__ == '__main__':
    from test11 import * 
    main()