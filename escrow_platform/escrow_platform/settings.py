from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Always load env from project root and override blank system vars.
load_dotenv(BASE_DIR / '.env', override=True)

SECRET_KEY = 'django-insecure-your-secret-key-here'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'escrow_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server (primary)
    "http://localhost:5174",  # Vite fallback port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://gigway-two.vercel.app",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://gigway-two.vercel.app",
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.CustomUser'

# Verifies GitHub, LinkedIn, portfolio, and website proof links with a live request.
# Keep enabled in production so dummy URLs cannot receive competency evidence credit.
VERIFY_EXTERNAL_LINKS = os.getenv('VERIFY_EXTERNAL_LINKS', 'True') == 'True'

# M-Pesa Configuration
MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY', 'YOUR_SANDBOX_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET', 'YOUR_SANDBOX_CONSUMER_SECRET')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE', '174379')
MPESA_B2C_SHORTCODE = os.getenv('MPESA_B2C_SHORTCODE', '600000')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY', 'YOUR_SANDBOX_PASSKEY')
# Base URL for callbacks (e.g. https://your-ngrok.ngrok-free.app)
# Extract base URL from full callback URL if MPESA_CALLBACK_BASE_URL is not set
callback_url_full = os.getenv('MPESA_CALLBACK_URL', '')
if callback_url_full and '/api/' in callback_url_full:
    MPESA_CALLBACK_BASE_URL = callback_url_full.split('/api/')[0]
else:
    MPESA_CALLBACK_BASE_URL = os.getenv('MPESA_CALLBACK_BASE_URL', 'http://localhost:8000')

MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL', f'{MPESA_CALLBACK_BASE_URL}/api/mpesa/callback/deposit')

# eConfirm Escrow API
ECONFIRM_V1_BASE_URL = os.getenv('ECONFIRM_V1_BASE_URL', 'https://econfirm.co.ke/api/v1')
ECONFIRM_API_KEY = os.getenv('ECONFIRM_API_KEY', '')

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@escrowgig.com')

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
