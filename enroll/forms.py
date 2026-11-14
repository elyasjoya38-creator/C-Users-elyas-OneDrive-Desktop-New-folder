from django import forms
from django.core.exceptions import ValidationError

from .models import (
    Attendance,
    Certificate,
    Course,
    Enrollment,
    Student,
    Teacher,
    pdc_detials,
)


class StyledModelForm(forms.ModelForm):
    """Apply the shared form-control style to every model form field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()
            field.widget.attrs.setdefault("placeholder", field.label)


class AddPDCForm(StyledModelForm):
    class Meta:
        model = pdc_detials
        fields = [
            "title", "producer", "descript", "types", "time",
            "startdate", "enddate", "location", "urls",
        ]
        widgets = {
            "descript": forms.Textarea(attrs={"rows": 4}),
            "time": forms.TimeInput(attrs={"type": "time"}),
            "startdate": forms.DateInput(attrs={"type": "date"}),
            "enddate": forms.DateInput(attrs={"type": "date"}),
            "urls": forms.URLInput(attrs={"placeholder": "https://example.com"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("startdate")
        end = cleaned_data.get("enddate")
        if start and end and end < start:
            self.add_error("enddate", "End date cannot be earlier than start date.")
        return cleaned_data


# Keep the original lowercase name available for existing imports.
addpdcform = AddPDCForm


class StudentForm(StyledModelForm):
    class Meta:
        model = Student
        fields = ["student_id", "full_name", "faculty", "department", "email", "phone"]
        labels = {
            "student_id": "Student ID",
            "full_name": "Full name",
            "faculty": "Faculty",
            "department": "Department",
            "email": "Email address",
            "phone": "Phone number",
        }
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
        }


class TeacherForm(StyledModelForm):
    class Meta:
        model = Teacher
        fields = ["full_name", "specialization", "email", "phone"]
        labels = {
            "full_name": "Full name",
            "specialization": "Specialization",
            "email": "Email address",
            "phone": "Phone number",
        }
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
        }


class CourseForm(StyledModelForm):
    class Meta:
        model = Course
        fields = ["course_name", "teacher", "start_date", "end_date", "description"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date cannot be earlier than start date.")
        return cleaned_data


class EnrollmentForm(StyledModelForm):
    class Meta:
        model = Enrollment
        fields = ["student", "course"]

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        course = cleaned_data.get("course")
        if student and course:
            existing = Enrollment.objects.filter(student=student, course=course)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("This student is already enrolled in this course.")
        return cleaned_data


class AttendanceForm(StyledModelForm):
    class Meta:
        model = Attendance
        fields = ["student", "course", "date", "status"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class CertificateForm(StyledModelForm):
    class Meta:
        model = Certificate
        fields = ["student", "course", "issue_date", "certificate_no"]
        widgets = {"issue_date": forms.DateInput(attrs={"type": "date"})}
