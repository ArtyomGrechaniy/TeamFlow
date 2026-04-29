from django import forms
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Task, TaskCategory
from teams.models import TeamMember

User = get_user_model()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'deadline', 'category', 'assigned_to']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.team_id = kwargs.pop('team_id', None)
        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        if not self.team_id and 'assigned_to' in self.fields:
            del self.fields['assigned_to']

        if self.team_id:
            self.fields['category'].queryset = TaskCategory.objects.filter(team_id=self.team_id)
        elif self.user:
            self.fields['category'].queryset = TaskCategory.objects.filter(
                Q(user=self.user) | 
                Q(team__in=TeamMember.objects.filter(user=self.user).values_list('team', flat=True))
            ).distinct()

        if self.team_id and 'assigned_to' in self.fields:
            self.fields['assigned_to'].queryset = User.objects.filter(
                team_memberships__team_id=self.team_id
            ).distinct()

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user:
            instance.user = self.user

        if self.team_id:
            instance.team_id = self.team_id
            instance.user = None
        else:
            instance.team = None

        if commit:
            instance.save()
        return instance


class TaskCategoryForm(forms.ModelForm):
    class Meta:
        model = TaskCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Еда, Транспорт, Развлечения...'
            }),
        }