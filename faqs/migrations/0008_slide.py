# Generated by Django 5.1.3 on 2024-11-12 18:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faqs', '0007_answer_has_steps'),
    ]

    operations = [
        migrations.CreateModel(
            name='Slide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField()),
                ('down', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='down_slide', to='faqs.slide')),
                ('faq', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slides', to='faqs.faq')),
                ('left', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='left_slide', to='faqs.slide')),
                ('right', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='right_slide', to='faqs.slide')),
                ('up', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='up_slide', to='faqs.slide')),
            ],
        ),
    ]