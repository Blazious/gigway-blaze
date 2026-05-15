from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from core.models import CustomUser
from core.utils import decode_jwt_token

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        payload = decode_jwt_token(token)
        
        if 'error' in payload:
            raise AuthenticationFailed(payload['error'])
            
        try:
            user = CustomUser.objects.get(id=payload['user_id'])
            if not user.is_active:
                raise AuthenticationFailed('User account is disabled')
            return (user, None)
        except CustomUser.DoesNotExist:
            raise AuthenticationFailed('User not found')