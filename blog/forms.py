from django import forms
from .models import ContactMessage, Post


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message", "agree"]
        widgets = {
            "subject": forms.Select(choices=ContactMessage.SUBJECT_CHOICES),
        }
        labels = {
            "agree": "I agree to the Privacy Policy and Terms of Service",
        }


class PostForm(forms.ModelForm):
    """Form for creating blog posts."""

    tags_input = forms.CharField(
        required=False,
        label="Tags",
        help_text="Comma separated",
    )

    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            "excerpt",
            "content",
            "featured_image_url",
            "status",
            "categories",
        ]
        widgets = {
            "categories": forms.SelectMultiple,
        }

