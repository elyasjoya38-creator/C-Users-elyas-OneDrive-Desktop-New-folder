from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    AddPDCForm,
    AttendanceForm,
    CertificateForm,
    CourseForm,
    EnrollmentForm,
    StudentForm,
    StudentRegistrationForm,
    TeacherForm,
)
from .models import Attendance, Certificate, Course, Enrollment, Student, Teacher, pdc_detials


def is_pdc_admin(user):
    """Only staff and superusers may manage institutional records."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def is_admin(user):
    """Backward-compatible alias for the institutional admin check."""
    return is_pdc_admin(user)


admin_required = user_passes_test(is_pdc_admin, login_url="user_dashboard")


def is_teacher(user):
    return user.is_authenticated and user.groups.filter(name="Teacher").exists()


def is_student(user):
    return user.is_authenticated and user.groups.filter(name="Student").exists()


@login_required
def home(request):
    if not is_pdc_admin(request.user):
        return redirect("user_dashboard")
    today = timezone.localdate()
    records = pdc_detials.objects.all()
    return render(request, "enroll/index.html", {
        "active_page": "home",
        "total_pdcs": records.count(),
        "seminar_count": records.filter(types="Seminar").count(),
        "workshop_count": records.filter(types="Workshop").count(),
        "upcoming_pdcs": records.filter(startdate__gte=today).count(),
        "recent_pdcs": records[:5],
        "total_students": Student.objects.count(),
        "total_teachers": Teacher.objects.count(),
        "total_courses": Course.objects.count(),
        "total_enrollments": Enrollment.objects.count(),
        "total_attendance": Attendance.objects.count(),
        "total_certificates": Certificate.objects.count(),
    })


@login_required
def user_dashboard(request):
    if is_pdc_admin(request.user):
        return redirect("home")
    context = {"active_page": "user_dashboard", "is_student": is_student(request.user), "is_teacher": is_teacher(request.user)}
    student = Student.objects.filter(user=request.user).first()
    teacher = Teacher.objects.filter(user=request.user).first()
    context.update({"student_profile": student, "teacher_profile": teacher})
    if student and is_student(request.user):
        enrollments = student.enrollments.select_related("course", "course__teacher")
        context.update({
            "enrollments": enrollments,
            "available_courses": Course.objects.exclude(enrollments__student=student).filter(end_date__gte=timezone.localdate()),
        })
    if teacher and is_teacher(request.user):
        context["teacher_courses"] = Course.objects.filter(teacher=teacher).select_related("teacher")
    return render(request, "enroll/user_dashboard.html", context)


@login_required
@require_POST
def student_enroll(request, course_id):
    if not is_student(request.user):
        return redirect("user_dashboard")
    student = Student.objects.filter(user=request.user).first()
    if student is None:
        messages.error(request, "Your account is not linked to a student record. Contact the PDC office.")
        return redirect("user_dashboard")
    course = get_object_or_404(Course, pk=course_id)
    if course.end_date < timezone.localdate():
        messages.error(request, "Registration for this course has ended.")
        return redirect("user_dashboard")
    enrollment, created = Enrollment.objects.get_or_create(
        student=student, course=course, defaults={"status": Enrollment.STATUS_PENDING}
    )
    if created:
        messages.success(request, "Your enrollment request was submitted for review.")
    elif enrollment.status == Enrollment.STATUS_REJECTED:
        enrollment.status = Enrollment.STATUS_PENDING
        enrollment.enrolled_at = timezone.localdate()
        enrollment.save(update_fields=["status", "enrolled_at"])
        messages.success(request, "Your enrollment request was submitted again for review.")
    else:
        messages.info(request, "You already have an enrollment request for this course.")
    return redirect("user_dashboard")


@admin_required
def pdcadd(request):
    form = AddPDCForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "PDC successfully added.")
        return redirect("managepdc")
    if request.method == "POST":
        messages.error(request, "Please correct the errors below.")
    return render(request, "enroll/addpdc.html", {"form": form, "active_page": "addpdc"})


@admin_required
def managepdc(request):
    records = pdc_detials.objects.all()
    return render(request, "enroll/managepdc.html", {"data": records, "records": records, "active_page": "managepdc"})


@admin_required
def updatepdc(request, id):
    record = get_object_or_404(pdc_detials, pk=id)
    form = AddPDCForm(request.POST or None, instance=record)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "PDC successfully updated.")
        return redirect("managepdc")
    if request.method == "POST":
        messages.error(request, "Please correct the errors below.")
    return render(request, "enroll/updatepdc.html", {"form": form, "data": record, "active_page": "managepdc"})


@admin_required
@require_POST
def deletes(request, id):
    get_object_or_404(pdc_detials, pk=id).delete()
    messages.success(request, "PDC successfully deleted.")
    return redirect("managepdc")


@admin_required
def review_enrollment(request, id):
    enrollment = get_object_or_404(Enrollment, pk=id)
    status = request.POST.get("status")
    if request.method == "POST" and status in (Enrollment.STATUS_APPROVED, Enrollment.STATUS_REJECTED):
        enrollment.status = status
        enrollment.save(update_fields=["status"])
        messages.success(request, f"Enrollment request {enrollment.get_status_display().lower()}.")
    else:
        messages.error(request, "Invalid enrollment review request.")
    return redirect("enrollment_list")


def user_register(request):
    if request.user.is_authenticated:
        return redirect("home" if is_pdc_admin(request.user) else "user_dashboard")
    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
        except Student.DoesNotExist:
            form.add_error("student_id", "This student record was just linked to another account. Contact the PDC office.")
        else:
            messages.success(request, "Student account created. Please sign in.")
            return redirect("login")
    return render(request, "enroll/register.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home" if is_pdc_admin(request.user) else "user_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect("home" if is_pdc_admin(user) else "user_dashboard")
        messages.error(request, "Username or password is incorrect.")
    return render(request, "enroll/login.html")


@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


@admin_required
def student_list(request):
    search = request.GET.get("search", "").strip()
    students = Student.objects.all()
    if search:
        students = students.filter(Q(full_name__icontains=search) | Q(student_id__icontains=search) | Q(email__icontains=search) | Q(department__icontains=search) | Q(faculty__icontains=search))
    return render(request, "enroll/student_list.html", {"students": students, "search": search, "active_page": "students"})


@admin_required
def add_student(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student added successfully. Share the student ID with them to create their portal account.")
        return redirect("student_list")
    return render(request, "enroll/add_student.html", {"form": form, "active_page": "students"})


@admin_required
def edit_student(request, id):
    student = get_object_or_404(Student, pk=id)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student updated successfully.")
        return redirect("student_list")
    return render(request, "enroll/edit_student.html", {"form": form, "student": student, "active_page": "students"})


@admin_required
def delete_student(request, id):
    student = get_object_or_404(Student, pk=id)
    if request.method == "POST":
        student.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect("student_list")
    return render(request, "enroll/delete_student.html", {"student": student, "active_page": "students"})


@admin_required
def student_detail(request, id):
    student = get_object_or_404(Student, pk=id)
    return render(request, "enroll/student_detail.html", {"student": student, "active_page": "students"})


@admin_required
def teacher_list(request):
    search = request.GET.get("search", "").strip()
    teachers = Teacher.objects.select_related("user")
    if search:
        teachers = teachers.filter(Q(full_name__icontains=search) | Q(specialization__icontains=search) | Q(email__icontains=search))
    return render(request, "enroll/teacher_list.html", {"teachers": teachers, "search": search, "active_page": "teachers"})


@admin_required
def add_teacher(request):
    form = TeacherForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Teacher added successfully.")
        return redirect("teacher_list")
    return render(request, "enroll/add_teacher.html", {"form": form, "active_page": "teachers"})


@admin_required
def edit_teacher(request, id):
    teacher = get_object_or_404(Teacher, pk=id)
    form = TeacherForm(request.POST or None, instance=teacher)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Teacher updated successfully.")
        return redirect("teacher_list")
    return render(request, "enroll/edit_teacher.html", {"form": form, "teacher": teacher, "active_page": "teachers"})


@admin_required
def delete_teacher(request, id):
    teacher = get_object_or_404(Teacher, pk=id)
    if request.method == "POST":
        teacher.delete()
        messages.success(request, "Teacher deleted successfully.")
        return redirect("teacher_list")
    return render(request, "enroll/delete_teacher.html", {"teacher": teacher, "active_page": "teachers"})


@admin_required
def teacher_detail(request, id):
    teacher = get_object_or_404(Teacher, pk=id)
    return render(request, "enroll/teacher_detail.html", {"teacher": teacher, "active_page": "teachers"})


def course_list(request):
    if is_pdc_admin(request.user):
        courses = Course.objects.select_related("teacher")
        is_teacher_view = False
    elif is_teacher(request.user):
        courses = Course.objects.filter(teacher__user=request.user).select_related("teacher")
        is_teacher_view = True
    else:
        return redirect("user_dashboard")
    search = request.GET.get("search", "").strip()
    if search:
        courses = courses.filter(Q(course_name__icontains=search) | Q(teacher__full_name__icontains=search))
    return render(request, "enroll/course_list.html", {"courses": courses, "search": search, "active_page": "courses", "is_teacher_view": is_teacher_view})


@admin_required
def add_course(request):
    form = CourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Course added successfully.")
        return redirect("course_list")
    return render(request, "enroll/add_course.html", {"form": form, "active_page": "courses"})


@admin_required
def edit_course(request, id):
    course = get_object_or_404(Course, pk=id)
    form = CourseForm(request.POST or None, instance=course)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Course updated successfully.")
        return redirect("course_list")
    return render(request, "enroll/edit_course.html", {"form": form, "course": course, "active_page": "courses"})


@admin_required
def delete_course(request, id):
    course = get_object_or_404(Course, pk=id)
    if request.method == "POST":
        course.delete()
        messages.success(request, "Course deleted successfully.")
        return redirect("course_list")
    return render(request, "enroll/delete_course.html", {"course": course, "active_page": "courses"})


def course_detail(request, id):
    course = get_object_or_404(Course.objects.select_related("teacher"), pk=id)
    if not is_pdc_admin(request.user) and not (is_teacher(request.user) and course.teacher.user_id == request.user.id):
        return redirect("user_dashboard")
    return render(request, "enroll/course_detail.html", {"course": course, "active_page": "courses"})


@admin_required
def enrollment_list(request):
    enrollments = Enrollment.objects.select_related("student", "course").all()
    return render(request, "enroll/enrollment_list.html", {"enrollments": enrollments, "active_page": "enrollment"})


@admin_required
def add_enrollment(request):
    form = EnrollmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student enrolled successfully.")
        return redirect("enrollment_list")
    return render(request, "enroll/add_enrollment.html", {"form": form, "active_page": "enrollment"})


def attendance_list(request):
    if is_pdc_admin(request.user):
        attendance = Attendance.objects.select_related("student", "course").all()
    elif is_teacher(request.user):
        attendance = Attendance.objects.select_related("student", "course").filter(course__teacher__user=request.user)
    else:
        return redirect("user_dashboard")
    return render(request, "enroll/attendance_list.html", {"attendance": attendance, "active_page": "attendance"})


def add_attendance(request):
    if is_pdc_admin(request.user):
        form = AttendanceForm(request.POST or None)
    elif is_teacher(request.user):
        form = AttendanceForm(request.POST or None, teacher=request.user)
    else:
        return redirect("user_dashboard")
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Attendance added successfully.")
        return redirect("attendance_list")
    return render(request, "enroll/add_attendance.html", {"form": form, "active_page": "attendance"})


@admin_required
def certificate_list(request):
    certificates = Certificate.objects.select_related("student", "course").all()
    return render(request, "enroll/certificate_list.html", {"certificates": certificates, "active_page": "certificate"})


@admin_required
def add_certificate(request):
    form = CertificateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Certificate created successfully.")
        return redirect("certificate_list")
    return render(request, "enroll/add_certificate.html", {"form": form, "active_page": "certificate"})


@admin_required
def reports(request):
    context = {
        "total_students": Student.objects.count(),
        "total_teachers": Teacher.objects.count(),
        "total_courses": Course.objects.count(),
        "total_enrollments": Enrollment.objects.count(),
        "pending_enrollments": Enrollment.objects.filter(status=Enrollment.STATUS_PENDING).count(),
        "total_attendance": Attendance.objects.count(),
        "total_certificates": Certificate.objects.count(),
        "total_pdcs": pdc_detials.objects.count(),
        "active_page": "reports",
    }
    return render(request, "enroll/reports.html", context)
