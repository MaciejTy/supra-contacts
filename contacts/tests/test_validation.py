"""Tests that the validation rules hold without the client-side JavaScript.

The browser rules are a convenience and can be bypassed - by disabling
JavaScript, by posting to the REST API, or by importing a CSV file. These tests
go through all three paths.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from contacts.models import Contact, ContactStatus


@pytest.fixture
def status(db):
    return ContactStatus.objects.get(name="nowy")


def payload(**overrides):
    data = {
        "first_name": "Anna",
        "last_name": "Kowalska",
        "phone_number": "501234567",
        "email": "anna@example.com",
        "city": "Gdańsk",
        "status": "nowy",
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize(
    "overrides,expected",
    [
        ({}, 201),
        # The formats the browser accepts must keep working server-side.
        ({"phone_number": "+48 501 234 567"}, 201),
        ({"phone_number": "501-234-567"}, 201),
        ({"phone_number": "abc-not-a-phone"}, 400),
        ({"phone_number": "1"}, 400),
        ({"phone_number": "5012345678901"}, 400),
        ({"first_name": "A"}, 400),
        ({"last_name": "B"}, 400),
        ({"city": "X"}, 400),
    ],
)
def test_api_enforces_the_same_rules_as_the_browser(
    client, status, overrides, expected
):
    response = client.post(
        "/api/contacts/", payload(**overrides), content_type="application/json"
    )
    assert response.status_code == expected, response.content


def test_web_form_rejects_a_malformed_phone_number(client, status):
    response = client.post(
        reverse("contact_create"),
        {**payload(), "status": status.pk, "phone_number": "nie-telefon"},
    )

    assert response.status_code == 200  # re-rendered with errors, not saved
    assert Contact.objects.count() == 0


def test_csv_import_rejects_a_malformed_phone_number(client, db):
    csv_file = (
        "first_name,last_name,phone_number,email,city,status\n"
        "Jan,Kowalski,501100200,jan@example.com,Wrocław,nowy\n"
        "Zła,Osoba,nie-telefon,zla@example.com,Poznań,nowy\n"
    ).encode()

    response = client.post(
        reverse("contact_import"),
        {"csv_file": SimpleUploadedFile("contacts.csv", csv_file, "text/csv")},
        follow=True,
    )

    assert Contact.objects.count() == 1, "the valid row is still imported"
    assert any("phone_number" in str(m) for m in response.context["messages"])


def test_weather_endpoint_rejects_an_oversized_city(client, db):
    """The endpoint is public: every distinct value costs an outbound request."""
    assert client.get("/api/weather/?city=" + "a" * 200).status_code == 400
