# Generated by Django 5.1.1 on 2024-10-01 16:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visit',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 10, 1, 16, 27, 12, 407401)),
        ),
    ]
