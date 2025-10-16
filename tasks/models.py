import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

User = get_user_model()

class TaskList(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название списка")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_lists')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Список задач"
        verbose_name_plural = "Списки задач"

    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершено'),
    ]

    list = models.ForeignKey(TaskList, on_delete=models.CASCADE, related_name='tasks', verbose_name="Список")
    title = models.CharField(max_length=200, verbose_name="Название задачи")
    description = models.TextField(blank=True, verbose_name="Описание")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', verbose_name="Исполнитель")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Срок выполнения")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"

    def is_overdue(self):
        if self.status == 'completed' or not self.due_date:
            return False
        return self.due_date < timezone.now()

# ← НОВОЕ: Модель для уведомлений (in-app)
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email}: {self.message[:50]}"


class TelegramProfile(models.Model):
    """
    Связка между пользователем и Telegram chat_id.
    - link_token: uuid, используется для безопасной привязки (показать пользователю в профиле).
    - chat_id: строка (может быть большой), заполняется ботом при /start <token>.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_profile')
    chat_id = models.CharField(max_length=64, null=True, blank=True, unique=True)
    link_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    linked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} — chat:{self.chat_id}"

    def link(self, chat_id_str):
        self.chat_id = str(chat_id_str)
        self.linked_at = timezone.now()
        self.save()
    
    def regenerate_token(self):
        self.link_token = uuid.uuid4()
        self.save(update_fields=['link_token'])
        return self.link_token
