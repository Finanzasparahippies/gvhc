# Generated by Django 5.1.2 on 2024-12-01 19:32

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('faqs', '0012_remove_answerconnection_condition_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='step',
            name='image',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='image'),
        ),
    ]
