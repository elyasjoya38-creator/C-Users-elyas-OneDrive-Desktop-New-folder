from django.contrib import admin
from .models import pdc_detials, Student, Teacher, Course, Enrollment, Attendance, Certificate


@admin.register(pdc_detials)
class PdcDetailsAdmin(admin.ModelAdmin):
    list_display = ("title", "producer", "types", "startdate", "enddate", "location")
    list_filter = ("types", "startdate")
    search_fields = ("title", "producer", "location")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "faculty", "department", "email")
    search_fields = ("student_id", "full_name", "email")
    list_filter = ("faculty", "department")


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialization", "email")
    search_fields = ("full_name", "specialization", "email")


admin.site.register((Course, Enrollment, Attendance, Certificate))
