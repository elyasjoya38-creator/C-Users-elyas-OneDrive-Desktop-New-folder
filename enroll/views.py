from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AddPDCForm, AttendanceForm, CertificateForm, CourseForm, EnrollmentForm, StudentForm, StudentRegistrationForm, TeacherForm
from .models import Attendance, Certificate, Course, Enrollment, PDCRegistration, Student, Teacher, pdc_detials


def is_pdc_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def is_admin(user):
    return is_pdc_admin(user)


admin_required = user_passes_test(is_pdc_admin, login_url="user_dashboard")


def is_teacher(user):
    return user.is_authenticated and user.groups.filter(name="Teacher").exists()


def is_student(user):
    return user.is_authenticated and user.groups.filter(name="Student").exists()


def _student_dashboard_context(user):
    student = Student.objects.filter(user=user).first()
    context = {"active_page": "user_dashboard", "is_student": is_student(user), "is_teacher": is_teacher(user), "student_profile": student, "teacher_profile": Teacher.objects.filter(user=user).first()}
    if student and is_student(user):
        today = timezone.localdate()
        context.update({
            "enrollments": student.enrollments.select_related("course", "course__teacher"),
            "available_courses": Course.objects.exclude(enrollments__student=student).filter(end_date__gte=today).select_related("teacher"),
            "pdc_registrations": student.pdc_registrations.select_related("pdc"),
            "available_pdcs": pdc_detials.objects.filter(Q(startdate__isnull=True) | Q(startdate__gte=today)).exclude(registrations__student=student).annotate(registration_count=Count("registrations")).order_by("startdate", "id"),
        })
    teacher = context["teacher_profile"]
    if teacher and is_teacher(user):
        context["teacher_courses"] = Course.objects.filter(teacher=teacher).prefetch_related("enrollments__student")
    return context


@login_required
def home(request):
    if not is_pdc_admin(request.user):
        return redirect("user_dashboard")
    today = timezone.localdate()
    records = pdc_detials.objects.all()
    return render(request, "enroll/index.html", {
        "active_page": "home", "total_pdcs": records.count(),
        "seminar_count": records.filter(types="Seminar").count(),
        "workshop_count": records.filter(types="Workshop").count(),
        "upcoming_pdcs": records.filter(startdate__gte=today).count(),
        "recent_pdcs": records[:5], "total_students": Student.objects.count(),
        "total_teachers": Teacher.objects.count(), "total_courses": Course.objects.count(),
        "total_enrollments": Enrollment.objects.count(), "pending_enrollments": Enrollment.objects.filter(status=Enrollment.STATUS_PENDING).count(),
        "total_pdc_registrations": PDCRegistration.objects.count(), "total_attendance": Attendance.objects.count(),
        "total_certificates": Certificate.objects.count(),
    })


@login_required
def user_dashboard(request):
    if is_pdc_admin(request.user):
        return redirect("home")
    return render(request, "enroll/user_dashboard.html", _student_dashboard_context(request.user))


@login_required
@require_POST
def student_enroll(request, course_id):
    if not is_student(request.user):
        messages.error(request, "فقط شاگردان می‌توانند درخواست ثبت‌نام کورس بفرستند.")
        return redirect("user_dashboard")
    student = Student.objects.filter(user=request.user).first()
    if student is None:
        messages.error(request, "حساب شما به پروفایل شاگرد وصل نیست؛ با ادارهٔ PDC تماس بگیرید.")
        return redirect("user_dashboard")
    course = get_object_or_404(Course, pk=course_id)
    if course.end_date < timezone.localdate():
        messages.error(request, "مهلت ثبت‌نام این کورس تمام شده است.")
        return redirect("user_dashboard")
    enrollment, created = Enrollment.objects.get_or_create(student=student, course=course, defaults={"status": Enrollment.STATUS_PENDING})
    if created:
        messages.success(request, "درخواست ثبت‌نام کورس ارسال شد و منتظر بررسی مدیر است.")
    elif enrollment.status == Enrollment.STATUS_REJECTED:
        enrollment.status = Enrollment.STATUS_PENDING
        enrollment.save(update_fields=["status"])
        messages.success(request, "درخواست ثبت‌نام دوباره ارسال شد.")
    else:
        messages.info(request, "برای این کورس قبلاً درخواست ثبت‌نام فرستاده‌اید.")
    return redirect("user_dashboard")


