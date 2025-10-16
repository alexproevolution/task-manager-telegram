from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import MyUser


class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password) and user.is_active and not user.deleted_at:
                user.backend = 'users.backends.EmailBackend'
                return user
        except UserModel.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return MyUser .objects.get(pk=user_id, is_active=True, deleted_at__isnull=True)
        except MyUser.DoesNotExist:
            return None
