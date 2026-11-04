from django import forms
from .models import pdc_detials

class addpdcform(forms.ModelForm):
    class Meta:
        model = pdc_detials
        fields = ["title", "producer", "descript", "types", "time", "startdate", "enddate", "location", "urls"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Enter PDC title"}),
            "producer": forms.TextInput(attrs={"placeholder": "Producer / facilitator"}),
            "descript": forms.Textarea(attrs={"rows": 4, "placeholder": "Description"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
            "startdate": forms.DateInput(attrs={"type": "date"}),
            "enddate": forms.DateInput(attrs={"type": "date"}),
            "location": forms.TextInput(attrs={"placeholder": "Location"}),
            "urls": forms.URLInput(attrs={"placeholder": "https://example.com"}),
        }
    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("startdate"), cleaned.get("enddate")
        if start and end and end < start:
            self.add_error("enddate", "End date cannot be earlier than start date.")
        return cleaned
