# Generated by Django 5.0.4 on 2025-01-28 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TimeManagement', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TableRow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column1', models.CharField(blank=True, max_length=255, null=True)),
                ('column2', models.CharField(blank=True, max_length=255, null=True)),
                ('column3', models.CharField(blank=True, max_length=255, null=True)),
                ('column4', models.CharField(blank=True, max_length=255, null=True)),
                ('column5', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
    ]
