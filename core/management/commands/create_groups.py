from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = "Create default user groups"

    def handle(self, *args, **kwargs):
        for group_name in ["reader", "author"]:
            Group.objects.get_or_create(name=group_name)
        self.stdout.write(self.style.SUCCESS("Default groups ensured"))
