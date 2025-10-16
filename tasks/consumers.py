import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            await self.channel_layer.group_add(
                f'user_{self.user.id}_group',  # Приватная группа для уведомлений
                self.channel_name
            )
        await self.channel_layer.group_add(
            'tasks_group',  # Общая для task_update
            self.channel_name
        )
        await self.accept()
        print(f"WS connected for user {self.user.email if self.user.is_authenticated else 'anonymous'}")

    async def disconnect(self, close_code):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f'user_{self.user.id}_group',
                self.channel_name
            )
        await self.channel_layer.group_discard(
            'tasks_group',
            self.channel_name
        )
        print(f"WS disconnected")

    async def task_update(self, event):
        # Обновление задачи (глобально)
        await self.send(text_data=json.dumps({
            'type': 'task_update',
            'task_id': event['task_id'],
            'title': event['title'],
            'status': event['status'],
            'assignee': event['assignee'],
            'due_date': event['due_date'],
        }))

    async def notification(self, event):
        # Уведомление (user-specific)
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'notification_id': event['notification_id'],
            'unread_count': event['unread_count'],
            'user_id': event.get('user_id', self.user.id if self.user.is_authenticated else None),
        }))
