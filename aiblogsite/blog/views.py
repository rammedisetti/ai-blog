from django.shortcuts import render
from .forms import ContactForm


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
