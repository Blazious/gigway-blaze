import os
import base64
import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from rest_framework.exceptions import APIException

def get_mpesa_access_token():
    """
    Get M-Pesa access token using consumer key and secret
    Returns: str - Access token valid for 1 hour
    Raises: APIException if authentication fails
    """
    consumer_key = os.getenv('MPESA_CONSUMER_KEY')
    consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
    
    if not all([consumer_key, consumer_secret]):
        raise APIException('M-Pesa credentials not configured')

    try:
        # Use sandbox URL for testing
        if os.getenv('MPESA_ENVIRONMENT') == 'sandbox':
            auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        else:
            auth_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        
        response = requests.get(
            auth_url,
            auth=HTTPBasicAuth(consumer_key, consumer_secret)
        )
        
        response.raise_for_status()
        return response.json()['access_token']
    
    except requests.exceptions.RequestException as e:
        raise APIException(f'M-Pesa authentication failed: {str(e)}')