# contact/views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from firebase_admin import firestore
from .firebase import db

# Configure logger
logger = logging.getLogger(__name__)


class DummyUser:
    def __init__(self, username):
        self.username = username
        self.pk = username  # Used as unique identifier for JWT
        self.is_active = True
        self.is_authenticated = True

    def __str__(self):
        return self.username

    @property
    def is_anonymous(self):
        return False


class FirestoreLoginView(APIView):
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            # Validate input
            if not username or not password:
                logger.warning(
                    f"Missing credentials in login attempt: username={username}")
                return Response(
                    {'detail': 'Username and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Initialize Firestore client
            try:
                db = firestore.client()
                users_ref = db.collection('users')
                user_doc = users_ref.document(username).get()
            except Exception as e:
                logger.error(f"Firestore connection error: {str(e)}")
                return Response(
                    {'detail': 'Database connection error'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Check if user exists and verify password
            if user_doc.exists:
                stored_hash = user_doc.to_dict().get('password')
                if not stored_hash:
                    logger.warning(
                        f"No password hash found for user: {username}")
                    return Response(
                        {'detail': 'Invalid user data'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                if check_password(password, stored_hash):
                    try:
                        # Create JWT token
                        refresh = RefreshToken.for_user(DummyUser(username))
                        logger.info(f"Successful login for user: {username}")
                        return Response({
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        }, content_type="application/json")
                    except Exception as e:
                        logger.error(
                            f"Token generation error for user {username}: {str(e)}")
                        return Response(
                            {'detail': 'Error generating authentication token'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                logger.warning(
                    f"Invalid password attempt for user: {username}")
                return Response(
                    {'detail': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            logger.warning(f"User not found: {username}")
            return Response(
                {'detail': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        except Exception as e:
            logger.error(f"Unexpected error in login process: {str(e)}")
            return Response(
                {'detail': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            messages_ref = db.collection("contact_messages").order_by(
                "timestamp", direction=firestore.Query.DESCENDING
            )

            # Fetch and format messages
            messages = []
            for doc in messages_ref.stream():
                data = doc.to_dict()
                # Convert Firestore timestamp to ISO format if it exists
                timestamp = (
                    data.get("timestamp").isoformat() if data.get(
                        "timestamp") else None
                )
                messages.append(
                    {
                        "id": doc.id,
                        "name": data.get("name"),
                        "email": data.get("email"),
                        "message": data.get("message"),
                        "timestamp": timestamp,
                    }
                )

            # ✅ Seguridad: manejar correctamente si user no tiene username
            username = getattr(request.user, "username", "anonymous")
            logger.info(f"User {username} fetched {len(messages)} messages")

            return Response(messages, status=status.HTTP_200_OK)

        except Exception as e:
            username = getattr(request.user, "username", "anonymous")
            logger.error(
                f"Error fetching messages for user {username}: {str(e)}")
            status_code = (
                status.HTTP_500_INTERNAL_SERVER_ERROR
                if "firestore" in str(e).lower()
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(
                {"detail": "Failed to fetch messages"},
                status=status_code
            )
