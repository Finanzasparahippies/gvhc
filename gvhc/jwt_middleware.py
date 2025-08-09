# gvhc/jwt_middleware.py
from channels.auth import AuthMiddleware
from django.db import close_old_connections
from urllib.parse import parse_qs
from channels.db import database_sync_to_async

@database_sync_to_async
def get_user_from_token(token):

    from rest_framework_simplejwt.tokens import AccessToken
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    try:
        access_token_obj = AccessToken(token)
        user_id = access_token_obj['user_id']
        return User.objects.get(id=user_id)
    except Exception:
        return None

class JWTAuthMiddleware(AuthMiddleware):
    async def resolve_scope(self, scope):
        # close_old_connections()
        headers = dict(scope['headers'])
        token_str = None

        # Intenta obtener el token del encabezado Authorization
        if b'authorization' in headers:
            auth_header = headers[b'authorization'].decode('utf-8')
            if auth_header.startswith('Bearer '):
                token_str = auth_header.split(' ')[1]
        
        # Si no está en el encabezado, busca en la URL (como alternativa)
        if not token_str and 'query_string' in scope:
            query_params = parse_qs(scope['query_string'].decode())
            if 'token' in query_params:
                token_str = query_params['token'][0]

        scope['user'] = None
        if token_str:
            scope['user'] = await get_user_from_token(token_str)
        
        return await super().resolve_scope(scope)