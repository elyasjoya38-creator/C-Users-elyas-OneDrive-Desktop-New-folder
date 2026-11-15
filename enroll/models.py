from django.conf import settings
from django.db import models


PDC_TYPES = (
    ("Seminar", "Seminar"),
    ("Workshop", "Workshop"),
    ("Course", "Course"),
    ("Tranning", "Training"),
    ("zoomcall", "Zoom Call"),
)
typelist = PDC_TYPES


class pdc_detials(models.Model):
    title = models.CharField(max_length=100)
    producer = models.CharField(max_length=100, null=True, blank=True)
    descript = models.TextField(null=True, blank=True)
    types = models.CharField(max_length=50, choices=PDC_TYPES, null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    startdate = models.DateField(null=True, blank=True)
    enddate = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    urls = models.URLField(max_length=200, null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "PDC record"
        verbose_name_plural = "PDC records"

    def __str__(self):
        return self.title


class Teacher(models.Model):
    full_name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="teacher_profile",
    )

    class Meta:
        ordering = ["full_name", "id"]

    def __str__(self):
        return self.full_name


class Course(models.Model):
    course_name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()

    class Meta:
        ordering = ["course_name", "id"]

    def __str__(self):
        return self.course_name


class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    faculty = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="student_profile",
    )

    class Meta:
        ordering = ["full_name", "id"]

    def __str__(self):
        return self.full_name


class Enrollment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_APPROVED)

    class Meta:
        ordering = ["-enrolled_at", "id"]

    def __str__(self):
        return f"{self.student} - {self.course} ({self.get_status_display()})"


ATTENDANCE_STATUS = (
    ("Present", "Present"),
    ("Absent", "Absent"),
    ("Late", "Late"),
)


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS)

    class Meta:
        ordering = ["-date", "id"]

    def __str__(self):
        return f"{self.student} - {self.status}"


class Certificate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issue_date = models.DateField()
    certificate_no = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["-issue_date", "id"]

    def __str__(self):
        return self.certificate_no
