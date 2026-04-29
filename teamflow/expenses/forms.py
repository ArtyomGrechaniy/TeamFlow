from decimal import Decimal

from django import forms
from django.db.models import Q
from teams.models import TeamMember

from .models import CurrencyRate, Expense, ExpenseCategory


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ('title', 'description', 'amount', 'currency', 'date', 'category', 'team')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'team': forms.HiddenInput(),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Сумма расхода должна быть больше нуля.')
        return amount

    def __init__(self, *args, **kwargs):
        self.team_id = kwargs.pop('team_id', None)
        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['category'].queryset = ExpenseCategory.objects.filter(
                Q(user=self.user) | 
                Q(team__in=TeamMember.objects.filter(user=self.user).values_list('team', flat=True))
            ).distinct()

        if self.team_id:
            self.fields['category'].queryset = ExpenseCategory.objects.filter(
                team_id = self.team_id
            ).distinct()

        if self.team_id:
            self.fields['team'].initial = self.team_id

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.currency == 'RUB':
            instance.exchange_rate = Decimal('1.0000')
            instance.amount_rub = instance.amount
        else:
            try:
                rate = CurrencyRate.objects.get(currency=instance.currency).rate
                instance.exchange_rate = rate
                instance.amount_rub = instance.amount * rate
            except CurrencyRate.DoesNotExist:
                instance.exchange_rate = None
                instance.amount_rub = None

        if self.team_id:
            instance.user = None
            instance.team_id = self.team_id
        else:
            instance.user = self.user
            instance.team = None

        if commit:
            instance.save()
        return instance



class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Еда, Транспорт, Развлечения...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.team_id = kwargs.pop('team_id', None)
        super().__init__(*args, **kwargs)
