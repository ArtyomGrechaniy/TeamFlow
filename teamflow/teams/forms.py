from django import forms

from .models import Team


class TeamForm(forms.ModelForm):
    """Форма создания и редактирования команды."""

    class Meta:
        """Настройки полей и Bootstrap-виджетов формы команды."""

        model = Team
        fields = ("name", "description")
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Название команды"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Краткое описание команды (необязательно)",
                }
            ),
        }
