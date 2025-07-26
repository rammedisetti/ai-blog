from django.shortcuts import render, redirect
from .forms import ContactForm, PostForm, CommentForm
from accounts.forms import ProfileForm, PreferencesForm, PasswordUpdateForm, SignupForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from .models import Post, Category, Tag, UserSavedPost, Comment
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
        Post.objects.select_related("author").prefetch_related(
            "categories", "tags", "comments__user", "liked_by", "saved_by"
        ),
        slug=slug,
        status="published",
    )

    if request.method == "POST" and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.user = request.user
            new_comment.status = "pending"
            new_comment.save()
            return redirect("article_detail", slug=slug)
    else:
        comment_form = CommentForm()

    # Check if the post is saved by the user
    is_saved = request.user.is_authenticated and request.user in post.saved_by.all()
    # check if the user has already liked the post
    is_liked = request.user.is_authenticated and request.user in post.liked_by.all()
    #check for user role
    user_role = None
    if request.user.is_authenticated:
        user_role = "reader" if request.user.groups.filter(name="reader").exists() else "author"

    # Related posts (same categories, not this post)
    related_posts = (
        Post.objects.filter(status="published", categories__in=post.categories.all())
        .exclude(id=post.id)
        .distinct()[:3]
    )
    # Comments (approved only)
    comments = Comment.objects.filter(post=post, status="approved").order_by('created_at')

    # Stats
    like_count = post.liked_by.count()
    save_count = post.saved_by.count()
    comment_count = comments.count()
    view_count = post.view_count

    context = {
        "year": datetime.now().year,
        "post": post,
        "related_posts": related_posts,
        "comments": comments,
        "comment_form": comment_form,
        "like_count": like_count,
        "save_count": save_count,
        "comment_count": comment_count,
        "view_count": view_count + 1,
        "is_saved": is_saved,
        "is_liked": is_liked,
        "user_role": user_role,
    }
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
@user_passes_test(lambda u: _in_group(u, "reader"))
def toggle_like(request, post_id):
    """Toggle like on a post for the current user."""
    post = get_object_or_404(Post, id=post_id, status="published")
    if request.user in post.liked_by.all():
        post.liked_by.remove(request.user)
        liked = False
    else:
        post.liked_by.add(request.user)
        liked = True
    if request.htmx:
        is_liked = post.liked_by.filter(id=request.user.id).exists()
        context = {"post": post, "is_liked": is_liked}
        return render(request, "blog/partials/like_button.html", context)
    return redirect("article_detail", slug=post.slug)


@login_required(login_url="accounts:login")
@user_passes_test(lambda u: _in_group(u, "reader"))
def toggle_save(request, post_id):
    """Toggle save on a post for the current user."""
    post = get_object_or_404(Post, id=post_id, status="published")
    saved, created = UserSavedPost.objects.get_or_create(user=request.user, post=post)
    if not created and saved.is_active:
        saved.is_active = False
        saved.save()
        post.saved_by.remove(request.user)
        is_saved = False
    else:
        saved.is_active = True
        saved.save()
        post.saved_by.add(request.user)
        is_saved = True
    if request.htmx:
        context = {"post": post, "is_saved": is_saved}
        return render(request, "blog/partials/save_button.html", context)
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
    return redirect("author_dashboard")

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
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser:
        return redirect("author_management")
    elif hasattr(user, "role") and user.role == User.Role.AUTHOR:
        return redirect("author_dashboard")
    elif hasattr(user, "role") and user.role == User.Role.READER:
        return redirect("reader_dashboard")
    else:
        return redirect("home")

@login_required(login_url="accounts:login")
@user_passes_test(lambda u: _in_group(u, "reader"))
def reader_dashboard(request):
    """Dashboard view accessible only to readers."""
    liked_posts = request.user.liked_posts.select_related("author")
    saved_relations = (
        UserSavedPost.objects.filter(user=request.user, is_active=True)
        .select_related("post__author")
        .order_by("-saved_at")
    )
    saved_posts = [rel.post for rel in saved_relations]
    saved_at_map = {rel.post_id: rel.saved_at for rel in saved_relations} #to verify this logic later on
    saved_categories = Category.objects.filter(posts__in=saved_posts)
    related_posts = (
        Post.objects.filter(status="published", categories__in=saved_categories)
        .exclude(id__in=[p.id for p in saved_posts])
        .distinct()[:3]
    )

     # Remove 'role' from the profile form fields for readers
    class ReaderProfileForm(ProfileForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if "role" in self.fields:
                self.fields["role"].disabled = True  # or use del self.fields["role"] to hide completely

    profile_form = ReaderProfileForm(instance=request.user)
    pref_form = PreferencesForm(instance=request.user)
    password_form = PasswordUpdateForm(request.user)

    active_tab = "profile"  # Default active tab
    
    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = ReaderProfileForm(request.POST, instance=request.user)
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
        "saved_posts": saved_posts,
        "saved_at_map": saved_at_map,
        "liked_posts": liked_posts,
        "related_posts": related_posts,
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
    posts = Post.objects.filter(author=request.user).prefetch_related("comments", "liked_by", "saved_by")
    # Remove 'role' from the profile form fields for authors
    class AuthorProfileForm(ProfileForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if "role" in self.fields:
                self.fields["role"].disabled = True

    profile_form = AuthorProfileForm(instance=request.user)
    pref_form = PreferencesForm(instance=request.user)
    password_form = PasswordUpdateForm(request.user)
    active_tab = "profile"

    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = AuthorProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated")
                return redirect("author_dashboard")
            active_tab = "profile"
        elif "update_prefs" in request.POST:
            pref_form = PreferencesForm(request.POST, instance=request.user)
            if pref_form.is_valid():
                pref_form.save()
                messages.success(request, "Preferences updated")
                return redirect("author_dashboard")
            active_tab = "prefs"
        elif "change_password" in request.POST:
            password_form = PasswordUpdateForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed")
                return redirect("author_dashboard")
            active_tab = "password"

    context = {
        "profile_form": profile_form,
        "pref_form": pref_form,
        "password_form": password_form,
        "posts": posts,
        "year": datetime.now().year,
        "active_tab": active_tab,
    }
    return render(request, "blog/author_dashboard.html", context)


@login_required(login_url="accounts:login")
@user_passes_test(lambda u: u.is_superuser)
def author_management(request):
    """Management panel reserved for superusers."""
    """Admin-only dashboard for managing authors."""
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.AUTHOR
            user.is_staff = True
            user.save()
            return redirect("author_management")
    else:
        form = SignupForm()

    # Handle comment approval/denial
    if request.method == 'POST' and 'approve_comment' in request.POST:
        comment_id = request.POST.get('comment_id')
        action = request.POST.get('approve_comment')
        
        try:
            comment = Comment.objects.get(id=comment_id)
            if action == 'approve':
                comment.status = "approved"
                comment.save()
                messages.success(request, "Comment approved.")
            elif action == 'deny':
                comment.delete()  # Or set comment.status = "denied" if you want to keep records
                messages.success(request, "Comment denied.")
        except Comment.DoesNotExist:
            messages.error(request, "Comment not found.")

    pending_comments = Comment.objects.filter(status="pending").order_by('-created_at')
    authors = User.objects.filter(role=User.Role.AUTHOR)
    context = {"form": form, "authors": authors, "pending_comments": pending_comments}
    return render(request, "blog/author_management.html", context)