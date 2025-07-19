"""Views for the accounts app."""

from django.contrib.auth import login
from django.shortcuts import redirect, render
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
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


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
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})
