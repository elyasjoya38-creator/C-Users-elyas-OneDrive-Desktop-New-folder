from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("enroll", "0009_student_teacher_photos"), ("auth", "0012_alter_user_first_name_max_length")]
    operations = [
        migrations.AddField(
            model_name="student",
            name="user",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="student_profile", to="auth.user"),
        ),
        migrations.AddField(
            model_name="teacher",
            name="user",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="teacher_profile", to="auth.user"),
        ),
    ]
