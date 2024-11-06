# Generated by Django 5.1.1 on 2024-11-03 20:33

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events_app', '0004_alter_visit_created_at_alter_visit_visitors'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='events',
            field=models.ManyToManyField(through='events_app.EventVisit', to='events_app.event'),
        ),
        migrations.AlterField(
            model_name='visit',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 3, 20, 33, 12, 557099)),
        ),
    ]
