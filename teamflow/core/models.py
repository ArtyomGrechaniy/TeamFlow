from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode


class BaseCategory(models.Model):
    """Абстрактная базовая модель для всех категорий"""

    name = models.CharField(max_length=100, verbose_name=_("Название"))
    slug = models.SlugField(
        max_length=120, blank=True, default="", verbose_name=_("Slug")
    )

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
