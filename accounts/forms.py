"""Forms for user registration."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate

User = get_user_model()


class SignupForm(UserCreationForm):
    """User creation form requiring unique email."""

    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email


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
