# contact/views.py
from firebase_admin import firestore
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import status, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .firebase import db
import datetime
import jwt


class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"detail": "username and password required."}, status=status.HTTP_400_BAD_REQUEST)

        users_ref = db.collection("users")
        query = users_ref.where("username", "==", username).limit(1).get()

        if not query:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        user_doc = query[0]
        user_data = user_doc.to_dict()
        stored_hash = user_data.get("password")

        if not check_password(password, stored_hash):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        # Generar JWT manual
        payload = {
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            "iat": datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        return Response({
            "access": token,
            "detail": "Login successful!"
        }, status=status.HTTP_200_OK)


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
