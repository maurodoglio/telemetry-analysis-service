# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-23 13:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0030_rename_run_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sparkjobrun',
            name='started_at',
            field=models.DateTimeField(blank=True, help_text='Date/time when the cluster was started on AWS EMR.', null=True),
        ),
    ]
