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
   
    @abstractmethod
    def save_transaction(self, data: Dict[str, Any]) -> Tuple[int, UUID]:
        """
        Save transaction history to database.
        
        Args:
            data: Transaction data dictionary containing:
                - order_id: Order identifier
                - user_id: User UUID
                - gateway_id: Payment gateway ID
                - amount: Transaction amount
                - currency: Currency code
                - description: Transaction description
                - authority_code: Payment authority code
                - ref_id: Reference ID (optional initially)
                - meta: Additional metadata (optional)
                - idempotency_key: Idempotency key for duplicate prevention
        
        Returns:
            Tuple[int, UUID]: Status code (0 for success) and transaction UUID
        """
    
    
    
    def validate_transaction_payload(self, data: Dict[str, Any]) -> bool:
        """
        Validate transaction payload data.
        
        Args:
            data: Transaction data dictionary
        
        Returns:
            bool: True if valid, False otherwise
        """
        raise NotImplementedError("validate_transaction_payload must be implemented")
    
    
    def save_in_cache(self ,
                transaction_data:Dict[str,Any] ,
                transaction_uuid : UUID | str

                )->None:
        """
        In This Case we use cache add Transaction
        """

