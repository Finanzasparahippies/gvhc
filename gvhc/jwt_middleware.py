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
        from django.contrib.auth.models import AnonymousUser

        close_old_connections()
        
        token_str = None
        user = AnonymousUser()

        headers = dict(scope['headers'])
        if b'authorization' in headers:
            auth_header = headers[b'authorization'].decode('utf-8')
            if auth_header.startswith('Bearer '):
                token_str = auth_header.split(' ')[1]
        
        # 2. Si no se encuentra el token, buscamos en la query string
        if not token_str and 'query_string' in scope:
            query_params = parse_qs(scope['query_string'].decode())
            if 'token' in query_params:
                token_str = query_params['token'][0]

        # 3. Si se encuentra un token, intentamos obtener el usuario
        if token_str:
            db_user = await get_user_from_token(token_str)
            if db_user:
                user = db_user

        # 4. Establecemos el usuario en el scope
        scope['user'] = user
        
        # 5. Llamamos a la implementación del middleware base
        return await super().resolve_scope(scope)