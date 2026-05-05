from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Profile(models.Model):
    """Модель профиля."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    avatar = models.ImageField(
        upload_to="avatars/", blank=True, null=True, verbose_name="Аватарка"
    )

    bio = models.TextField(blank=True, verbose_name="О себе", max_length=2000)

    github_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="GitHub",
        help_text="https://github.com/username",
    )

    telegram = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Telegram",
        help_text="@username или https://t.me/...",
    )

    is_statistics_public = models.BooleanField(
        default=False,
        verbose_name="Public statistics",
        help_text="Allow other users to view profile statistics.",
    )

    def __str__(self):
        return f"Профиль {self.user.username}"

    @property
    def avatar_initials(self):
        if self.user.first_name and self.user.last_name:
            return (self.user.first_name[0] + self.user.last_name[0]).upper()
        return self.user.username[:2].upper()
    
    class Meta:
        verbose_name = _("Профиль")
        verbose_name_plural = _("Профили")

# Автоматическое создание профиля при регистрации пользователя
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)
