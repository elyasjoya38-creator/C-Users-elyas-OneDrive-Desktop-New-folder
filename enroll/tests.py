from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .forms import TeacherForm
from .models import Teacher


class TeacherAccountCreationTests(TestCase):
    def test_staff_teacher_form_creates_linked_non_staff_account(self):
        form = TeacherForm(data={
            "full_name": "Amina Teacher",
            "specialization": "Mathematics",
            "email": "amina@example.com",
            "phone": "0700000000",
            "username": "amina_teacher",
            "password1": "TeacherPass!7392",
            "password2": "TeacherPass!7392",
        })
        self.assertTrue(form.is_valid(), form.errors)
        teacher = form.save()
        user = teacher.user
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password("TeacherPass!7392"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.groups.filter(name="Teacher").exists())
        self.assertEqual(Teacher.objects.count(), 1)

    def test_duplicate_username_is_rejected(self):
        User = get_user_model()
        User.objects.create_user(username="taken", password="OtherPass!6382")
        form = TeacherForm(data={
            "full_name": "Amina Teacher",
            "specialization": "Mathematics",
            "email": "amina@example.com",
            "phone": "0700000000",
            "username": "TAKEN",
            "password1": "TeacherPass!7392",
            "password2": "TeacherPass!7392",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_edit_form_preserves_linked_account_without_credential_fields(self):
        User = get_user_model()
        user = User.objects.create_user(username="amina_teacher", password="TeacherPass!7392")
        teacher = Teacher.objects.create(
            full_name="Amina Teacher",
            specialization="Mathematics",
            email="amina@example.com",
            phone="0700000000",
            user=user,
        )
        form = TeacherForm(instance=teacher)
        self.assertNotIn("username", form.fields)
        self.assertNotIn("password1", form.fields)
        self.assertNotIn("password2", form.fields)
        self.assertEqual(form.save().user, user)

    def test_admin_can_create_teacher_and_teacher_can_sign_in(self):
        User = get_user_model()
        admin = User.objects.create_user(username="pdc_admin", password="AdminPass!7392", is_staff=True)
        self.client.force_login(admin)
        response = self.client.post(reverse("add_teacher"), {
            "full_name": "Amina Teacher",
            "specialization": "Mathematics",
            "email": "amina@example.com",
            "phone": "0700000000",
            "username": "amina_teacher",
            "password1": "TeacherPass!7392",
            "password2": "TeacherPass!7392",
        })
        self.assertRedirects(response, reverse("teacher_list"))
        teacher = Teacher.objects.get(email="amina@example.com")
        self.assertEqual(teacher.user.username, "amina_teacher")
        self.assertTrue(teacher.user.groups.filter(name="Teacher").exists())
        self.client.logout()
        self.assertTrue(self.client.login(username="amina_teacher", password="TeacherPass!7392"))
        self.assertEqual(self.client.get(reverse("user_dashboard")).status_code, 200)

    def test_student_cannot_open_teacher_creation_page(self):
        User = get_user_model()
        student_user = User.objects.create_user(username="student_user", password="StudentPass!7392")
        student_group, _ = Group.objects.get_or_create(name="Student")
        student_user.groups.add(student_group)
        self.client.force_login(student_user)
        response = self.client.get(reverse("add_teacher"))
        self.assertNotEqual(response.status_code, 200)


