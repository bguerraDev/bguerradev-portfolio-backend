from django.contrib.auth.models import PermissionsMixin
from .firebase import db
from django.contrib.auth.hashers import make_password

class CustomUserManager:
    def create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        user_data = {"username": username, "password": make_password(password), **extra_fields}
        db.collection("users").document().set(user_data)
        return {"username": username, "id": db.collection("users").document().id}  # Return a mock object or ID

    # Remove _create_django_user since we’re not using Django’s ORM

class CustomUser:
    username = None  # Remove field since it’s stored in Firestore
    is_active = None
    is_staff = None

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username or "Unknown"

class Message:
    name = None
    email = None
    message = None
    timestamp = None

    def __str__(self):
        return f"{self.name} - {self.email}"