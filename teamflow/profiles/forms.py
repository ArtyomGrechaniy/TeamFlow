from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    """Форма создания и редактирования профиля."""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Имя",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label="Фамилия",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Profile
        fields = ["avatar", "bio", "github_url", "telegram", "is_statistics_public"]
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "github_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://github.com/username",
                }
            ),
            "telegram": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "@username или https://t.me/...",
                }
            ),
            "is_statistics_public": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            user = profile.user
            user.first_name = self.cleaned_data.get("first_name", "")
            user.last_name = self.cleaned_data.get("last_name", "")
            user.save()
        return profile
