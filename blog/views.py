from django.shortcuts import render
from .forms import ContactForm, PostForm
from .models import Post, Category, Tag


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


def add_post(request):
    """Create a new blog post."""
    from datetime import datetime
    from django.contrib.auth import get_user_model
    from django.utils import timezone

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            if request.user.is_authenticated:
                post.author = request.user
            else:
                User = get_user_model()
                post.author = User.objects.first()
            if post.status == "published" and not post.published_at:
                post.published_at = timezone.now()
            post.save()
            form.save_m2m()
            if request.htmx:
                return render(
                    request,
                    "blog/add_post_success.html",
                    {"post": post},
                )
            context = {"year": datetime.now().year}
            return redirect("blog_home")
    else:
        form = PostForm()

    context = {"form": form, "year": datetime.now().year}
    if request.htmx:
        return render(request, "blog/_post_form.html", context)
    return render(request, "blog/add_post.html", context)
