# Generated by Django 5.1.3 on 2024-11-11 22:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faqs', '0002_answer_category_event_responsetype_remove_faq_answer_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='answer',
            name='steps',
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField()),
                ('text', models.TextField()),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='faqs.answer')),
            ],
        ),
    ]
