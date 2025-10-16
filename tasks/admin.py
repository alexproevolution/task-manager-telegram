from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.html import format_html
from .models import TaskList, Task, Notification, TelegramProfile


@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'list', 'assignee', 'status',
        'due_date', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'due_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at', 'user']
    search_fields = ['message', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        """Action — отметить выбранные уведомления как прочитанные."""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'Помечено как прочитанные {updated} уведомлений.')
    mark_as_read.short_description = "Пометить выбранные как прочитанные"


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat_id', 'linked_at', 'link_token', 'open_link')
    search_fields = ('user__email', 'chat_id')
    fields = (
        'user', 'chat_id',
        'link_token_display', 'open_link',
        'linked_at', 'regenerate_token_button'
    )

    readonly_fields = (
        'link_token_display', 'open_link',
        'linked_at', 'chat_id', 'regenerate_token_button'
    )

    bot_username = "ITDeveloper_bot"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "regenerate_token/<int:pk>/",
                self.admin_site.admin_view(self.regenerate_token),
                name="telegramprofile_regenerate_token",
            ),
        ]
        return custom_urls + urls

    def regenerate_token(self, request, pk):
        """Обновляет токен и возвращает обратно в админку пользователя."""
        profile = get_object_or_404(TelegramProfile, pk=pk)
        profile.regenerate_token()
        messages.success(request, f"✅ Новый токен сгенерирован: {profile.link_token}")
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))

    def link_token_display(self, obj):
        """Показать токен красиво."""
        if not obj or not obj.link_token:
            return "—"
        return format_html("<code>{}</code>", obj.link_token)
    link_token_display.short_description = "Link-токен"

    def open_link(self, obj):
        """Кнопка 'Открыть в Telegram'."""
        if not obj or not obj.link_token:
            return "—"
        url = f"https://t.me/{self.bot_username}?start={obj.link_token}"
        return format_html(
            '<a class="button" href="{}" target="_blank">Открыть в Telegram</a>', url
        )
    open_link.short_description = "Ссылка для привязки"

    def regenerate_token_button(self, obj):
        """Кнопка для регенерации токена прямо в форме."""
        if not obj or not obj.pk:
            return "—"
        return format_html(
            '<a class="button" href="{}">🔄 Сгенерировать новый токен</a>',
            f"../regenerate_token/{obj.pk}/"
        )
    regenerate_token_button.short_description = "Действие"
