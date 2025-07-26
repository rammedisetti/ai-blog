from django.shortcuts import render, redirect
from .forms import ContactForm, PostForm
from accounts.forms import ProfileForm, PreferencesForm, PasswordUpdateForm, SignupForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from .models import Post, Category, Tag
from accounts.models import User
from django.shortcuts import get_object_or_404
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


@login_required(login_url="accounts:login")
def toggle_like(request, post_id):
    """Toggle like on a post for the current user."""
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.liked_by.all():
        post.liked_by.remove(request.user)
    else:
        post.liked_by.add(request.user)
    return redirect("article_detail", slug=post.slug)


@login_required(login_url="accounts:login")
def toggle_save(request, post_id):
    """Toggle save on a post for the current user."""
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.saved_by.all():
        post.saved_by.remove(request.user)
    else:
        post.saved_by.add(request.user)
    return redirect("article_detail", slug=post.slug)


@login_required(login_url="accounts:login")
def update_post_status(request, post_id):
    """Allow authors to update their post status."""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    status = request.POST.get("status")
    if status in dict(Post.STATUS_CHOICES):
        post.status = status
        if status == "published" and not post.published_at:
            post.published_at = timezone.now()
        post.save()
    return redirect("user_dashboard")


@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    """Admin-only dashboard for managing authors."""
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.AUTHOR
            user.is_staff = True
            user.save()
            return redirect("admin_dashboard")
    else:
        form = SignupForm()

    authors = User.objects.filter(role=User.Role.AUTHOR)
    context = {"form": form, "authors": authors}
    return render(request, "blog/admin_dashboard.html", context)

@login_required(login_url='accounts:login')
def add_post(request):
    """Create a new blog post (authenticated users only)."""

    if request.user.role != User.Role.AUTHOR and not request.user.is_staff:
        return redirect("blog_home")

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
    else:
        form = PostForm()

    context = {"form": form, "year": datetime.now().year}
    return render(request, "blog/add_post.html", context)


def _in_group(user, group_name: str) -> bool:
    """Helper to check if a user belongs to a given group."""
    return user.groups.filter(name=group_name).exists()

@login_required(login_url="accounts:login")
@user_passes_test(lambda u: _in_group(u, "reader"))
def reader_dashboard(request):
    """Dashboard view accessible only to readers."""
    posts = Post.objects.filter(author=request.user).select_related("author")
    liked_posts = request.user.liked_posts.select_related("author")
    saved_posts = request.user.saved_posts.select_related("author")

    profile_form = ProfileForm(instance=request.user)
    pref_form = PreferencesForm(instance=request.user)
    password_form = PasswordUpdateForm(request.user)

    active_tab = "profile"  # Default active tab
    
    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated")
                return redirect("user_dashboard")
            active_tab = "profile"
        elif "update_prefs" in request.POST:
            pref_form = PreferencesForm(request.POST, instance=request.user)
            if pref_form.is_valid():
                pref_form.save()
                messages.success(request, "Preferences updated")
                return redirect("user_dashboard")
            active_tab = "prefs"
        elif "change_password" in request.POST:
            password_form = PasswordUpdateForm(request.user, request.POST)
            if password_form.is_valid():
                print("password updated form valid")
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed")
                return redirect("user_dashboard")
            active_tab = "password"

    context = {
        "posts": posts,
        "liked_posts": liked_posts,
        "saved_posts": saved_posts,
        "profile_form": profile_form,
        "pref_form": pref_form,
        "password_form": password_form,
        "year": datetime.now().year,
        "active_tab": active_tab,
    }
    return render(request, "blog/reader_dashboard.html", context)

@login_required(login_url="accounts:login")
@user_passes_test(lambda u: _in_group(u, "author"))
def author_dashboard(request):
    """Dashboard view accessible only to authors."""
    return render(request, "blog/author_dashboard.html")


@login_required(login_url="accounts:login")
@user_passes_test(lambda u: u.is_superuser)
def author_management(request):
    """Management panel reserved for superusers."""
    return render(request, "blog/author_management.html")