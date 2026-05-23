import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Always load env from project root and override blank system vars.
load_dotenv(BASE_DIR / '.env', override=True)

def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default=None):
    value = os.getenv(name, "")
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here')

DEBUG = env_bool('DEBUG', True)

ALLOWED_HOSTS = env_list(
    'ALLOWED_HOSTS',
    ['localhost', '127.0.0.1', '.railway.app', '.up.railway.app']
)

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
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'escrow_platform.urls'

WSGI_APPLICATION = 'escrow_platform.wsgi.application'

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
] + env_list('CORS_ALLOWED_ORIGINS')

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "https://gigway-two.vercel.app",
]
CSRF_TRUSTED_ORIGINS += env_list('CSRF_TRUSTED_ORIGINS')

database_url = os.getenv('DATABASE_URL', '')
if database_url:
    parsed_database_url = urlparse(database_url)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed_database_url.path.lstrip('/'),
            'USER': parsed_database_url.username,
            'PASSWORD': parsed_database_url.password,
            'HOST': parsed_database_url.hostname,
            'PORT': parsed_database_url.port or 5432,
            'OPTIONS': {'sslmode': 'require'},
            'CONN_MAX_AGE': 600,
        }
    }
elif os.getenv('PGHOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('PGDATABASE'),
            'USER': os.getenv('PGUSER'),
            'PASSWORD': os.getenv('PGPASSWORD'),
            'HOST': os.getenv('PGHOST'),
            'PORT': os.getenv('PGPORT', '5432'),
            'OPTIONS': {'sslmode': 'require'},
            'CONN_MAX_AGE': 600,
        }
    }
else:
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

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', BASE_DIR / 'media'))

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

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
