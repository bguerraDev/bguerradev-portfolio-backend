from django.core.management.base import BaseCommand
from contact.models import CustomUser
from contact.firebase import db


class Command(BaseCommand):
    help = "Sincroniza los usuarios desde Firestore al modelo CustomUser"

    def handle(self, *args, **kwargs):
        self.stdout.write("Syncing users from Firestore...")
        users_ref = db.collection("users").stream()

        for user_doc in users_ref:
            user_data = user_doc.to_dict()
            username = user_data.get("username")
            if not username:
                continue

            _, created = CustomUser.objects.get_or_create(username=username)
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"User '{username}' synced."))
            else:
                self.stdout.write(f"User '{username}' already exists.")

        self.stdout.write(self.style.SUCCESS("Sync complete."))