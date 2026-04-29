from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from unidecode import unidecode
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Аватарка"
    )

    bio = models.TextField(blank=True, verbose_name="О себе", max_length=2000)

    github_url = models.URLField(
        max_length=200, blank=True, null=True, 
        verbose_name="GitHub", help_text="https://github.com/username"
    )

    telegram = models.CharField(
        max_length=50, blank=True, null=True, 
        verbose_name="Telegram", help_text="@username или https://t.me/..."
    )

    def __str__(self):
        return f'Профиль {self.user.username}'
    
    @property
    def avatar_initials(self):
        if self.user.first_name and self.user.last_name:
            return (self.user.first_name[0] + self.user.last_name[0]).upper()
        return self.user.username[:2].upper()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class BaseCategory(models.Model):
    """Абстрактная базовая модель для всех категорий"""
    name = models.CharField(max_length=100, verbose_name=_('Название'))
    slug = models.SlugField(max_length=120, blank=True, default='', verbose_name=_('Slug'))

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.capitalize()
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name