"""
Social Authentication Handler
Handles OAuth authentication with Google and Facebook
"""
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from core.utils import generate_jwt_token, format_phone_number
import logging

logger = logging.getLogger(__name__)
User = get_user_model()  # This replaces CustomUser

def get_google_user_info(access_token):
    """Get user info from Google using access token"""
    try:
        # Try v2 first, fallback to v3
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to get Google user info: {str(e)}")
        raise Exception(f"Failed to verify Google token: {str(e)}")

def exchange_google_code_for_token(code, redirect_uri):
    """Exchange a Google OAuth authorization code for tokens."""
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')

    if not client_id or not client_secret:
        raise Exception("Google OAuth server credentials are not configured")

    response = requests.post(
        'https://oauth2.googleapis.com/token',
        data={
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        },
        timeout=10
    )
    response.raise_for_status()
    return response.json()

def get_facebook_user_info(access_token):
    """Get user info from Facebook using access token"""
    try:
        response = requests.get(
            'https://graph.facebook.com/me',
            params={
                'fields': 'id,name,email,picture',
                'access_token': access_token
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get Facebook user info: {str(e)}")
        raise Exception(f"Failed to verify Facebook token: {str(e)}")

def create_or_get_social_user(provider, social_id, email, name, picture_url=None, phone_number=None):
    """
    Create or get user from social authentication
    Returns: (user, created)
    """
    created = False
    try:
        user = User.objects.get(email=email)
        return user, False
    except User.DoesNotExist:
        # Create new user
        name_parts = name.split(' ', 1) if name else ['User', '']
        first_name = name_parts[0] if name_parts else 'User'
        
        if not phone_number:
            phone_number = "254700000000"  # placeholder
        
        phone_number = format_phone_number(phone_number)
        
        try:
            user = User.objects.create_user(
                email=email,
                password=User.objects.make_random_password(length=32),
                phone_number=phone_number,
                user_type='freelancer',
            )
        except Exception as e:
            logger.error(f"Failed to create {provider} user {email}: {str(e)}")
            raise ValidationError(f"Could not create account from {provider}: {str(e)}")
        
        # Optional extra fields
        if name:
            user.company_name = name
        if picture_url:
            pass  # Optionally handle profile picture
        
        user.save()
        created = True
        logger.info(f"Created new user from {provider}: {email}")
    
    return user, created

def authenticate_social_user(provider, access_token=None, phone_number=None, code=None, redirect_uri=None):
    """
    Authenticate user via social provider
    Returns: dict with user data and JWT token
    """
    if provider == 'google':
        if code:
            token_data = exchange_google_code_for_token(code, redirect_uri)
            access_token = token_data.get('access_token')
        if not access_token:
            raise ValueError("Google access token was not provided")

        user_info = get_google_user_info(access_token)
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture_url = user_info.get('picture')
        social_id = user_info.get('id')
    elif provider == 'facebook':
        user_info = get_facebook_user_info(access_token)
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture_url = user_info.get('picture', {}).get('data', {}).get('url') if user_info.get('picture') else None
        social_id = user_info.get('id')
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    if not email:
        raise ValueError(f"Email not provided by {provider}")
    
    user, created = create_or_get_social_user(
        provider=provider,
        social_id=social_id,
        email=email,
        name=name,
        picture_url=picture_url,
        phone_number=phone_number
    )
    
    token = generate_jwt_token(user)
    
    return {
        'user': {
            'id': str(user.id),
            'email': user.email,
            'phone_number': user.phone_number,
            'user_type': user.user_type,
            'company_name': user.company_name,
        },
        'token': token,
        'created': created
    }
