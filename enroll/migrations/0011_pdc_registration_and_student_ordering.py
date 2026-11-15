# Generated for PDC event registrations and deterministic student ordering.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("enroll", "0010_alter_attendance_options_alter_certificate_options_and_more")]

    operations = [
        migrations.AlterModelOptions(
            name="student",
            options={"ordering": ["id"]},
        ),
        migrations.AddModel(
            name="pdcregistration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(choices=[("pending", "Pending review"), ("approved", "Registered"), ("rejected", "Rejected")], default="pending", max_length=12)),
                ("pdc", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="registrations", to="enroll.pdc_detials")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pdc_registrations", to="enroll.student")),
            ],
            options={"ordering": ["-requested_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="pdcregistration",
            constraint=models.UniqueConstraint(fields=("student", "pdc"), name="unique_student_pdc_registration"),
        ),
    ]
