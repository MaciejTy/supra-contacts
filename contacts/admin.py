from django.contrib import admin

from .models import Contact, ContactStatus


@admin.register(ContactStatus)
class ContactStatusAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        "last_name",
        "first_name",
        "phone_number",
        "email",
        "city",
        "status",
        "created_at",
    ]
    list_filter = ["status", "city"]
    search_fields = ["last_name", "first_name", "email", "phone_number", "city"]