# Generated by Django 5.1.3 on 2024-11-11 19:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faqs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.TextField(blank=True, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='answers/')),
                ('steps', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('relevance', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('requirements', models.TextField(blank=True)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('hospital', models.CharField(blank=True, max_length=255)),
                ('county', models.CharField(blank=True, max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('event_type', models.CharField(choices=[('PRIMORDIAL', 'Primordial'), ('NORMAL', 'Normal')], default='NORMAL', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ResponseType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='faq',
            name='answer',
        ),
        migrations.AddField(
            model_name='faq',
            name='keywords',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='faq',
            name='answers',
            field=models.ManyToManyField(related_name='faqs', to='faqs.answer'),
        ),
        migrations.CreateModel(
            name='AnswerConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition', models.CharField(blank=True, max_length=20, null=True)),
                ('from_answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_connections', to='faqs.answer')),
                ('to_answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_connections', to='faqs.answer')),
            ],
        ),
        migrations.AddField(
            model_name='answer',
            name='related_answers',
            field=models.ManyToManyField(through='faqs.AnswerConnection', to='faqs.answer'),
        ),
        migrations.AddField(
            model_name='faq',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='faqs.category'),
        ),
        migrations.AddField(
            model_name='faq',
            name='events',
            field=models.ManyToManyField(blank=True, related_name='events', to='faqs.event'),
        ),
        migrations.AddField(
            model_name='faq',
            name='response_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='faqs.responsetype'),
        ),
    ]
