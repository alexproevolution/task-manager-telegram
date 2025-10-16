from rest_framework import serializers

from .models import Task, TaskList
from django.contrib.auth import get_user_model

User  = get_user_model()


class TelegramLinkSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    chat_id = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для User (email + имя для assignee/created_by)."""
    class Meta:
        model = User
        fields = ('id', 'email', 'get_full_name')
        read_only_fields = ('id', 'email', 'get_full_name')


class TaskListSerializer(serializers.ModelSerializer):
    """Сериализатор для TaskList (список задач)."""
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = TaskList
        fields = ('id', 'name', 'created_by', 'created_at')
        read_only_fields = ('id', 'created_by', 'created_at')


class TaskCreateSerializer(serializers.ModelSerializer):
    """Для создания/обновления (не read_only для editable полей)."""
    class Meta:
        model = Task
        fields = ('title', 'description', 'list', 'assignee', 'due_date', 'status')
        extra_kwargs = {
            'due_date': {'input_formats': ['%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']},  # Форматы даты
        }


class TaskSerializer(serializers.ModelSerializer):
    """Полный сериализатор для Task (все поля + связи)."""
    list = TaskListSerializer(read_only=True)  # Вложенный список
    assignee = UserSerializer(read_only=True)  # Assignee как объект
    created_by = UserSerializer(read_only=True)  # Создатель
    
    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description', 'list', 'assignee', 'due_date', 
            'status', 'created_by', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')
        extra_kwargs = {
            'due_date': {'input_formats': ['%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']},
        }
