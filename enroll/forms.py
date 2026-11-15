from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
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


class StudentRegistrationForm(UserCreationForm):
    """Create a standard student account linked to a pre-created student record."""

    student_id = forms.CharField(max_length=20, label="Student ID")

    class Meta(UserCreationForm.Meta):
        fields = ("username", "student_id")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["student_id"].widget.attrs["autocomplete"] = "off"

    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"].strip()
        if not Student.objects.filter(student_id=student_id, user__isnull=True).exists():
            raise ValidationError("Student ID was not found or is already linked to an account. Contact the PDC office.")
        return student_id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        if commit:
            from django.db import transaction
            from django.contrib.auth.models import Group

            with transaction.atomic():
                user.save()
                student = Student.objects.select_for_update().get(
                    student_id=self.cleaned_data["student_id"], user__isnull=True
                )
                student.user = user
                student.save(update_fields=["user"])
                group, _ = Group.objects.get_or_create(name="Student")
                user.groups.add(group)
        return user


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
        fields = ["full_name", "specialization", "email", "phone", "user"]
        labels = {"full_name": "Full name", "email": "Email address", "phone": "Phone number", "user": "Teacher login account (optional)"}
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields["user"].queryset = User.objects.filter(is_staff=False, is_superuser=False).order_by("username")
        self.fields["user"].required = False
        self.fields["user"].help_text = "Select a non-staff account created for this teacher, or leave blank."


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
                raise ValidationError("This student already has an enrollment for this course.")
        return cleaned_data


class AttendanceForm(StyledModelForm):
    class Meta:
        model = Attendance
        fields = ["student", "course", "date", "status"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher is not None:
            teacher_courses = Course.objects.filter(teacher__user=teacher)
            self.fields["course"].queryset = teacher_courses
            self.fields["student"].queryset = Student.objects.filter(
                enrollments__course__in=teacher_courses,
                enrollments__status=Enrollment.STATUS_APPROVED,
            ).distinct()


class CertificateForm(StyledModelForm):
    class Meta:
        model = Certificate
        fields = ["student", "course", "issue_date", "certificate_no"]
        widgets = {"issue_date": forms.DateInput(attrs={"type": "date"})}
