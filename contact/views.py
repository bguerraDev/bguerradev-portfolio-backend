# contact/views.py
from firebase_admin import firestore
from django.contrib.auth.hashers import check_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .firebase import db
from .models import CustomUser
import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"detail": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            users_ref = db.collection("users")
            query = users_ref.where(
                "username", "==", username).limit(1).stream()
            user_doc = next(query, None)

            if not user_doc:
                logger.warning(
                    f"Login attempt failed: User '{username}' not found.")
                return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

            user_data = user_doc.to_dict()
            stored_hash = user_data.get("password")
            if not stored_hash or not check_password(password, stored_hash):
                logger.warning(
                    f"Login attempt failed: Invalid password for user '{username}'.")
                return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

            # Generate tokens using a mock user or username
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken()
            refresh["username"] = username
            refresh.set_exp()  # Set expiration manually if needed

            logger.info(f"User '{username}' logged in successfully.")
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "detail": "Login successful!"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error during login for user '{username}': {str(e)}")
            return Response({"detail": "An error occurred during login."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactMessageView(APIView):
    def post(self, request):
        data = request.data
        try:
            db.collection("contact_messages").add({
                "name": data["name"],
                "email": data["email"],
                "message": data["message"],
                "timestamp": firestore.SERVER_TIMESTAMP,
            })
            return Response({"detail": "Message stored successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MessageListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            messages_ref = db.collection("contact_messages").order_by(
                "timestamp", direction=firestore.Query.DESCENDING)
            messages = []

            for doc in messages_ref.stream():
                data = doc.to_dict()
                messages.append({
                    "id": doc.id,
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "message": data.get("message"),
                    "timestamp": data.get("timestamp"),
                })

            return Response(messages, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
