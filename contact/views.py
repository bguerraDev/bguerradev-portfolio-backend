# contact/views.py
from firebase_admin import firestore
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .firebase import db
from rest_framework_simplejwt.tokens import RefreshToken


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

        # Generar token JWT manualmente
        refresh = RefreshToken.for_user(None)
        refresh["username"] = username

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "detail": "Login successful!"
        }, status=status.HTTP_200_OK)


class ContactMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        try:
            db.collection("contact_messages").add({
                "name": data["name"],
                "username": data["username"],
                "message": data["message"],
                "timestamp": firestore.SERVER_TIMESTAMP,
            })
            return Response({"detail": "Message stored successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
