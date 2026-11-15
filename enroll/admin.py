from django.contrib import admin
from .models import Attendance, Certificate, Course, Enrollment, PDCRegistration, Student, Teacher, pdc_detials


@admin.register(pdc_detials)
class PdcDetailsAdmin(admin.ModelAdmin):
    list_display = ("title", "producer", "types", "startdate", "enddate", "location")
    list_filter = ("types", "startdate")
    search_fields = ("title", "producer", "location")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "faculty", "department", "email", "user")
    search_fields = ("student_id", "full_name", "email")
    ordering = ("id",)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialization", "email", "user")
    search_fields = ("full_name", "email", "specialization")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("course_name", "teacher", "start_date", "end_date")
    list_filter = ("teacher", "start_date")
    search_fields = ("course_name", "teacher__full_name")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "enrolled_at", "status")
    list_filter = ("status", "course")
    search_fields = ("student__full_name", "student__student_id", "course__course_name")


@admin.register(PDCRegistration)
class PDCRegistrationAdmin(admin.ModelAdmin):
    list_display = ("pdc", "student", "requested_at", "status")
    list_filter = ("status", "pdc")
    search_fields = ("pdc__title", "student__full_name", "student__student_id")


admin.site.register(Attendance)
admin.site.register(Certificate)
