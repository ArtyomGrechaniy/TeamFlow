from decimal import Decimal

from core.models import BaseCategory
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from teams.models import Team
from unidecode import unidecode

User = get_user_model()


class CurrencyRate(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'Доллар США'),
        ('EUR', 'Евро'),
        ('CNY', 'Китайский юань'),
    ]

    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, unique=True)
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = "Курс валюты"
        verbose_name_plural = "Курсы валют"
        ordering = ['-date']

    def __str__(self):
        return f"{self.currency} — {self.rate} ₽ ({self.date})"


class ExpenseCategory(BaseCategory):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expense_categories',
        verbose_name=_('Пользователь'),
        null=True,
        blank=True,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='expense_categories',
        verbose_name=_('Команда'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Категория расходов')
        verbose_name_plural = _('Категории расходов')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'slug'],
                name='unique_expense_slug_per_user',
                condition=models.Q(user__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['team', 'slug'],
                name='unique_expense_slug_per_team',
                condition=models.Q(team__isnull=False)
            ),
        ]

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('expenses:category_detail', kwargs={'slug': self.slug})


class Expense(models.Model):
    CURRENCY_CHOICES = [
        ('RUB', '₽ Российский рубль'),
        ('USD', '$ Доллар США'),
        ('EUR', '€ Евро'),
        ('CNY', '¥ Юань'),
    ]
    title = models.CharField(
        max_length=200,
        verbose_name='Наименование расхода',
        blank=False
    )
    description = models.TextField(
        max_length=2000,
        verbose_name=_('Описание'),
        blank=True,
        default='',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Сумма'),
        validators=[MinValueValidator(Decimal('0.1'))]
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='RUB'
    )
    exchange_rate = models.DecimalField(
    max_digits=10, 
    decimal_places=4, 
    null=True, 
    blank=True,
    verbose_name="Курс на момент создания"
    )
    amount_rub = models.DecimalField(
    max_digits=12, 
    decimal_places=2, 
    null=True, 
    blank=True,
    verbose_name="Сумма в RUB"
    )  
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name=_('Пользователь'),
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name=_('Команда'),
    )
    category = models.ForeignKey(
        'ExpenseCategory',
        on_delete=models.SET_NULL,
        related_name='expenses',
        verbose_name=_('Категория'),
        null=True,
        blank=True,
    )
    date = models.DateField(
        verbose_name=_('Дата расхода'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата последнего изменения'),
    )

    class Meta:
        verbose_name = _('Расход')
        verbose_name_plural = _('Расходы')
        ordering = ['-date', '-amount']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['category']),
            models.Index(fields=['date']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, team__isnull=True) |
                    models.Q(user__isnull=True, team__isnull=False)
                ),
                name='expense_belongs_to_either_user_or_team'
            )
        ]

    def get_currency_symbol(self):
        symbols = {'RUB': '₽', 'USD': '$', 'EUR': '€', 'CNY': '¥'}
        return symbols.get(self.currency, self.currency)

    def __str__(self):
        cat = self.category.name if self.category else 'Без категории'
        owner = self.user.username if self.user else f'Команда "{self.team.name }"'
        return f'{owner} — {self.date} — {self.amount} ₽ ({cat})'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('expenses:expense_detail', kwargs={'pk': self.pk})