from django import forms
from .models import ContactMessage


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
