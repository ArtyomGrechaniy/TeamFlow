from django.db import models
from django.contrib.auth import get_user_model
import secrets
import string
User = get_user_model()


class Team(models.Model):
    name = models.CharField(max_length=120, verbose_name="Название команды")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="owned_teams",
        verbose_name="Владелец"
    )

    invite_code = models.CharField(
        max_length=12,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="Код приглашения"
    )

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = ''.join(
                secrets.choice(string.ascii_lowercase + string.digits) 
                for _ in range(12)
            )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"
        ordering = ['-created_at']


class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('member', 'Участник'),
        ('admin', 'Администратор'),
        ('owner', 'Владелец')
    ]
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name="members", 
        verbose_name="Команда"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="team_memberships", 
        verbose_name="Пользователь"
    )
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='member',
        verbose_name="Роль"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'user')
        verbose_name = 'Участник команды'
        verbose_name_plural = "Участники команд"

    def __str__(self):
        return f"{self.user.username} в {self.team.name}"
    