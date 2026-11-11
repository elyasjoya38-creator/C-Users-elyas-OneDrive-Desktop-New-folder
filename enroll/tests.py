from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Course, Student, Teacher

User = get_user_model()


class AccessControlTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="test-pass-12345")
        self.user = User.objects.create_user(username="regular", password="test-pass-12345")

    def test_dashboard_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_superuser_can_open_dashboard(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_regular_user_is_redirected_from_admin_dashboard(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse("home")), reverse("user_dashboard"))

    def test_regular_user_cannot_open_management_page(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("student_list")).status_code, 302)


class DeleteMethodTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="test-pass-12345")
        self.client.force_login(self.admin)
        teacher = Teacher.objects.create(full_name="Teacher", specialization="Math", email="teacher@example.com", phone="123")
        self.teacher = teacher
        self.student = Student.objects.create(student_id="S1", full_name="Student", faculty="Science", department="Math", email="student@example.com", phone="456")
        self.course = Course.objects.create(course_name="Math", teacher=teacher, start_date="2026-01-01", end_date="2026-01-10", description="Course")

    def test_teacher_cannot_be_deleted_with_get(self):
        response = self.client.get(reverse("delete_teacher", args=[self.teacher.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Teacher.objects.filter(pk=self.teacher.pk).exists())

    def test_teacher_can_be_deleted_with_post(self):
        response = self.client.post(reverse("delete_teacher", args=[self.teacher.pk]))
        self.assertRedirects(response, reverse("teacher_list"))
        self.assertFalse(Teacher.objects.filter(pk=self.teacher.pk).exists())

    def test_student_cannot_be_deleted_with_get(self):
        response = self.client.get(reverse("delete_student", args=[self.student.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Student.objects.filter(pk=self.student.pk).exists())

    def test_course_cannot_be_deleted_with_get(self):
        response = self.client.get(reverse("delete_course", args=[self.course.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())
