from celery import shared_task
from django.utils import timezone
from .models import Task, Notification
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def check_overdue_tasks():
    """Проверка просроченных задач (ежедневно, с уникальностью — нет дублей)."""
    overdue = Task.objects.filter(due_date__lt=timezone.now(), status__in=['pending', 'in_progress'])
    sent_count = 0
    for task in overdue:
        if task.assignee:
            creator_name = task.created_by.get_full_name() if task.created_by.get_full_name() else task.created_by.email
            message = f'Задача "{task.title}" просрочена! (создана {creator_name})'

            if not Notification.objects.filter(
                user=task.assignee, 
                message__icontains=task.title, 
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).exists():
                notification = Notification.objects.create(user=task.assignee, message=message)
                sent_count += 1
                print(f"{task.assignee.email}: {task.title} (ID: {notification.id})")
            else:
                print(f"{task.assignee.email}: {task.title}")

    print(f"Checked overdue: {len(overdue)} tasks, new notifications sent: {sent_count}")
