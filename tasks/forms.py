from django import forms
from .models import Task, TaskList


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title', 'description', 'list', 'assignee', 'due_date', 'status')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['assignee'].queryset = user.__class__.objects.filter(is_active=True)
            self.fields['assignee'].initial = user
            self.fields['list'].queryset = TaskList.objects.filter()

class TaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
