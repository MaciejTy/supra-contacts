"""Bulk import of contacts from CSV files."""

import csv
import io

from .forms import ContactForm
from .models import ContactStatus

REQUIRED_COLUMNS = ["first_name", "last_name", "phone_number", "email", "city", "status"]


class CsvImportError(Exception):
    """Raised when the file cannot be processed at all."""


def import_contacts(uploaded_file):
    """Import contacts from an uploaded CSV file.

    Returns (created_count, row_errors). Rows are validated independently, so
    valid contacts are saved even when other rows are rejected.
    """
    try:
        # utf-8-sig strips the byte order mark that Excel writes at file start.
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CsvImportError("Plik musi być zapisany w kodowaniu UTF-8.")

    reader = csv.DictReader(io.StringIO(text))

    missing = [name for name in REQUIRED_COLUMNS if name not in (reader.fieldnames or [])]
    if missing:
        raise CsvImportError(f"W pliku brakuje kolumn: {', '.join(missing)}.")

    created = 0
    errors = []

    # start=2 because line 1 is the header row.
    for line_number, row in enumerate(reader, start=2):
        data = {name: (row.get(name) or "").strip() for name in REQUIRED_COLUMNS}

        # The CSV holds status names; the form expects a primary key.
        status = ContactStatus.objects.filter(name__iexact=data["status"]).first()
        if status is None:
            errors.append(f"Wiersz {line_number}: nieznany status „{data['status']}”.")
            continue
        data["status"] = status.pk

        # Reusing ContactForm keeps validation rules in one place.
        form = ContactForm(data)
        if form.is_valid():
            form.save()
            created += 1
        else:
            details = "; ".join(
                f"{field}: {' '.join(msgs)}" for field, msgs in form.errors.items()
            )
            errors.append(f"Wiersz {line_number}: {details}")

    return created, errors