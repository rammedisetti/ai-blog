from django.shortcuts import render, redirect
from .forms import ContactForm, PostForm
from accounts.forms import ProfileForm, PreferencesForm, PasswordUpdateForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .models import Post, Category, Tag
from django.utils.text import slugify
from datetime import datetime
from django.utils import timezone

def home(request):
    """Render landing page with current year."""
    from datetime import datetime

    context = {"year": datetime.now().year}
    return render(request, "blog/landing.html", context)


def blog_home(request):
    """Render the blog index page with dynamic posts."""
    from datetime import datetime

    posts = (
        Post.objects.filter(status="published")
        .select_related("author")
        .prefetch_related("categories", "tags")
    )
    categories = Category.objects.all()
    context = {"year": datetime.now().year, "posts": posts, "categories": categories}
    return render(request, "blog/blog_home.html", context)


def article_detail(request, slug):
    """Render a single article detail page from the database."""
    from datetime import datetime
    from django.shortcuts import get_object_or_404

    post = get_object_or_404(
        Post.objects.select_related("author").prefetch_related("categories", "tags"),
        slug=slug,
        status="published",
    )

    related_posts = (
        Post.objects.filter(status="published", categories__in=post.categories.all())
        .exclude(id=post.id)
        .distinct()[:3]
    )
    context = {"year": datetime.now().year, "post": post, "related_posts": related_posts}
    return render(request, "blog/article_detail.html", context)


def about(request):
    """Render the About page."""
    from datetime import datetime

    context = {"year": datetime.now().year}
    return render(request, "blog/about.html", context)


def contact(request):
    """Display and process the contact form."""
    from datetime import datetime

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            context = {
                "form": ContactForm(),
                "success": True,
                "year": datetime.now().year,
            }
            return render(request, "blog/contact.html", context)
    else:
        form = ContactForm()

    context = {"form": form, "year": datetime.now().year}
    return render(request, "blog/contact.html", context)


def privacy(request):
    """Render the Privacy Policy page."""
    from datetime import datetime

    context = {"year": datetime.now().year}
    return render(request, "blog/privacy.html", context)


def terms(request):
    """Render the Terms and Conditions page."""
    from datetime import datetime

    context = {"year": datetime.now().year}
    return render(request, "blog/terms.html", context)


def cancellation(request):
    """Render the Cancellation & Refund Policy page."""
    from datetime import datetime

    context = {"year": datetime.now().year}
    return render(request, "blog/cancellation.html", context)

@login_required(login_url='accounts:login')
def add_post(request):
    """Create a new blog post (authenticated users only)."""

    if request.method == "POST":
        form = PostForm(request.POST)    
        if form.is_valid():
            print("Form is valid")
            post = form.save(commit=False)
            post.author = request.user
            action = request.POST.get("action")
            tags_input = request.POST.get("tags_input", "")

            if action == "publish":
                post.status = "published"
                if not post.published_at:
                    post.published_at = timezone.now()
            else:
                post.status = "draft"

            post.save()
            form.save_m2m()
            if tags_input:
                tag_names = [t.strip() for t in tags_input.split(",") if t.strip()]
                tags = []
                for name in tag_names:
                    tag, _ = Tag.objects.get_or_create(
                        slug=slugify(name), defaults={"name": name}
                    )
                    tags.append(tag)
                post.tags.set(tags)
            return redirect("blog_home")
            
            if request.htmx:
                return render(request, "blog/add_post_success.html", {"post": post})

            return redirect("blog_home")
    else:
        form = PostForm()

    context = {"form": form, "year": datetime.now().year}
    return render(request, "blog/add_post.html", context)

@login_required(login_url="accounts:login")
def user_dashboard(request):
    """Display and update the user's profile and related settings."""
    from datetime import datetime

    posts = Post.objects.filter(author=request.user).select_related("author")

    profile_form = ProfileForm(instance=request.user)
    pref_form = PreferencesForm(instance=request.user)
    password_form = PasswordUpdateForm(request.user)

    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated")
                return redirect("user_dashboard")
        elif "update_prefs" in request.POST:
            print("prefs updated")
            pref_form = PreferencesForm(request.POST, instance=request.user)
            if pref_form.is_valid():
                pref_form.save()
                messages.success(request, "Preferences updated")
                return redirect("user_dashboard")
        elif "change_password" in request.POST:
            password_form = PasswordUpdateForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed")
                return redirect("user_dashboard")

    context = {
        "posts": posts,
        "profile_form": profile_form,
        "pref_form": pref_form,
        "password_form": password_form,
        "year": datetime.now().year,
    }
    return render(request, "blog/user_dashboard.html", context)
