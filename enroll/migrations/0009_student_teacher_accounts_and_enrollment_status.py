# Generated for student account linking, teacher ownership, and reviewed enrollment requests.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("enroll", "0008_certificate"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="user",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="student_profile", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="teacher",
            name="user",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="teacher_profile", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="enrollment",
            name="status",
            field=models.CharField(choices=[("pending", "Pending review"), ("approved", "Approved"), ("rejected", "Rejected")], default="approved", max_length=12),
        ),
        migrations.AlterField(
            model_name="enrollment",
            name="course",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="enroll.course"),
        ),
        migrations.AlterField(
            model_name="enrollment",
            name="student",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="enroll.student"),
        ),
    ]
