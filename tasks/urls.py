from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api

app_name = 'tasks'

router = DefaultRouter()
router.register(r'tasks', api.TaskViewSet, basename='tasks')

urlpatterns = [
    # Веб-интерфейс
    path('', views.task_list, name='task_list'),
    path('lists/create/', views.create_list, name='create_list'),
    path('create/', views.create_task, name='create_task'),
    path('update/<int:pk>/', views.update_task, name='update_task'),
    path('complete/<int:pk>/', views.complete_task, name='complete_task'),
    path('delete/<int:pk>/', views.delete_task, name='delete_task'),

    # Telegram Bot API
    path('api/bot/link/', views.bot_link_view, name='bot-link'),
    path('api/bot/tasks_by_chat/',
         views.tasks_by_chat,
         name='bot-tasks-by-chat'),
    path('api/bot/complete_by_chat/',
         views.complete_by_chat,
         name='bot-complete-by-chat'),

    # DRF Router
    path('api/', include(router.urls)),

]
