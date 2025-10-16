from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Task
from .serializers import TaskSerializer
from .views import broadcast_task_update

class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        if task.assignee != request.user:
            return Response({'error': 'No permission'}, status=403)
        task.status = 'completed'
        task.save()
        broadcast_task_update(task)  # Синхронизация с веб (WS)
        return Response({'status': 'completed'})