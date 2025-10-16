from django import forms
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from .models import MyUser


class MyUserCreationForm(BaseUserCreationForm):
    """Форма создания пользователя (для админки и API)."""
    first_name = forms.CharField(
        max_length=50,
        label="Имя",
        required=True
    )
    last_name = forms.CharField(
        max_length=50,
        label="Фамилия",
        required=True
    )
    middle_name = forms.CharField(
        max_length=50,
        label="Отчество",
        required=False,
        help_text="Отчество (необязательно)"
    )
    email = forms.EmailField(
        label="Email",
        required=True,
        help_text="Email будет использоваться для входа"
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
        help_text="Пароль должен содержать минимум 8 символов."
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        help_text="Введите пароль ещё раз для подтверждения."
    )

    class Meta:
        model = MyUser 
        fields = ('first_name', 'last_name', 'middle_name', 'email')

    def clean_password2(self):
        """Проверка совпадения паролей."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают!")
        return password2

    def save(self, commit=True):
        """Сохранение: хэширует пароль и создаёт пользователя."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class MyUserChangeForm(BaseUserChangeForm):
    """Форма изменения профиля (для пользователя, без пароля и админских полей)."""
    first_name = forms.CharField(
        max_length=50,
        label="Имя",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=50,
        label="Фамилия",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    middle_name = forms.CharField(
        max_length=50,
        label="Отчество",
        required=False,
        help_text="Отчество (необязательно)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        required=True,
        help_text="Email используется для входа и не может быть изменён.",
        widget=forms.EmailInput(attrs={
            'readonly': 'readonly',
            'class': 'form-control'
        })
    )

    class Meta:
        model = MyUser 
        fields = ('first_name', 'last_name', 'middle_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            del self.fields['password']
        
        for field in ['is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login']:
            if field in self.fields:
                del self.fields[field]

        instance = kwargs.get('instance')
        if instance:
            self.fields['email'].initial = instance.email
            self.fields['email'].widget.attrs['value'] = instance.email

    def save(self, commit=True):
        """Сохранение: Только профильные поля, пароль не трогаем."""
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
