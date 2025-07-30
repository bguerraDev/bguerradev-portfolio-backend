# contact/views.py
from firebase_admin import firestore
from django.contrib.auth.hashers import check_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .firebase import db
import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"detail": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            query = db.collection("users").where(
                "username", "==", username).limit(1).stream()
            user_doc = next(query, None)

            if not user_doc:
                return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

            user_data = user_doc.to_dict()
            if not check_password(password, user_data.get("password")):
                return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

            return Response({"detail": "Login successful!"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Login error: {e}")
            return Response({"detail": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    def get(self, request):
        try:
            messages_ref = db.collection("contact_messages").order_by(
                "timestamp", direction=firestore.Query.DESCENDING)
            messages = [
                {
                    "id": doc.id,
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "message": data.get("message"),
                    "timestamp": data.get("timestamp"),
                }
                for doc in messages_ref.stream()
                for data in [doc.to_dict()]
            ]
            return Response(messages, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
