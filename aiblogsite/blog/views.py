from django.shortcuts import render


def home(request):
    """Render landing page with current year."""
    from datetime import datetime

    context = {"year": datetime.now().year}
    return render(request, "blog/landing.html", context)


def blog_home(request):
    """Render the blog index page."""
    from datetime import datetime

    context = {"year": datetime.now().year}
    return render(request, "blog/blog_home.html", context)
