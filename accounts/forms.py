"""Forms for user registration."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordChangeForm,
)
from django.contrib.auth import authenticate
from .models import InterestChoices

User = get_user_model()


class SignupForm(UserCreationForm):
    """User creation form requiring unique email."""

    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "first_name",
            "last_name",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.READER
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Authentication form accepting username or email."""

    username = forms.CharField(label="Username or Email")

    def clean(self):
        username_or_email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username_or_email and password:
            user_model = get_user_model()
            try:
                user_obj = user_model.objects.get(email__iexact=username_or_email)
                username = user_obj.get_username()
            except user_model.DoesNotExist:
                username = username_or_email

            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(self.error_messages["invalid_login"], code="invalid_login")
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class ProfileForm(forms.ModelForm):
    """Form for updating basic profile information."""

    interests = forms.MultipleChoiceField(
        choices=InterestChoices.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "profile_picture_url",
            "role",
            "status",
            "location",
            "profession",
            "date_of_birth",
            "interests",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.interests:
            self.initial["interests"] = self.instance.interests

    def clean_interests(self):
        return self.cleaned_data.get("interests", [])


class PreferencesForm(forms.ModelForm):
    """Notification preference toggles for the user."""

    class Meta:
        model = User
        fields = [
            "email_notifications",
            "newsletter_subscription",
            "comment_notifications",
            "marketing_updates",
        ]


class PasswordUpdateForm(PasswordChangeForm):
    """Wrapper around Django's PasswordChangeForm for clarity."""

    pass
