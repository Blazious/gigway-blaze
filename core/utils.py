import jwt
from datetime import datetime, timedelta
from django.conf import settings

JWT_SECRET = 'your-secret-key'  # Should be from settings in production
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24

def generate_jwt_token(user):
    payload = {
        'user_id': str(user.id),
        'user_type': user.user_type,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}

def format_phone_number(phone):
    """Convert phone to 2547... format (Kenya)"""
    phone = str(phone).strip().replace('+', '').replace(' ', '')
    if phone.startswith('0'):
        return '254' + phone[1:]
    elif phone.startswith('254'):
        return phone
    else:
        return '254' + phone  # assumes Kenyan number, prefix omitted