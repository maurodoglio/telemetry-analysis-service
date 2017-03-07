# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-02-22 15:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0012_add_job_run_history'),
    ]

    operations = [
        migrations.CreateModel(
            name='SparkJobRunAlert',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('run', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='alert', serialize=False, to='jobs.SparkJobRun')),
                ('reason', models.CharField(blank=True, help_text='The reason for the creation of the alert.', max_length=50, null=True)),
                ('mail_sent_date', models.DateTimeField(blank=True, help_text='The datetime the alert email was sent.', null=True)),
            ],
            options={
                'abstract': False,
                'get_latest_by': 'modified_at',
                'ordering': ('-modified_at', '-created_at'),
            },
        ),
    ]
