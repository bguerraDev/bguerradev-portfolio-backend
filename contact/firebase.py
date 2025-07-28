import firebase_admin
from firebase_admin import credentials, firestore
from django.conf import settings

cred = credentials.Certificate(settings.FIREBASE_CREDENTIAL)
default_app = firebase_admin.initialize_app(cred)
db = firestore.client()