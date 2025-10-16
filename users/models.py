from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

from .managers import UserManager


class MyUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Отчество")
    email = models.EmailField(unique=True, verbose_name="Email")
    is_staff = models.BooleanField(default=False, verbose_name="Статус персонала")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Дата регистрации")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}"
        if self.middle_name:
            full_name += f" {self.middle_name}"
        return f"{full_name} ({self.email})"

    def soft_delete(self):
        if self.is_active:
            self.is_active = False
            self.deleted_at = timezone.now()
            self.save(update_fields=['is_active', 'deleted_at'])

    def delete(self, using=None, keep_parents=False):
        self.soft_delete()

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}"
        if self.middle_name:
            full_name += f" {self.middle_name}"
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def has_permission(self, resource_name, action_name):
        if self.is_superuser:
            return True
        if not self.is_active or self.deleted_at:
            return False
        if not self.is_authenticated:
            return False

        for role in self.roles.all():
            if role.has_permission(resource_name, action_name):
                return True
        return False


@receiver(post_save, sender=MyUser)
def create_telegram_profile(sender, instance, created, **kwargs):
    """Создаёт TelegramProfile при регистрации нового пользователя."""
    if created:
        try:
            from tasks.models import TelegramProfile
            TelegramProfile.objects.get_or_create(user=instance)
            print(f"[SIGNAL] Создан TelegramProfile для {instance.email}")
        except Exception as e:
            print(f"[SIGNAL ERROR] Не удалось создать TelegramProfile: {e}")
