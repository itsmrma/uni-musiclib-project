from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend which allows users to authenticate using either their
    username or email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username')
            
        try:
            # Check if the user exists with the given username or email
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
        except User.MultipleObjectsReturned:
            # Fallback if multiple users have the same email
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('id').first()
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
                
        return None
