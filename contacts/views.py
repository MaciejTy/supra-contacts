from django.shortcuts import render
from django.db.models import Q

from .models import Contact

#Whitelist of allowed sort values. User input is never passed to order_by() directly,
# so an arbitrary query string cannot reach the database layer

SORT_OPTIONS =["last_name", "-last_name", "created_at", "-created_at}"]
DEFAULT_SORT = "last_name"

def contact_list(request):
    """Display all contacts with optional sorting."""

    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", DEFAULT_SORT)

    if sort not in SORT_OPTIONS:
        sort = DEFAULT_SORT

    #select related() fetches the related status in the same SQL query,
    #instead of one extra query per contact when rendering the table.

    contacts = Contact.objects.select_related("status")

    if query:
        contacts = contacts.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone_number__icontains=query)
            | Q(city__icontains=query)
        )
    contacts = contacts.order_by(sort)

    context = {
        "contacts": contacts,
        "query": query,
        "sort": sort,
        #Precomputed targets for the sort links, so the template stays simple.
        "sort_by_name": "-last_name" if sort == "last_name" else "last_name",
        "sort_by_date": "-created_at" if sort == "created_at" else "created_at",
    }
    return render(request, "contacts/contact_list.html", context)


