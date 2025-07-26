"""Views for the accounts app."""

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, SignupForm


@require_http_methods(["GET", "POST"])
def signup(request):
    """Handle user signup with email and password confirmation."""
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        return render(
            request,
            "accounts/auth_split.html",
            {
                "signup_form": form,
                "login_form": LoginForm(),
                "active_form": "signup",
            },
        )

    # For GET requests redirect to the combined auth page
    return redirect(f"{reverse('accounts:auth_split')}?form=signup")


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Authenticate user by username or email and redirect to home."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("home")
        return render(
            request,
            "accounts/auth_split.html",
            {
                "signup_form": SignupForm(),
                "login_form": form,
                "active_form": "login",
            },
        )

    # For GET requests redirect to the combined auth page
    return redirect(f"{reverse('accounts:auth_split')}?form=login")


def auth_split(request):
    """Render split-screen auth page with signup and login forms."""
    active = request.GET.get("form", "signup")
    if active not in {"login", "signup"}:
        active = "signup"

    context = {
        "signup_form": SignupForm(),
        "login_form": LoginForm(),
        "active_form": active,
    }
    return render(request, "accounts/auth_split.html", context)

@require_http_methods(["POST"])
def logout_view(request):
    """Log out the user and redirect to home."""
    logout(request)
    return redirect("accounts:login")



class ForgotPasswordView(PasswordResetView):
    """Start password reset by sending an email to the user."""

    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class ForgotPasswordDoneView(PasswordResetDoneView):
    """Display a message after the reset email is sent."""

    template_name = "accounts/password_reset_done.html"


class ForgotPasswordConfirmView(PasswordResetConfirmView):
    """Allow the user to set a new password via the emailed link."""

    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class ForgotPasswordCompleteView(PasswordResetCompleteView):
    """Confirmation page shown after the password has been reset."""

    template_name = "accounts/password_reset_complete.html"