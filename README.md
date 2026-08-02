# Contact Manager

A Django application for managing contacts, with live weather for each contact's city
and a REST API.

Contacts can be searched, sorted, paginated, created, edited, deleted, imported from
CSV and exported back to it. Weather comes from two external APIs and is cached on two
levels, so the list stays fast no matter how many contacts it holds.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 6.0 |
| API | Django REST Framework |
| Frontend | Bootstrap 5, vanilla JavaScript |
| Database | SQLite |
| Cache | Redis under Docker, in-process cache otherwise |
| Tests | pytest, pytest-django |
| External APIs | OpenStreetMap Nominatim, Open-Meteo |

## Running with Docker

The fastest way to get everything up, including Redis:

```bash
git clone https://github.com/MaciejTy/supra-contacts.git
cd supra-contacts
docker compose up --build
```

The app runs at http://localhost:8000. Migrations run automatically on startup.

To create an admin account:

```bash
docker compose exec web python manage.py createsuperuser
```

## Running locally

Requires Python 3.10 or newer. Redis is not needed — without it the app falls back to
an in-process cache.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

`migrate` creates the database and seeds four contact statuses (`nowy`, `w trakcie`,
`zagubiony`, `nieaktualny`) through a data migration, so the app is usable immediately
with no manual setup.

## Tests

```bash
python -m pytest
```

