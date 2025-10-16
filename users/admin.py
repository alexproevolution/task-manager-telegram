from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django import forms
from django.utils import timezone
from django.utils.html import format_html
from .models import MyUser
from tasks.models import TelegramProfile


# --- ФОРМЫ ---

class MyUserChangeForm(forms.ModelForm):
    """Форма изменения пользователя в админке (с read-only полем пароля)."""
    password = ReadOnlyPasswordHashField(
        label="Пароль",
        help_text=(
            "Пароли не сохраняются в открытом виде. "
            "Вы можете изменить пароль с помощью "
            "<a href=\"../password/\">этой формы</a>."
        ),
    )

    class Meta:
        model = MyUser
        fields = (
            'email', 'password', 'first_name', 'last_name', 'middle_name',
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
            'deleted_at', 'date_joined',
        )


class MyUserCreationForm(forms.ModelForm):
    """Форма создания пользователя в админке."""
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ('email', 'first_name', 'last_name', 'middle_name')

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Пароли не совпадают")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class TelegramProfileInline(admin.StackedInline):
    model = TelegramProfile
    can_delete = False
    extra = 0

    # здесь перечисляем "виртуальные" поля (методы) как readonly_fields
    readonly_fields = (
        'link_token_display',
        'open_link',
        'linked_at',
        'chat_id',
        'regenerate_token_button',
    )

    # какие поля показываем в inline-форме (regenerate_token_button — виртуальное)
    fields = (
        'chat_id',
        'link_token_display',
        'open_link',
        'linked_at',
        'regenerate_token_button',
    )

    # укажи username своего бота без @
    bot_username = "ITDeveloper_bot"

    def link_token_display(self, obj):
        if not obj or not obj.link_token:
            return "—"
        return format_html("<code>{}</code>", obj.link_token)
    link_token_display.short_description = "Link-токен"

    def open_link(self, obj):
        if not obj or not obj.link_token:
            return "—"
        url = f"https://t.me/{self.bot_username}?start={obj.link_token}"
        return format_html('<a class="button" href="{}" target="_blank">Открыть в Telegram</a>', url)
    open_link.short_description = "Ссылка для привязки"

    def regenerate_token_button(self, obj):
        if not obj or not obj.pk:
            return "—"
        return format_html(
            '<a class="button" href="{}">🔄 Сгенерировать новый токен</a>',
            f"../regenerate_token/{obj.pk}/"
        )
    regenerate_token_button.short_description = "Действие"



# --- АДМИНКА ПОЛЬЗОВАТЕЛЯ ---

class MyUserAdmin(BaseUserAdmin):
    """Кастомная админка для MyUser."""
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    inlines = [TelegramProfileInline]

    list_display = (
        'email',
        'first_name',
        'last_name',
        'middle_name',
        'is_staff',
        'is_active',
        'deleted_at',
        'date_joined'
    )

    list_filter = (
        'is_staff', 
        'is_superuser', 
        'is_active', 
        'date_joined',
        'deleted_at',
    )

    search_fields = ('email', 'first_name', 'last_name', 'middle_name')
    ordering = ('last_name', 'first_name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {
            'fields': ('first_name', 'last_name', 'middle_name')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Даты', {'fields': ('date_joined', 'deleted_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'middle_name',
                'password1', 'password2', 'is_staff', 'is_active'
            ),
        }),
    )

    readonly_fields = ('date_joined', 'deleted_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(deleted_at__isnull=True, is_active=True)

    def delete_model(self, request, obj):
        """Мягкое удаление одного пользователя."""
        obj.is_active = False
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['is_active', 'deleted_at'])

    def delete_queryset(self, request, queryset):
        """Мягкое удаление нескольких пользователей."""
        queryset.update(is_active=False, deleted_at=timezone.now())

    def undelete_users(self, request, queryset):
        """Восстановить выбранных удалённых пользователей."""
        count = 0
        for user in queryset:
            if not user.is_active and user.deleted_at:
                user.is_active = True
                user.deleted_at = None
                user.save(update_fields=['is_active', 'deleted_at'])
                count += 1
        self.message_user(request, f'Восстановлено {count} пользователей.')
    undelete_users.short_description = 'Восстановить выбранных пользователей'

    actions = ['delete_queryset', 'undelete_users']


admin.site.register(MyUser, MyUserAdmin)
