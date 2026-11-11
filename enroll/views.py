from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.contrib.auth.models import Group

def is_admin(user):
    return user.groups.filter(
        name="Admin"
    ).exists()

admin_required = user_passes_test(
    is_admin
)


def is_pdc_admin(user):
    """Only staff/superusers may manage PDC records."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


admin_required = user_passes_test(is_pdc_admin, login_url="user_dashboard")


from .forms import (
    addpdcform,
    StudentForm,
    TeacherForm,
    CourseForm,
    EnrollmentForm,
    AttendanceForm,
    CertificateForm
)

from .models import (
    pdc_detials,
    Student,
    Teacher,
    Course,
    Enrollment,
    Attendance,
    Certificate,
)


def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def is_teacher(user):
    return user.groups.filter(name='Teacher').exists()

def is_student(user):
    return user.groups.filter(name='Student').exists()


@login_required
def home(request):
    if not is_pdc_admin(request.user):
        return redirect("user_dashboard")
    today = timezone.localdate()
    records = pdc_detials.objects.all()
    return render(request, "enroll/index.html", {

    "active_page": "home",

    "total_pdcs": records.count(),

    "seminar_count": records.filter(
        types="Seminar"
    ).count(),

    "workshop_count": records.filter(
        types="Workshop"
    ).count(),

    "upcoming_pdcs": records.filter(
        startdate__gte=today
    ).count(),

    "recent_pdcs": records.order_by("-id")[:5],

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
    return render(request, "enroll/user_dashboard.html", {"active_page": "user_dashboard"})


@admin_required
def pdcadd(request):
    form = addpdcform(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "PDC successfully added.")
        return redirect("managepdc")
    if request.method == "POST":
        messages.error(request, "Please correct the errors below.")
    return render(request, "enroll/addpdc.html", {"form": form, "active_page": "addpdc"})


@admin_required
def managepdc(request):
    records = pdc_detials.objects.all().order_by("-id")
    return render(request, "enroll/managepdc.html", {
        "data": records, "records": records, "active_page": "managepdc"
    })


@admin_required
def updatepdc(request, id):
    record = get_object_or_404(pdc_detials, pk=id)
    form = addpdcform(request.POST or None, instance=record)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "PDC successfully updated.")
        return redirect("managepdc")
    if request.method == "POST":
        messages.error(request, "Please correct the errors below.")
    return render(request, "enroll/updatepdc.html", {
        "form": form, "data": record, "active_page": "managepdc"
    })


@admin_required
@require_POST
def deletes(request, id):
    record = get_object_or_404(pdc_detials, pk=id)
    record.delete()
    messages.success(request, "PDC successfully deleted.")
    return redirect("managepdc")



def user_register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        # Public registration must never grant staff/admin privileges.
        user.is_staff = False
        user.is_superuser = False
        user.save()
        messages.success(request, "Your account was created. Please sign in.")
        return redirect("login")
    return render(request, "enroll/register.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url, allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                # Do not let normal users redirect into staff-only destinations.
                if is_pdc_admin(user) or next_url not in ("/addpdc/", "/managepdc/"):
                    return redirect(next_url)
            return redirect("home")
        messages.error(request, "Username or password is incorrect.")
    return render(request, "enroll/login.html")



@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


@admin_required
def student_list(request):

    search = request.GET.get("search")

    students = Student.objects.all()

    if search:
        students = students.filter(
            full_name__icontains=search
        )

    return render(
        request,
        "enroll/student_list.html",
        {
            "students": students,
            "active_page": "students"
        }
    )


@admin_required
def add_student(request):
    form = StudentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student added successfully")
        return redirect("student_list")

    return render(
        request,
        "enroll/add_student.html",
        {
            "form": form,
            "active_page": "students"
        }
    )


@admin_required
def edit_student(request, id):

    student = get_object_or_404(
        Student,
        id=id
    )

    form = StudentForm(
        request.POST or None,
        instance=student
    )

    if form.is_valid():
        form.save()
        return redirect("student_list")

    return render(
        request,
        "enroll/edit_student.html",
        {
            "form": form
        }
    )


@admin_required
def delete_student(request, id):

    student = get_object_or_404(
        Student,
        id=id
    )

    student.delete()

    return redirect("student_list")


@admin_required
def teacher_list(request):
    teachers = Teacher.objects.all()

    return render(
        request,
        "enroll/teacher_list.html",
        {
            "teachers": teachers,
            "active_page": "teachers"
        }
    )


@admin_required
def add_teacher(request):
    form = TeacherForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Teacher added successfully")
        return redirect("teacher_list")

    return render(
        request,
        "enroll/add_teacher.html",
        {
            "form": form,
            "active_page": "teachers"
        }
    )


@admin_required
def course_list(request):
    courses = Course.objects.all()

    return render(
        request,
        "enroll/course_list.html",
        {
            "courses": courses,
            "active_page": "courses"
        }
    )

@admin_required
def add_course(request):

    form = CourseForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Course added successfully")
        return redirect("course_list")

    return render(
        request,
        "enroll/add_course.html",
        {
            "form": form,
            "active_page": "courses"
        }
    )


@admin_required
def enrollment_list(request):

    enrollments = Enrollment.objects.all()

    return render(
        request,
        "enroll/enrollment_list.html",
        {
            "enrollments": enrollments,
            "active_page": "enrollment"
        }
    )


@admin_required
def add_enrollment(request):

    form = EnrollmentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Student enrolled successfully"
        )

        return redirect("enrollment_list")

    return render(
        request,
        "enroll/add_enrollment.html",
        {
            "form": form,
            "active_page": "enrollment"
        }
    )


@admin_required
def attendance_list(request):

    attendance = Attendance.objects.all()

    return render(
        request,
        "enroll/attendance_list.html",
        {
            "attendance": attendance,
            "active_page": "attendance"
        }
    )


@admin_required
def add_attendance(request):

    form = AttendanceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Attendance added successfully"
        )

        return redirect("attendance_list")

    return render(
        request,
        "enroll/add_attendance.html",
        {
            "form": form,
            "active_page": "attendance"
        }
    )


@admin_required
def certificate_list(request):

    certificates = Certificate.objects.all()

    return render(
        request,
        "enroll/certificate_list.html",
        {
            "certificates": certificates,
            "active_page": "certificate"
        }
    )


@admin_required
def add_certificate(request):

    form = CertificateForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Certificate created successfully"
        )

        return redirect("certificate_list")

    return render(
        request,
        "enroll/add_certificate.html",
        {
            "form": form,
            "active_page": "certificate"
        }
    )


@admin_required
def certificate_list(request):

    certificates = Certificate.objects.all()

    return render(
        request,
        "enroll/certificate_list.html",
        {
            "certificates": certificates,
            "active_page": "certificate"
        }
    )


@admin_required
def reports(request):

    context = {
        "total_students": Student.objects.count(),
        "total_teachers": Teacher.objects.count(),
        "total_courses": Course.objects.count(),
        "total_enrollments": Enrollment.objects.count(),
        "total_attendance": Attendance.objects.count(),
        "total_certificates": Certificate.objects.count(),
        "total_pdcs": pdc_detials.objects.count(),
        "active_page": "reports",
    }

    return render(
        request,
        "enroll/reports.html",
        context
    )

@admin_required
def edit_teacher(request, id):

    teacher = get_object_or_404(
        Teacher,
        id=id
    )

    form = TeacherForm(
        request.POST or None,
        instance=teacher
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Teacher updated successfully"
        )

        return redirect("teacher_list")

    return render(
        request,
        "enroll/edit_teacher.html",
        {
            "form": form
        }
    )

@admin_required
def delete_teacher(request, id):

    teacher = get_object_or_404(
        Teacher,
        id=id
    )

    teacher.delete()

    messages.success(
        request,
        "Teacher deleted successfully"
    )

    return redirect("teacher_list")

@admin_required
def edit_student(request, id):

    student = get_object_or_404(
        Student,
        id=id
    )

    form = StudentForm(
        request.POST or None,
        instance=student
    )

    if request.method == "POST" and form.is_valid():

        form.save()

        messages.success(
            request,
            "Student updated successfully"
        )

        return redirect("student_list")

    return render(
        request,
        "enroll/edit_student.html",
        {
            "form": form
        }
    )

@admin_required
def delete_student(request, id):

    student = get_object_or_404(
        Student,
        id=id
    )

    if request.method == "POST":
        student.delete()

        messages.success(
            request,
            "Student deleted successfully"
        )

        return redirect("student_list")

    return render(
        request,
        "enroll/delete_student.html",
        {
            "student": student
        }
    )

@admin_required
def edit_course(request, id):

    course = get_object_or_404(
        Course,
        id=id
    )

    form = CourseForm(
        request.POST or None,
        instance=course
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        return redirect("course_list")

    return render(
        request,
        "enroll/edit_course.html",
        {
            "form": form
        }
    )

@admin_required
def delete_course(request, id):

    course = get_object_or_404(
        Course,
        id=id
    )

    if request.method == "POST":

        course.delete()

        messages.success(
            request,
            "Course deleted successfully"
        )

        return redirect("course_list")

    return render(
        request,
        "enroll/delete_course.html",
        {
            "course": course
        }
    )

@admin_required
def student_list(request):

    search = request.GET.get("search")

    students = Student.objects.all()

    if search:
        students = students.filter(
            full_name__icontains=search
        )

    return render(
        request,
        "enroll/student_list.html",
        {
            "students": students,
            "active_page": "students"
        }
    )

@admin_required
def edit_teacher(request, id):
    teacher = get_object_or_404(
        Teacher,
        id=id
    )

    return render(
        request,
        "enroll/edit_teacher.html"
    )

@admin_required
def course_list(request):

    search = request.GET.get("search")

    courses = Course.objects.all()

    if search:
        courses = courses.filter(
            course_name__icontains=search
        )

    return render(
        request,
        "enroll/course_list.html",
        {
            "courses": courses,
            "active_page": "courses"
        }
    )

@admin_required
def student_detail(request, id):

    student = get_object_or_404(
        Student,
        id=id
    )

    return render(
        request,
        "enroll/student_detail.html",
        {
            "student": student
        }
    )

@admin_required
def teacher_detail(request, id):

    teacher = get_object_or_404(
        Teacher,
        id=id
    )

    return render(
        request,
        "enroll/teacher_detail.html",
        {
            "teacher": teacher
        }
    )

@admin_required
def course_detail(request, id):

    course = get_object_or_404(
        Course,
        id=id
    )

    return render(
        request,
        "enroll/course_detail.html",
        {
            "course": course
        }
    )


def is_teacher(user):
    return user.groups.filter(
        name="Teacher"
    ).exists()


def is_student(user):
    return user.groups.filter(
        name="Student"
    ).exists()

