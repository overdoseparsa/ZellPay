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


# send request aysing 
# loggin 
# validation databsae 
# save in database 



class AbstractRequesTransaction(ABC):
    """
        Abstract base class for payment Request gateways
    
    >>> class RequestTransaction(
        AbstractRequesTransaction
    ):
    ... def send_request(self,*args,**kwargs):
            # mylogic 
    
    ```
        we should use this class fr om abstract 
        imaggin you have to variy transaction provider such ass 
        zarinpall 
        saddat 
        mockfor testing 
        i use this layer class for be maiintanse and adtabtable with another 
        providef if we want to add any more i create in this status spreate 
        - we have class to show struct base from how transaction work 

        >>> send_request():
            # my logic 
            # in this section you can defind your transaction 


        in this abstract whe can implement the 
        some base effinent like 
        millwatre 
        your ratelimit 
        your requests ttype 

    
    
    """
    
    authorize = None
    transaction_handler = ... 

    def __init__(self,
                transaction_handler: RequestZarinpallHandeler,
                **config: Dict[str, Any]):
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
        logger.info(f"Initializing {self.__class__.__name__}")
        
        
        if not isinstance(transaction_handler, AbstractTransactionHandler):
            raise TypeError("transaction_handler must be an instance of TransactionMixin")
        
        self.transaction_handler = transaction_handler
        
        def ensure_not_empty(value: Any, error_message: str = "Value cannot be empty")->None|Any:
            """
            Values must not empty 
            """
            if not value:
                logger.error(error_message)
                raise ValueError(error_message)
        
        
        self.__authorization = config.get('authorize') or self.get_authorization()
        self.__amount = config.get('amount')
        self.__description = str(config.get('description', ''))




        ensure_not_empty(self.__authorization,"Authorization not set for payment gateway")

        ensure_not_empty(self.__amoun,f"Invalid amount: {self.__amount}")

        ensure_not_empty(self.__description,"Description not provided")

        
        
        self.__currency = config.get('currency', 'IRR')
        self.__metadata = config.get('metadata', {})
        self.__order_id = config.get('order_id')
        self.__gateway_id = config.get('gateway_id')
        
        
        self._data = self.build_config()
        
        logger.info(f"{self.__class__.__name__} initialized successfully")

    # you can validate yor data here 
    def validate_data(self , data):
        # TODO add some filter here 
        assert self.data
        return data


    def build_config(self, **meta) -> Dict[str, Any]:
        """Build configuration dictionary - can be overridden"""
        config = {
            'order_id':self.__order_id,
            'authorize': self.__authorization,
            'amount': self.__amount,
            'description': self.__description,
            'currency': self.__currency,
            'gateway_id':self.__gateway_id,
            **meta,
        }
        
        if self.__metadata:
            config['metadata'] = self.__metadata
        
        return config
    
    @property
    def data(self): # TODO create immutable from data 
        return self.validate_data(
            self._data
        )

    def set_context(self, context: Any = None)->None:
        """Set custom context data from business logic"""
        if context is not None:
            self._data['context'] = context
            logger.debug("Custom request data set")
    
    
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
        self._data = self.build_config()
        self._data['callback_url'] = self.callback_url
        
        logger.debug(f"Payment request prepared with callback: {self.callback_url}")
    
    
    def get_default_callback_url(self) -> str:
        """Get default callback URL - must be implemented by subclasses"""
        raise NotImplementedError("get_default_callback_url must be implemented")

