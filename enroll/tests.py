from django.contrib.auth import get_user_model
from django.test import TestCase

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
