# Generated by Django 5.1.6 on 2025-02-13 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userresume',
            name='position',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
