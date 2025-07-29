from contact.models import CustomUser
from contact.firebase import db


def sync_firestore_users():
    users_ref = db.collection("users").stream()
    for user_doc in users_ref:
        user_data = user_doc.to_dict()
        username = user_data.get("username")
        try:
            CustomUser.objects.get_or_create(username=username)
            print(f"Synced user: {username}")
        except Exception as e:
            print(f"Error syncing user {username}: {e}")


sync_firestore_users()
