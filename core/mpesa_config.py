import os

# M-Pesa Configuration
MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'sandbox')  # sandbox or production
# Default False: use real M-Pesa when credentials are set. Set to 'true' only to mock (no real STK).
MPESA_TEST_MODE = os.getenv('MPESA_TEST_MODE', 'false').lower() == 'true'

# Sandbox credentials - use real ones in production
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY', 'YOUR_SANDBOX_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET', 'YOUR_SANDBOX_CONSUMER_SECRET')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE', '174379')  # Sandbox test paybill
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY', 'YOUR_SANDBOX_PASSKEY')

# Base URLs
if MPESA_ENVIRONMENT == 'sandbox':
    MPESA_BASE_URL = 'https://sandbox.safaricom.co.ke'
else:
    MPESA_BASE_URL = 'https://api.safaricom.co.ke'

# API Endpoints
MPESA_AUTH_URL = '/oauth/v1/generate?grant_type=client_credentials'
MPESA_STK_PUSH_URL = '/mpesa/stkpush/v1/processrequest'

# Callback URL must be full HTTPS URL reachable by Safaricom (e.g. ngrok). No appending.
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL') or 'http://yourdomain.com/api/mpesa/callback/deposit'