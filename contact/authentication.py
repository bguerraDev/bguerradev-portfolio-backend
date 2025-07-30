from rest_framework_simplejwt.authentication import JWTAuthentication
from .views import DummyUser

class DummyUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        # En lugar de buscar en la DB, usar DummyUser directamente
        username = validated_token.get("username")
        if not username:
            return None
        return DummyUser(username)