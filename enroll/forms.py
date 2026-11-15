from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Attendance, Certificate, Course, Enrollment, PDCRegistration, Student, Teacher, pdc_detials


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()
            field.widget.attrs.setdefault("placeholder", field.label)


class StudentRegistrationForm(UserCreationForm):
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
            with transaction.atomic():
                user.save()
                student = Student.objects.select_for_update().get(student_id=self.cleaned_data["student_id"], user__isnull=True)
                student.user = user
                student.save(update_fields=["user"])
                group, _ = Group.objects.get_or_create(name="Student")
                user.groups.add(group)
        return user


class AddPDCForm(StyledModelForm):
    class Meta:
        model = pdc_detials
        fields = ["title", "producer", "descript", "types", "time", "startdate", "enddate", "location", "urls"]
        widgets = {"descript": forms.Textarea(attrs={"rows": 4}), "time": forms.TimeInput(attrs={"type": "time"}), "startdate": forms.DateInput(attrs={"type": "date"}), "enddate": forms.DateInput(attrs={"type": "date"}), "urls": forms.URLInput(attrs={"placeholder": "https://example.com"})}

    def clean(self):
        cleaned_data = super().clean()
        start, end = cleaned_data.get("startdate"), cleaned_data.get("enddate")
        if start and end and end < start:
            self.add_error("enddate", "End date cannot be earlier than start date.")
        return cleaned_data


addpdcform = AddPDCForm


class StudentForm(StyledModelForm):
    class Meta:
        model = Student
        fields = ["student_id", "full_name", "faculty", "department", "email", "phone"]
        labels = {"student_id": "Student ID", "full_name": "Full name", "faculty": "Faculty", "department": "Department", "email": "Email address", "phone": "Phone number"}
        widgets = {"email": forms.EmailInput(attrs={"autocomplete": "email"}), "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"})}


class TeacherForm(StyledModelForm):
    """Staff creates the teacher's login while creating their profile.

    Editing an existing profile intentionally does not expose account credentials.
    """

    username = forms.CharField(label="Teacher login username", max_length=150)
    password1 = forms.CharField(label="Temporary password", strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm temporary password", strip=False, widget=forms.PasswordInput)

    class Meta:
        model = Teacher
        fields = ["full_name", "specialization", "email", "phone"]
        labels = {"full_name": "Full name", "email": "Email address", "phone": "Phone number"}
        widgets = {"email": forms.EmailInput(attrs={"autocomplete": "email"}), "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.creating_profile = self.instance.pk is None
        if self.creating_profile:
            User = get_user_model()
            self.fields["username"].max_length = User._meta.get_field(User.USERNAME_FIELD).max_length
            self.fields["username"].widget.attrs["autocomplete"] = "username"
            self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
            self.fields["password2"].widget.attrs["autocomplete"] = "new-password"
            self.fields["password1"].help_text = "Give this temporary password to the teacher securely; they should change it after signing in."
        else:
            self.fields.pop("username")
            self.fields.pop("password1")
            self.fields.pop("password2")

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not self.creating_profile:
            return username
        User = get_user_model()
        lookup = {f"{User.USERNAME_FIELD}__iexact": username}
        if User.objects.filter(**lookup).exists():
            raise ValidationError("This username is already in use. Choose another one.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        if self.creating_profile:
            password1 = cleaned_data.get("password1")
            password2 = cleaned_data.get("password2")
            if password1 and password2 and password1 != password2:
                self.add_error("password2", "The passwords do not match.")
            if password1:
                User = get_user_model()
                user = User(**{User.USERNAME_FIELD: cleaned_data.get("username", "")})
                try:
                    validate_password(password1, user=user)
                except ValidationError as error:
                    self.add_error("password1", error)
        return cleaned_data

    def save(self, commit=True):
        teacher = super().save(commit=False)
        if not commit:
            return teacher
        if not self.creating_profile:
            teacher.save()
            self.save_m2m()
            return teacher

        User = get_user_model()
        username = self.cleaned_data["username"]
        credentials = {User.USERNAME_FIELD: username, "password": self.cleaned_data["password1"]}
        if any(field.name == "email" for field in User._meta.get_fields()):
            credentials["email"] = self.cleaned_data["email"]
        with transaction.atomic():
            user = User.objects.create_user(**credentials)
            user.is_staff = False
            user.is_superuser = False
            user.save(update_fields=["is_staff", "is_superuser"])
            group, _ = Group.objects.get_or_create(name="Teacher")
            user.groups.add(group)
            teacher.user = user
            teacher.save()
        return teacher


class CourseForm(StyledModelForm):
    class Meta:
        model = Course
        fields = ["course_name", "teacher", "start_date", "end_date", "description"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}), "end_date": forms.DateInput(attrs={"type": "date"}), "description": forms.Textarea(attrs={"rows": 4})}

    def clean(self):
        cleaned_data = super().clean()
        start, end = cleaned_data.get("start_date"), cleaned_data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date cannot be earlier than start date.")
        return cleaned_data


class EnrollmentForm(StyledModelForm):
    class Meta:
        model = Enrollment
        fields = ["student", "course"]

    def clean(self):
        cleaned_data = super().clean()
        student, course = cleaned_data.get("student"), cleaned_data.get("course")
        if student and course:
            existing = Enrollment.objects.filter(student=student, course=course)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("This student already has an enrollment record for this course.")
        return cleaned_data


class AttendanceForm(StyledModelForm):
    class Meta:
        model = Attendance
        fields = ["student", "course", "date", "status"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher
        if teacher is not None:
            teacher_courses = Course.objects.filter(teacher__user=teacher)
            self.fields["course"].queryset = teacher_courses
            self.fields["student"].queryset = Student.objects.filter(enrollments__course__in=teacher_courses, enrollments__status=Enrollment.STATUS_APPROVED).distinct()

    def clean(self):
        cleaned_data = super().clean()
        student, course = cleaned_data.get("student"), cleaned_data.get("course")
        if student and course and self.teacher:
            if not Course.objects.filter(pk=course.pk, teacher__user=self.teacher).exists():
                self.add_error("course", "You can only manage attendance for your assigned courses.")
            if not Enrollment.objects.filter(student=student, course=course, status=Enrollment.STATUS_APPROVED).exists():
                self.add_error("student", "Attendance can only be recorded for an approved student in this course.")
        return cleaned_data


class PDCRegistrationForm(forms.ModelForm):
    class Meta:
        model = PDCRegistration
        fields = []


class CertificateForm(StyledModelForm):
    class Meta:
        model = Certificate
        fields = ["student", "course", "issue_date", "certificate_no"]
        widgets = {"issue_date": forms.DateInput(attrs={"type": "date"})}
