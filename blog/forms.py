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
            "tags",
        ]
        widgets = {
            "categories": forms.CheckboxSelectMultiple,
            "tags": forms.CheckboxSelectMultiple,
        }
