from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("enroll", "0008_certificate")]

    operations = [
        migrations.AddField(
            model_name="student",
            name="photo",
            field=models.ImageField(blank=True, null=True, upload_to="students/"),
        ),
        migrations.AddField(
            model_name="teacher",
            name="photo",
            field=models.ImageField(blank=True, null=True, upload_to="teachers/"),
        ),
    ]
