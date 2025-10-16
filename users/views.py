from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from .forms import MyUserCreationForm, MyUserChangeForm
from functools import wraps
from tasks.models import Task, Notification
from django.views.decorators.http import require_http_methods
from django.conf import settings
from tasks.models import TelegramProfile


def home(request):
    if request.user.is_authenticated:
        return redirect('tasks:task_list')
    return render(request, 'users/home.html')


def permission_required(resource, action):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.path.startswith('/rbac/api/'):
                    return HttpResponse('Unauthorized: Login required.', status=401)
                messages.error(request, 'Доступ запрещён: Не авторизованы.')
                return redirect('users:login')

            if not request.user.has_permission(resource, action):
                if request.path.startswith('/rbac/api/'):
                    return HttpResponseForbidden('Forbidden: No permission.')
                messages.error(request, f'Доступ запрещён: Нет прав на {action} {resource}.')
                return redirect('users:home')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def register(request):
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Регистрация успешна! Теперь создайте задачи.')
                return redirect('tasks:task_list')
            else:
                messages.error(request, 'Ошибка аутентификации после регистрации.')
    else:
        form = MyUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Вход выполнен! Переходим к задачам.')
                return redirect('tasks:task_list')
            messages.error(request, 'Неверный email или пароль.')
        else:
            messages.error(request, 'Введите email и пароль.')
    return render(request, 'users/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы.')
    return redirect('users:login')


@login_required
def profile(request):
    user = request.user
    recent_tasks = Task.objects.filter(created_by=request.user)[:5]
    total_tasks = Task.objects.filter(created_by=request.user).count()
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    recent_notifications = Notification.objects.filter(user=request.user)[:3]
    return render(request, 'users/profile.html', {
        'user': user,
        'recent_tasks': recent_tasks,
        'total_tasks': total_tasks,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
    })


@login_required
def notifications(request):
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        mark_all = request.POST.get('mark_all_read')
        notification_id = request.POST.get('notification_id')

        if mark_all == 'true':
            # Mark all as read (все unread, включая дубли)
            updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            unread_count = 0
            messages.success(request, f'Все уведомления помечены как прочитанные ({updated} шт.).')
        elif notification_id:
            # Mark single as read
            updated = Notification.objects.filter(id=notification_id, user=request.user, is_read=False).update(is_read=True)
            if updated:
                unread_count -= 1
                messages.success(request, 'Уведомление помечено как прочитанное.')
            else:
                messages.warning(request, 'Уведомление уже прочитано.')

        # Redirect для reload (обновление badge/list)
        return redirect('users:notifications')

    return render(request, 'users/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })

# API для поллинга badge (динамическое обновление)
@login_required
@require_http_methods(['GET'])
def unread_count_api(request):
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def profile_update(request):
    user = request.user
    if request.method == 'POST':
        form = MyUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('tasks:task_list')
    else:
        form = MyUserChangeForm(instance=user)
    return render(request, 'users/profile_update.html', {'form': form})

@login_required
def profile_delete(request):
    user = request.user
    if request.user != user:
        messages.error(request, 'Вы можете удалить только свой аккаунт.')
        return redirect('users:profile')

    if request.method == 'POST':
        try:
            user.soft_delete()
            logout(request)
            messages.success(request, 'Аккаунт удалён. Вы вышли из системы.')
            return redirect('users:home')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            return redirect('users:profile')
    else:
        return render(request, 'users/delete_confirm.html', {'user': user})

@login_required
def telegram_link_view(request):
    """Показывает пользователю токен и ссылку на Telegram-бота."""
    # Создаём профиль Telegram, если его нет
    profile, _ = TelegramProfile.objects.get_or_create(user=request.user)

    # Берём имя бота из .env
    bot_username = getattr(settings, "TG_BOT_USERNAME", None)

    context = {
        "token": profile.link_token,
        "bot_username": bot_username,
    }
    return render(request, "users/telegram_link.html", context)
