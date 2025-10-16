from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import TaskList, Task, Notification, TelegramProfile
from .forms import TaskForm, TaskListForm
from .serializers import TaskSerializer, TelegramLinkSerializer
from .celery_tasks import notify_assignment


def broadcast_task_update(task):
    """Рассылает обновления задачи через WebSocket."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'tasks_group',
                {
                    'type': 'task_update',
                    'task_id': task.id,
                    'title': task.title,
                    'status': task.status,
                    'assignee': task.assignee.email if task.assignee else None,
                    'due_date': (
                        task.due_date.isoformat() if task.due_date else None
                    ),
                },
            )
    except Exception as e:
        print(f"[WS Error] {e}")


@login_required
def task_list(request):
    """Отображает список всех задач."""
    lists = TaskList.objects.all()
    tasks = Task.objects.filter(list__in=lists).order_by('-created_at')
    return render(request, 'tasks/list.html', {'lists': lists, 'tasks': tasks})


@login_required
def create_list(request):
    """Создаёт новый список задач."""
    if request.method == 'POST':
        form = TaskListForm(request.POST)
        if form.is_valid():
            list_obj = form.save(commit=False)
            list_obj.created_by = request.user
            list_obj.save()
            messages.success(request, 'Список задач создан!')
            return redirect('tasks:task_list')
    else:
        form = TaskListForm()
    return render(request, 'tasks/create_list.html', {'form': form})


@login_required
def create_task(request):
    """Создание новой задачи и отправка уведомлений."""
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()

            if task.assignee:
                notify_assignment.delay(task.id)
                messages.success(
                    request,
                    f'Задача создана и уведомление отправлено '
                    f'{task.assignee.email}',
                )
            else:
                messages.success(
                    request, 'Задача создана без назначения исполнителя.'
                )

            broadcast_task_update(task)
            return redirect('tasks:task_list')
    else:
        form = TaskForm(user=request.user)

    return render(request, 'tasks/create.html', {'form': form})


@login_required
def update_task(request, pk):
    """Редактирует существующую задачу."""
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            broadcast_task_update(task)
            messages.success(request, 'Задача обновлена!')
            return redirect('tasks:task_list')
    else:
        form = TaskForm(instance=task, user=request.user)
    return render(request, 'tasks/update.html', {'form': form, 'task': task})


@login_required
def complete_task(request, pk):
    """Помечает задачу как выполненную."""
    task = get_object_or_404(Task, pk=pk)
    if task.assignee != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    task.status = 'completed'
    task.save()
    broadcast_task_update(task)
    return JsonResponse({'status': 'completed'})


@login_required
def delete_task(request, pk):
    """Удаляет задачу."""
    task = get_object_or_404(Task, pk=pk)
    if task.created_by != request.user:
        messages.error(request, 'Вы можете удалить только свои задачи!')
        return redirect('tasks:task_list')

    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задача удалена!')
        broadcast_task_update(task)
        return redirect('tasks:task_list')
    return render(request, 'tasks/delete_confirm.html', {'task': task})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def bot_link_view(request):
    """Привязывает Telegram-аккаунт пользователя к сайту."""
    serializer = TelegramLinkSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data['token']
    chat_id = serializer.validated_data['chat_id']

    print("DEBUG BOT LINK >>> token:", token, "chat_id:", chat_id)

    try:
        profile = TelegramProfile.objects.get(link_token=token)
    except TelegramProfile.DoesNotExist:
        print("DEBUG BOT LINK >>> profile not found in DB")
        return Response(
            {'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST
        )

    profile.link(chat_id)
    print("DEBUG BOT LINK >>> profile found:", profile.user.email)
    return Response({'detail': 'linked'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def tasks_by_chat(request):
    """Возвращает активные задачи пользователя по chat_id."""
    chat_id = request.query_params.get('chat_id')
    if not chat_id:
        return Response(
            {'detail': 'chat_id required'}, status=status.HTTP_400_BAD_REQUEST
        )

    profile = get_object_or_404(TelegramProfile, chat_id=str(chat_id))
    user = profile.user
    queryset = (
        Task.objects.filter(assignee=user)
        .exclude(status='completed')
        .order_by('due_date')
    )
    serializer = TaskSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def complete_by_chat(request):
    """Отмечает задачу как выполненную через Telegram."""
    chat_id = request.data.get('chat_id')
    task_id = request.data.get('task_id')

    if not chat_id or not task_id:
        return Response(
            {'detail': 'chat_id and task_id required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    profile = get_object_or_404(TelegramProfile, chat_id=str(chat_id))
    user = profile.user

    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return Response({'detail': 'not found'}, status=status.HTTP_404_NOT_FOUND)

    if task.assignee != user:
        return Response({'detail': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

    task.status = 'completed'
    task.save()
    Notification.objects.create(
        user=user,
        message=f'✅ Задача "{task.title}" завершена через Telegram.',
    )
    broadcast_task_update(task)
    return Response({'detail': 'ok'}, status=status.HTTP_200_OK)
