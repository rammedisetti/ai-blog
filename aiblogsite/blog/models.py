from django.db import models


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ("Support", "Support"),
        ("Feedback", "Feedback"),
        ("Business Inquiry", "Business Inquiry"),
        ("Other", "Other"),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    agree = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
