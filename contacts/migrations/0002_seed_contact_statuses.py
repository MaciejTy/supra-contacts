from django.db import migrations

INITIAL_STATUSES = ["nowy", "w trakcie", "zagubiony", "nieaktualny"]


def create_statuses(apps, schema_editor):
    """Seed the statuses required by the task on a fresh database."""
    ContactStatus = apps.get_model("contacts", "ContactStatus")
    for name in INITIAL_STATUSES:
        ContactStatus.objects.get_or_create(name=name)


def remove_statuses(apps, schema_editor):
    ContactStatus = apps.get_model("contacts", "ContactStatus")
    ContactStatus.objects.filter(name__in=INITIAL_STATUSES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("contacts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_statuses, remove_statuses),
    ]
