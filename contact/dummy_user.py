# contact/dummy_user.py

class DummyUser:
    def __init__(self, username):
        self.username = username
        self.pk = username
        self.id = username  # Necesario para JWT
        self.is_active = True
        self.is_authenticated = True

    def __str__(self):
        return self.username

    @property
    def is_anonymous(self):
        return False
