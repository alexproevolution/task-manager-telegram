from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    # Аутентификация через users app с namespace
    path('users/', include('users.urls', namespace='users')),
    # Задачи (HTML + API)
    path('tasks/', include('tasks.urls')),
    # API (DRF: токены, login UI)
    path('api-auth/', include('rest_framework.urls')),
    # ← НОВОЕ: Явный /api/ для tasks (ViewSet на /api/tasks/)
    path('api/', include('tasks.urls')),
    # Главная / — редирект на users:home (или tasks, если готово)
    re_path(r'^.*$', RedirectView.as_view(url='/users/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT
                          )
