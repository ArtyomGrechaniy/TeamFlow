from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from core.models import BaseCategory
from teams.models import Team

User = get_user_model()


class TaskCategory(BaseCategory):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_categories',
        verbose_name=_('Пользователь'),
        null=True,
        blank=True,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='task_categories',
        verbose_name=_('Команда'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Категория задач')
        verbose_name_plural = _('Категории задач')
        ordering = ['name']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['team']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['user', 'slug'], name='unique_task_slug_per_user', condition=models.Q(user__isnull=False)),
            models.UniqueConstraint(fields=['team', 'slug'], name='unique_task_slug_per_team', condition=models.Q(team__isnull=False)),

            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, team__isnull=True) |
                    models.Q(user__isnull=True, team__isnull=False)
                ),
                name='task_category_belongs_to_either_user_or_team'
            ),
        ]

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tasks:task_category_detail', kwargs={'slug': self.slug})


class Task(models.Model):
    class Priority(models.IntegerChoices):
        LOW = 25, 'Низкий'
        MEDIUM = 50, 'Средний'
        HIGH = 75, 'Высокий'
        URGENT = 100, 'Срочный'
    class Status(models.IntegerChoices):
        TODO = 100, 'К выполнению'
        IN_PROGRESS = 75, 'В работе'
        DONE = 50, 'Выполнено'
        ARCHIVED = 25, 'В архиве'

    title = models.CharField(max_length=200, verbose_name="Название задачи")
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.TODO.value, verbose_name="Статус")
    priority = models.PositiveSmallIntegerField(choices=Priority.choices, default=Priority.MEDIUM.value, verbose_name="Приоритет")
    deadline = models.DateField(null=True, blank=True, verbose_name="Дедлайн")

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Создатель"
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Команда"
    )
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Категория"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name="Исполнитель"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.deadline and self.status != 'done':
            return self.deadline < timezone.now().date()
        return False

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['team', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['deadline']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, team__isnull=True) |
                    models.Q(user__isnull=True, team__isnull=False)
                ),
                name='task_belongs_to_either_user_or_team'
            )
        ]

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tasks:task_detail', kwargs={'pk': self.pk})

