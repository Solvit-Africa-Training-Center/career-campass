# Generated manually

from django.db import migrations
import uuid

def add_uuids_to_existing_students(apps, schema_editor):
    Student = apps.get_model('accounts', 'Student')
    for student in Student.objects.all():
        student.uuid = uuid.uuid4()
        student.save()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_student_uuid'),
    ]

    operations = [
        migrations.RunPython(add_uuids_to_existing_students),
    ]
