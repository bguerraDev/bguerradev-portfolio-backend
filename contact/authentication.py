from rest_framework_simplejwt.authentication import JWTAuthentication
from .dummy_user import DummyUser

class DummyUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        username = validated_token.get("user_id")
        if not username:
            return None
        return DummyUser(username)