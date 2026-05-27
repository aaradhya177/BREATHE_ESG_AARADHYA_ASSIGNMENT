from django.core.management.base import BaseCommand
from django.utils.text import slugify

from emissions.models import Client


class Command(BaseCommand):
    help = 'Create the default "Acme Corp" client.'

    def handle(self, *args, **options):
        client, created = Client.objects.get_or_create(
            slug=slugify("Acme Corp"),
            defaults={"name": "Acme Corp"},
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created client: {client.name}"))
            return

        self.stdout.write(self.style.WARNING(f"Client already exists: {client.name}"))
