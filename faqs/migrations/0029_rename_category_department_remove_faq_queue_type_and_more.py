# Generated by Django 5.1.3 on 2025-07-07 23:22

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faqs', '0028_alter_answer_node_type_alter_faq_queue_type'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Category',
            new_name='Department',
        ),
        migrations.RemoveField(
            model_name='faq',
            name='queue_type',
        ),
        migrations.AddField(
            model_name='answer',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, default=list, size=None),
        ),
        migrations.AddField(
            model_name='event',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, default=list, size=None),
        ),
        migrations.AddField(
            model_name='faq',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='faqs.department'),
        ),
        migrations.AddField(
            model_name='step',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, default=list, size=None),
        ),
        migrations.AlterField(
            model_name='faq',
            name='category',
            field=models.CharField(choices=[('Protocols', 'Protocols'), ('Tips', 'Tips'), ('Payrolls', 'Payrolls'), ('Escalations', 'Escalations'), ('FeedBack', 'FeedBack')], default='Scheduling', max_length=20),
        ),
        migrations.AlterField(
            model_name='faq',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, default=list, size=None),
        ),
    ]
