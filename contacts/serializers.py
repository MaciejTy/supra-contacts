from rest_framework import serializers

from .models import Contact, ContactStatus


class ContactListSerializer(serializers.ModelSerializer):
    """Representation for GET /api/contacts/.

    The task specifies this exact set of fields for the list endpoint, so phone
    number and email are deliberately left out.
    """

    status = serializers.StringRelatedField()

    class Meta:
        model = Contact
        fields = ["id", "first_name", "last_name", "city", "status", "created_at"]


class ContactSerializer(serializers.ModelSerializer):
    """Full representation used for create, update and detail responses."""

    # Statuses are exposed by name ("nowy") rather than by primary key, so the
    # API stays readable and does not leak database ids.
    status = serializers.SlugRelatedField(
        slug_field="name",
        queryset=ContactStatus.objects.all(),
    )

    class Meta:
        model = Contact
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "city",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]