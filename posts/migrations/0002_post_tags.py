# Generated by Django 5.1.3 on 2025-01-29 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
