"""Tests for CSV import."""

import io

import pytest

from contacts.importers import import_contacts
from contacts.models import Contact, ContactStatus

HEADER = "first_name,last_name,phone_number,email,city,status\n"


def make_file(content):
    return io.BytesIO(content.encode("utf-8"))


@pytest.fixture
def status(db):
    # The status is already created by the seed migration, so fetch it
    # instead of creating a duplicate.
    return ContactStatus.objects.get(name="nowy")


def test_import_creates_contacts(status):
    csv_file = make_file(
        HEADER + "Jan,Kowalski,501100200,jan@example.com,Wrocław,nowy\n"
    )

    created, errors = import_contacts(csv_file)

    assert created == 1
    assert errors == []
    assert Contact.objects.get(email="jan@example.com").city == "Wrocław"


def test_invalid_row_does_not_block_valid_ones(status):
    """One bad row should not discard the rest of the file."""
    csv_file = make_file(
        HEADER
        + "Jan,Kowalski,501100200,jan@example.com,Wrocław,nowy\n"
        + "Ewa,Nowak,501100201,ewa@example.com,Lublin,UNKNOWN\n"
    )

    created, errors = import_contacts(csv_file)

    assert created == 1
    assert len(errors) == 1
    assert "2" not in errors[0]  # the error is reported for line 3, not line 2


def test_duplicate_email_is_rejected(status):
    """Uniqueness is enforced on import, not just in the web form."""
    row = "Jan,Kowalski,501100200,jan@example.com,Wrocław,nowy\n"
    import_contacts(make_file(HEADER + row))

    created, errors = import_contacts(make_file(HEADER + row))

    assert created == 0
    assert len(errors) == 1
