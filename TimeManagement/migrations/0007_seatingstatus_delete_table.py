# Generated by Django 5.0.4 on 2025-02-14 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TimeManagement', '0006_remove_timemanagementtable_col2_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeatingStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('row', models.IntegerField()),
                ('col', models.IntegerField()),
                ('cell_value', models.CharField(blank=True, max_length=255)),
                ('water_override', models.IntegerField(default=0)),
            ],
        ),
        migrations.DeleteModel(
            name='Table',
        ),
    ]
