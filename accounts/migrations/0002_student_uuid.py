# Generated manually

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, help_text="UUID used for cross-service references"),
        ),
    ]