@login_required
@require_POST
def student_register_pdc(request, pdc_id):
    if not is_student(request.user):
        messages.error(request, "فقط شاگردان می‌توانند برای برنامه‌های PDC ثبت‌نام کنند.")
        return redirect("user_dashboard")
    student = Student.objects.filter(user=request.user).first()
    if student is None:
        messages.error(request, "حساب شما به پروفایل شاگرد وصل نیست؛ با ادارهٔ PDC تماس بگیرید.")
        return redirect("user_dashboard")
    pdc = get_object_or_404(pdc_detials, pk=pdc_id)
    today = timezone.localdate()
    if pdc.enddate and pdc.enddate < today:
        messages.error(request, "ثبت‌نام این برنامه بسته شده است.")
        return redirect("user_dashboard")
    registration, created = PDCRegistration.objects.get_or_create(student=student, pdc=pdc, defaults={"status": PDCRegistration.STATUS_PENDING})
    if created:
        messages.success(request, "درخواست اشتراک در برنامه ارسال شد و در پنل مدیر ثبت گردید.")
    elif registration.status == PDCRegistration.STATUS_REJECTED:
        registration.status = PDCRegistration.STATUS_PENDING
        registration.save(update_fields=["status"])
        messages.success(request, "درخواست اشتراک دوباره ارسال شد.")
    else:
        messages.info(request, "درخواست شما برای این برنامه از قبل ثبت شده است.")
    return redirect("user_dashboard")


@admin_required
def pdcadd(request):
    form = AddPDCForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "برنامهٔ PDC ثبت و در پنل شاگردان برای اطلاع و ثبت‌نام نمایش داده شد.")
        return redirect("managepdc")
    return render(request, "enroll/addpdc.html", {"form": form, "active_page": "addpdc"})


@admin_required
def managepdc(request):
    records = pdc_detials.objects.annotate(registration_count=Count("registrations"), pending_count=Count("registrations", filter=Q(registrations__status=PDCRegistration.STATUS_PENDING)), approved_count=Count("registrations", filter=Q(registrations__status=PDCRegistration.STATUS_APPROVED)))
    return render(request, "enroll/managepdc.html", {"data": records, "records": records, "active_page": "managepdc", "total_pdc_registrations": PDCRegistration.objects.count(), "pending_pdc_registrations": PDCRegistration.objects.filter(status=PDCRegistration.STATUS_PENDING).count()})


@admin_required
def pdc_registrations(request):
    registrations = PDCRegistration.objects.select_related("student", "pdc")
    return render(request, "enroll/pdc_registrations.html", {"registrations": registrations, "active_page": "managepdc"})


@admin_required
@require_POST
def review_pdc_registration(request, registration_id):
    registration = get_object_or_404(PDCRegistration, pk=registration_id)
    status = request.POST.get("status")
    if status not in (PDCRegistration.STATUS_APPROVED, PDCRegistration.STATUS_REJECTED):
        messages.error(request, "حالت درخواست معتبر نیست.")
    else:
        registration.status = status
        registration.save(update_fields=["status"])
        messages.success(request, f"درخواست {registration.get_status_display()} شد.")
    return redirect("pdc_registrations")


@admin_required
def updatepdc(request, id):
    record = get_object_or_404(pdc_detials, pk=id)
    form = AddPDCForm(request.POST or None, instance=record)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "برنامهٔ PDC به‌روز شد؛ معلومات تازه در پنل شاگردان نمایش داده می‌شود.")
        return redirect("managepdc")
    return render(request, "enroll/updatepdc.html", {"form": form, "data": record, "active_page": "managepdc"})


@admin_required
@require_POST
def deletes(request, id):
    get_object_or_404(pdc_detials, pk=id).delete()
    messages.success(request, "برنامهٔ PDC حذف شد.")
    return redirect("managepdc")


@admin_required
@require_POST
def review_enrollment(request, id):
    enrollment = get_object_or_404(Enrollment, pk=id)
    status = request.POST.get("status")
    if status not in (Enrollment.STATUS_APPROVED, Enrollment.STATUS_REJECTED):
        messages.error(request, "حالت درخواست معتبر نیست.")
    else:
        enrollment.status = status
        enrollment.save(update_fields=["status"])
        messages.success(request, f"درخواست ثبت‌نام {enrollment.get_status_display()} شد.")
    return redirect("enrollment_list")


def user_register(request):
    if request.user.is_authenticated:
        return redirect("home" if is_pdc_admin(request.user) else "user_dashboard")
    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except Student.DoesNotExist:
            form.add_error("student_id", "این شمارهٔ شاگردی هم‌زمان به حساب دیگری وصل شده است؛ با ادارهٔ PDC تماس بگیرید.")
        else:
            messages.success(request, "حساب شاگرد ساخته شد. اکنون وارد سیستم شوید.")
            return redirect("login")
    return render(request, "enroll/register.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home" if is_pdc_admin(request.user) else "user_dashboard")
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username", "").strip(), password=request.POST.get("password", ""))
        if user is not None:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect("home" if is_pdc_admin(user) else "user_dashboard")
        messages.error(request, "نام کاربری یا رمز عبور نادرست است.")
    return render(request, "enroll/login.html")


