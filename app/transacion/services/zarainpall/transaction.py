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

        # 1 : send the http_request 
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
            "UUID":transaction_uuid , 
            "TOKEN":token_url
        }
        