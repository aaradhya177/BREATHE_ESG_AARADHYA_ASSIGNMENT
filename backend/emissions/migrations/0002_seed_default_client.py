from django.db import migrations


def create_default_client(apps, schema_editor):
    Client = apps.get_model("emissions", "Client")
    Client.objects.get_or_create(
        slug="acme-corp",
        defaults={"name": "Acme Corp"},
    )


def remove_default_client(apps, schema_editor):
    Client = apps.get_model("emissions", "Client")
    Client.objects.filter(slug="acme-corp").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("emissions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_client, remove_default_client),
    ]
