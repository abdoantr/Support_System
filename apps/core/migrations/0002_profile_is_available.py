# Generated by Django 5.0 on 2025-02-11 23:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_available',
            field=models.BooleanField(default=True, help_text='Whether the user is available to take new support tickets'),
        ),
    ]
