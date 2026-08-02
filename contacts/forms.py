from django import forms

from .models import Contact


class ContactForm(forms.ModelForm):
    """Shared form for creating and editing contacts."""

    class Meta:
        model = Contact
        fields = ["first_name", "last_name", "phone_number", "email", "city", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap needs different classes for <select> and <input>

        for name, field in self.fields.items():
            field.widget.attrs["class"] = (
                "form-select" if name == "status" else "form-control"
            )


class ContactImportForm(forms.Form):
    """Upload form for bulk contact import."""

    csv_file = forms.FileField(
        label="Plik CSV",
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": ".csv"}
        ),
    )

    def clean_csv_file(self):
        uploaded = self.cleaned_data["csv_file"]
        if not uploaded.name.lower().endswith(".csv"):
            raise forms.ValidationError("Wybierz plik z rozszerzeniem .csv.")
        if uploaded.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Plik nie może być większy niż 2 MB.")
        return uploaded
