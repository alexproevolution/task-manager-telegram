from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/delete/', views.profile_delete, name='profile_delete'),
    path('', views.home, name='home'),
    path('notifications/', views.notifications, name='notifications'),
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),
    path('telegram-link/', views.telegram_link_view, name='telegram_link'),
]
