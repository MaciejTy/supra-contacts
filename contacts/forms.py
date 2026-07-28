from django import forms

from .models import Contact

class ContactForm(forms.ModelForm):
    """Shared form for creating and editing contacts."""

    class Meta:
        model = Contact
        fields = ["first_name", "last_name","phone_number", "email", "city", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #Bootstrap needs different classes for <select> and <input>

        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-select" if name == "status" else "form-control"