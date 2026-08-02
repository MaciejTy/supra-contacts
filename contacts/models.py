from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models

# Mirrors the client-side rule: an optional +48 prefix followed by nine digits,
# with spaces and dashes allowed as separators. Client-side validation can be
# disabled or bypassed, so the same rule has to exist on the model - that way it
# applies to the web form, the CSV import and the REST API alike.
phone_validator = RegexValidator(
    regex=r"^(\+?48[\s-]?)?(\d[\s-]?){8}\d$",
    message="Numer telefonu musi mieć 9 cyfr, opcjonalnie z prefiksem +48.",
)


class ContactStatus(models.Model):
    """Lookup table for contact statuses."""

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "contact statuses"

    def __str__(self):
        return self.name


class Contact(models.Model):
    first_name = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    last_name = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    phone_number = models.CharField(
        max_length=20, unique=True, validators=[phone_validator]
    )
    email = models.EmailField(unique=True)
    city = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    status = models.ForeignKey(
        ContactStatus,
        on_delete=models.PROTECT,
        related_name="contacts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
