# Generated by Django 5.0.4 on 2025-02-24 10:30

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TimeManagement', '0008_timemanagementtable_col2_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='timemanagementtable',
            name='date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
