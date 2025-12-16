"""Zarin Pall"""
import requests # TODO chance To Httpx for asyinc 
import json
from typing import (
    Dict,
    Any,
    Optional,
)

from logging import getLogger
from functools import wraps
import time

logger = getLogger(__name__)

# Default timeout for API requests (in seconds)
DEFAULT_TIMEOUT = 30
# Maximum retry attempts
MAX_RETRIES = 3
# Retry delay (in seconds)
RETRY_DELAY = 1


def retry_on_failure(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Decorator to retry function on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, ValueError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed: {e}")
            
            if last_exception:
                raise last_exception
        return wrapper
    return decorator




def send_request_zarinpall(
    ZP_API_REQUEST: Optional[str] = None,
    MERCHANT: Optional[str] = None,
    callbackURL: Optional[str] = None,
    amount: Optional[str] = None,
    description: Optional[str] = None,
    email: Optional[str] = None,
    mobile: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs
) -> Dict[str, Any]:
    
    """
    Send payment request to Zarinpal API.
    
    Args:
        ZP_API_REQUEST: Zarinpal API request URL
        MERCHANT: Merchant ID
        callbackURL: Callback URL for payment confirmation
        amount: Payment amount (string format)
        description: Payment description
        email: User email (optional)
        mobile: User mobile number (optional)
        timeout: Request timeout in seconds
        **kwargs: Additional parameters
    
    Returns:
        Dict[str, Any]: API response containing:
            - data: Response data with authority and payment link
            - errors: Error information (if any)
    
    Raises:
        ValueError: If required parameters are missing
        requests.RequestException: If API request fails
    """
    
    try:
        # Validate required parameters
        if not ZP_API_REQUEST:
            raise ValueError("ZP_API_REQUEST URL is required")
        
        if not MERCHANT:
            MERCHANT = kwargs.get('merchant_id') or kwargs.get('merchant')
            if not MERCHANT:
                raise ValueError("MERCHANT ID is required")
        
        if not callbackURL:
            callbackURL = kwargs.get('callback_url')
            if not callbackURL:
                raise ValueError("callbackURL is required")
        
        if not amount:
            amount = kwargs.get('amount')
            if not amount:
                raise ValueError("amount is required")
        
        if not description:
            description = kwargs.get('description')
            if not description:
                raise ValueError("description is required")
        
        # Prepare request data
        metadata = kwargs.get('metadata', {})
        if email or mobile:
            metadata.update({
                'mobile': mobile,
                'email': email
            })
        
        req_data = {
            "merchant_id": str(MERCHANT),
            "amount": str(amount),
            "callback_url": str(callbackURL),
            "description": str(description),
            "metadata": metadata if metadata else {}
        }
        
        # Prepare request headers
        req_headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        logger.info(f"Sending payment request to Zarinpal: amount={amount}, merchant={MERCHANT}")
        logger.debug(f"Request data: {req_data}")
        
        # Send POST request
        response = requests.post(
            url=ZP_API_REQUEST,
            data=json.dumps(req_data),
            headers=req_headers,
            timeout=timeout
        )
        
        # Raise exception for bad status codes
        response.raise_for_status()
        
        # Parse response
        response_data = response.json()
        
        # Check for errors in response
        if 'errors' in response_data and len(response_data['errors']) > 0:
            error_info = response_data['errors'][0]  # Zarinpal returns array of errors
            error_code = error_info.get('code', 'unknown')
            error_message = error_info.get('message', 'Unknown error')
            
            logger.error(f"Zarinpal API error: code={error_code}, message={error_message}")
            
            return {
                "status": "error",
                "message": error_message,
                "error_code": error_code,
                "errors": response_data['errors']
            }
        
        # Success response
        if 'data' in response_data:
            authority = response_data['data'].get('authority')
            payment_link = response_data['data'].get('link')
            
            logger.info(f"Payment request successful: authority={authority}")
            
            return {
                "status": "success",
                "data": response_data['data'],
                "errors": []
            }
        
        # Unexpected response format
        logger.warning(f"Unexpected response format: {response_data}")
        return {
            "status": "error",
            "message": "Unexpected response format",
            "error_code": "UNEXPECTED_FORMAT",
            "response": response_data
        }
        
    except requests.Timeout:
        logger.error(f"Request timeout after {timeout}s")
        return {
            "status": "error",
            "message": "Request timeout",
            "error_code": "TIMEOUT"
        }
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "error_code": "REQUEST_ERROR"
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "error_code": "UNEXPECTED_ERROR"
        }
    

    