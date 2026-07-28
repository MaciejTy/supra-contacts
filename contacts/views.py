from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages

from .models import Contact
from .forms import ContactForm

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

def contact_create(request):
    """Handle the new contact form: render it on GET, save it on POST."""
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Kontakt został dodany")
            return redirect("contact_list")
    else:
        form = ContactForm()

    return render(request, "contacts/contact_form.html", {
        "form": form,
        "heading": "Nowy kontakt",
    })
def contact_update(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
    #instance=contact tells the form to update this row instead of creating one.
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Kontakt został zakutalizowany.")
            return redirect("contact_list")
    else:
        form = ContactForm(instance=contact)
    return render(request, "contacts/contact_form.html", {
        "form": form,
        "heading": "Edycja kontaktu",
    })

def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)

    #Deleting only on POST - a GET request must never change data.
    if request.method == "POST":
        contact.delete()
        messages.success(request, "Kontakt został usunięty")
        return redirect("contact_list")
    return render(request, "contacts/contact_confirm_delete.html", {
        "contact": contact,
    })