@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, "از حساب خارج شدید.")
    return redirect("login")


@admin_required
def student_list(request):
    search = request.GET.get("search", "").strip()
    students = Student.objects.order_by("id")
    if search:
        students = students.filter(Q(full_name__icontains=search) | Q(student_id__icontains=search) | Q(email__icontains=search) | Q(department__icontains=search) | Q(faculty__icontains=search))
    return render(request, "enroll/student_list.html", {"students": students, "search": search, "active_page": "students"})


@admin_required
def add_student(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "شاگرد ثبت شد. شمارهٔ شاگردی را برای ساخت حساب به او بدهید.")
        return redirect("student_list")
    return render(request, "enroll/add_student.html", {"form": form, "active_page": "students"})


@admin_required
def edit_student(request, id):
    student = get_object_or_404(Student, pk=id)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "معلومات شاگرد به‌روز شد.")
        return redirect("student_list")
    return render(request, "enroll/edit_student.html", {"form": form, "student": student, "active_page": "students"})


@admin_required
@require_POST
def delete_student(request, id):
    get_object_or_404(Student, pk=id).delete()
    messages.success(request, "شاگرد حذف شد.")
    return redirect("student_list")


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
        messages.success(request, "پروفایل استاد ثبت شد؛ اگر حساب کاربری وصل شده باشد، دسترسی استاد فعال است.")
        return redirect("teacher_list")
    return render(request, "enroll/add_teacher.html", {"form": form, "active_page": "teachers"})


@admin_required
def edit_teacher(request, id):
    teacher = get_object_or_404(Teacher, pk=id)
    form = TeacherForm(request.POST or None, instance=teacher)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "معلومات استاد به‌روز شد.")
        return redirect("teacher_list")
    return render(request, "enroll/edit_teacher.html", {"form": form, "teacher": teacher, "active_page": "teachers"})


@admin_required
@require_POST
def delete_teacher(request, id):
    get_object_or_404(Teacher, pk=id).delete()
    messages.success(request, "پروفایل استاد حذف شد.")
    return redirect("teacher_list")


@admin_required
def teacher_detail(request, id):
    teacher = get_object_or_404(Teacher, pk=id)
    return render(request, "enroll/teacher_detail.html", {"teacher": teacher, "active_page": "teachers"})


def course_list(request):
    if is_pdc_admin(request.user):
        courses, is_teacher_view = Course.objects.select_related("teacher"), False
    elif is_teacher(request.user):
        courses, is_teacher_view = Course.objects.filter(teacher__user=request.user).select_related("teacher"), True
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
        messages.success(request, "کورس ثبت شد و در پنل شاگردان برای دیدن و درخواست ثبت‌نام نمایش داده می‌شود.")
        return redirect("course_list")
    return render(request, "enroll/add_course.html", {"form": form, "active_page": "courses"})


@admin_required
def edit_course(request, id):
    course = get_object_or_404(Course, pk=id)
    form = CourseForm(request.POST or None, instance=course)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "کورس به‌روز شد.")
        return redirect("course_list")
    return render(request, "enroll/edit_course.html", {"form": form, "course": course, "active_page": "courses"})


@admin_required
@require_POST
def delete_course(request, id):
    get_object_or_404(Course, pk=id).delete()
    messages.success(request, "کورس حذف شد.")
    return redirect("course_list")


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
        enrollment = form.save(commit=False)
        enrollment.status = Enrollment.STATUS_APPROVED
        enrollment.save()
        messages.success(request, "ثبت‌نام شاگرد در کورس انجام شد.")
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
        messages.success(request, "حاضری ثبت شد.")
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
        messages.success(request, "سند فراغت ثبت شد.")
        return redirect("certificate_list")
    return render(request, "enroll/add_certificate.html", {"form": form, "active_page": "certificate"})


@admin_required
def reports(request):
    context = {"total_students": Student.objects.count(), "total_teachers": Teacher.objects.count(), "total_courses": Course.objects.count(), "total_enrollments": Enrollment.objects.count(), "pending_enrollments": Enrollment.objects.filter(status=Enrollment.STATUS_PENDING).count(), "total_pdc_registrations": PDCRegistration.objects.count(), "pending_pdc_registrations": PDCRegistration.objects.filter(status=PDCRegistration.STATUS_PENDING).count(), "total_attendance": Attendance.objects.count(), "total_certificates": Certificate.objects.count(), "total_pdcs": pdc_detials.objects.count(), "active_page": "reports"}
    return render(request, "enroll/reports.html", context)
