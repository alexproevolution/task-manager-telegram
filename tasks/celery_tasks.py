from celery import shared_task
from django.conf import settings
from django.utils import timezone
import requests

from .models import TelegramProfile, Task, Notification


TG_BOT_TOKEN = getattr(settings, 'TG_BOT_TOKEN', None)
TG_API_SEND = (
    f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    if TG_BOT_TOKEN else None
)


@shared_task
def send_telegram_message(chat_id, text):
    """Отправляет сообщение пользователю через Telegram Bot API."""
    if not TG_API_SEND:
        print("[TG ERROR] TG_BOT_TOKEN не настроен в settings.py")
        return {'ok': False, 'error': 'TG_BOT_TOKEN not configured'}

    payload = {
        'chat_id': str(chat_id),
        'text': text,
        'parse_mode': 'HTML',
    }

    try:
        response = requests.post(TG_API_SEND, json=payload, timeout=5)
        print(f"[TG SEND] → {chat_id}: {response.status_code}")
        return {
            'ok': response.status_code == 200,
            'status': response.status_code,
            'text': response.text,
        }
    except Exception as e:
        print(f"[TG ERROR] {e}")
        return {'ok': False, 'error': str(e)}


@shared_task
def send_notification(user_id, message):
    """Создаёт уведомление и отправляет его в Telegram при наличии chat_id."""
    try:
        Notification.objects.create(user_id=user_id, message=message)
        print(f"[Celery] Notification created for user {user_id}: {message}")

        profile = TelegramProfile.objects.filter(user_id=user_id).first()
        if profile and profile.chat_id:
            send_telegram_message.delay(profile.chat_id, message)
        else:
            print(f"[Celery] Telegram chat_id отсутствует у пользователя {user_id}")
    except Exception as e:
        print(f"[Celery ERROR] send_notification: {e}")


@shared_task
def notify_assignment(task_id):
    """Уведомляет исполнителя о новой задаче."""
    try:
        task = Task.objects.select_related('assignee', 'created_by').get(pk=task_id)
    except Task.DoesNotExist:
        print(f"[Celery] Task {task_id} не найден")
        return

    if not task.assignee:
        print(f"[Celery] Task {task_id} без исполнителя — уведомление пропущено")
        return

    creator_name = task.created_by.get_full_name() or task.created_by.email
    due_str = (
        task.due_date.strftime("%d.%m.%Y %H:%M")
        if task.due_date else "Без срока"
    )
    text = (
        f'📝 Новая задача от <b>{creator_name}</b>:\n'
        f'"<b>{task.title}</b>"\nСрок: {due_str}'
    )

    recent = Notification.objects.filter(
        user=task.assignee,
        message__icontains=task.title,
        created_at__gte=timezone.now() - timezone.timedelta(hours=1),
    )
    if not recent.exists():
        Notification.objects.create(user=task.assignee, message=text)

    profile = getattr(task.assignee, 'telegram_profile', None)
    if profile and profile.chat_id:
        send_telegram_message.delay(profile.chat_id, text)
        print(f"[Celery] Telegram уведомление отправлено {task.assignee.email}")
    else:
        print(f"[TG SKIP] У пользователя {task.assignee.email} нет chat_id")


@shared_task
def check_and_notify_overdue():
    """Проверяет просроченные задачи и уведомляет исполнителей."""
    now = timezone.now()
    overdue_tasks = Task.objects.filter(
        due_date__lt=now
    ).exclude(status='completed')

    for task in overdue_tasks:
        if not task.assignee:
            continue

        text = (
            f"⏰ Задача просрочена:\n"
            f"<b>{task.title}</b>\n"
            f"Срок: {task.due_date.strftime('%d.%m.%Y %H:%M') if task.due_date else '—'}"
        )

        Notification.objects.create(user=task.assignee, message=text)

        profile = getattr(task.assignee, 'telegram_profile', None)
        if profile and profile.chat_id:
            send_telegram_message.delay(profile.chat_id, text)
        else:
            print(f"[TG SKIP] {task.assignee.email} без Telegram chat_id")