Twenty tests covering the parts with the most edge cases: the weather service (external
calls are mocked, so tests don't depend on the network), the CSV importer, and the
validation rules. They assert behaviour rather than output — the cache test checks that
a second lookup makes no HTTP call at all, not just that it returns the right value, and
the validation tests go through the REST API and a CSV upload rather than the browser
form, since those are the paths that bypass the client-side rules.

## Features

### Contacts

Search runs across first name, last name, email, phone number and city. Sorting works
on last name or creation date in both directions; clicking a column header toggles the
order. The list is paginated at 20 rows per page, and search and sort survive page
changes.

### Statuses

Status is a `ForeignKey` to a separate `ContactStatus` model rather than a text field
or `TextChoices`. New statuses can be added from the admin panel without touching code
or writing a migration. The relation uses `on_delete=PROTECT`, so a status still in use
cannot be deleted out from under existing contacts.

### Weather

Each row shows current temperature, humidity and wind speed for that contact's city.
The lookup runs in two stages: Nominatim resolves a city name to coordinates, then
Open-Meteo returns the weather for those coordinates.

Weather loads asynchronously after the page renders, so the contact list appears
immediately regardless of how slow the external APIs are.

### CSV import and export

Import lives at `/import/` and expects a header row with these columns:

```
first_name,last_name,phone_number,email,city,status
```

UTF-8 encoding, statuses matched by name against existing records. See
[`sample_contacts.csv`](sample_contacts.csv) for a working example — its last row has a
deliberately invalid status to demonstrate per-row error reporting.

Rows are validated independently, so valid contacts are saved even when others fail.
Every rejected row is reported with its line number and the reason.

Export produces the same column layout, which means an exported file can be imported
straight back.

### Validation

Two levels, with different jobs:

- **Client side** (vanilla JS) — email format, phone format and length, minimum length
  on the remaining fields. Errors appear when a field loses focus and clear as the
  value is corrected. Phone numbers accept spaces, dashes and an optional `+48` prefix,
  since rejecting `+48 501 234 567` would be hostile for no good reason.
- **Server side** — the same rules again, as model field validators: a phone format
  regex accepting the same spellings the browser does, a minimum length on the name and
  city fields, and `unique=True` on `phone_number` and `email`. Because they live on the
  model rather than on the form, they apply identically to the web form, the CSV import
  and the REST API.

Client-side validation is a convenience, not a safeguard: JavaScript can be disabled or
bypassed entirely, which is why nothing depends on it.

## REST API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/contacts/` | List contacts |
| POST | `/api/contacts/` | Create a contact |
| GET | `/api/contacts/{id}/` | Retrieve a contact |
| PUT | `/api/contacts/{id}/` | Update a contact |
| PATCH | `/api/contacts/{id}/` | Partially update a contact |
| DELETE | `/api/contacts/{id}/` | Delete a contact |
| GET | `/api/weather/?city={city}` | Current weather for a city |

The browsable DRF interface is at http://localhost:8000/api/.

The list endpoint returns `id`, `first_name`, `last_name`, `city`, `status` and
`created_at`. Write operations additionally require `phone_number` and `email`.
Statuses are referenced by name rather than primary key, so the API stays readable and
doesn't leak database ids:

```bash
curl -X POST http://localhost:8000/api/contacts/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Anna",
    "last_name": "Kowalska",
    "phone_number": "501234567",
    "email": "anna.kowalska@example.com",
    "city": "Gdańsk",
    "status": "nowy"
  }'
```

## Design notes

### Keeping external API traffic low

The naive implementation would call both APIs once per contact on every page load —
100 requests for 50 contacts. Nominatim permits one request per second, so that would
make the page unusable and risk getting the IP blocked.

Three things keep the traffic down:

1. **Server-side cache keyed by city**, not by contact. A hundred contacts living in
   five cities cost five API calls, not a hundred. Coordinates are cached for 30 days
   since cities don't move; weather for 30 minutes. Cities that cannot be resolved at
   all are cached too, for an hour — otherwise a single typo in a contact's city would
   cost one Nominatim request on every page load. The TTL is short so that an API
   outage doesn't blacklist a real city for a month.
2. **Client-side deduplication** — the JavaScript collects unique cities from the table
   and issues one request per city regardless of row count.
3. **Pagination** — only the cities visible on the current page are ever requested.

City names are normalised before use as a cache key, so `Warszawa`, `warszawa` and
` Warszawa ` all resolve to one entry.

### Failing gracefully

The weather functions return `None` instead of raising. An unreachable API, a typo in a
city name or a timeout produces a dash in the weather column while everything else
keeps working. Weather is a secondary feature and shouldn't be able to take down the
contact list.

Cache access is wrapped the same way. The cache is an optimisation, so an unreachable
Redis degrades the lookup to an uncached one rather than turning it into a 500.

### API quirks worth documenting

Open-Meteo's `current_weather=true` parameter does not include humidity, so the fields
are requested explicitly via
`current=temperature_2m,relative_humidity_2m,wind_speed_10m`.

Nominatim's usage policy requires a descriptive `User-Agent` identifying the
application; requests without one may be rejected.

### Structure

External API integration lives in `services.py` and CSV import in `importers.py`, both
outside the view layer. Views handle HTTP and nothing else. This keeps both testable
without running a server, and lets the weather service be shared between the HTML view
and the REST API.

The CSV importer reuses the same `ContactForm` as the web form, so validation rules
exist in exactly one place. Sort parameters are checked against a whitelist before
reaching `order_by()`, since they come from the query string.

## Layout

```
supra-contacts/
├── config/                  # Project settings and root URL config
├── contacts/
│   ├── migrations/          # Schema migrations plus the status seed
│   ├── templates/contacts/  # HTML templates
│   ├── templatetags/        # Query-string helper for pagination links
│   ├── tests/               # pytest suite
│   ├── models.py            # Contact, ContactStatus
│   ├── views.py             # HTML views and REST API
│   ├── forms.py             # Contact and import forms
│   ├── serializers.py       # DRF serializers
│   ├── services.py          # Nominatim and Open-Meteo integration
│   ├── importers.py         # CSV import
│   └── urls.py              # App URL config
├── docker-compose.yml
├── Dockerfile
├── sample_contacts.csv      # Example import file
├── requirements.txt
└── manage.py
```

## Notes

This runs in a development configuration: `DEBUG = True`, `SECRET_KEY` in the settings
file, SQLite, and Django's development server. A production deployment would move the
key and debug flag to environment variables, switch to PostgreSQL, run behind gunicorn,
and populate `ALLOWED_HOSTS`.

The REST API is currently unauthenticated.