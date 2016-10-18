# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
import logging
from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone

from .forms import NewSparkJobForm, EditSparkJobForm, DeleteSparkJobForm
from .models import SparkJob


logger = logging.getLogger("django")


@login_required
def new_spark_job(request):
    username = request.user.email.split("@")[0]
    initial = {
        "identifier": "{}-telemetry-scheduled-task".format(username),
        "size": 1,
        "interval_in_hours": SparkJob.WEEKLY,
        "job_timeout": 24,
        "start_date": timezone.now(),
    }
    if request.method == 'POST':
        form = NewSparkJobForm(
            request.user,
            data=request.POST,
            files=request.FILES,
            initial=initial,
        )
        if form.is_valid():
            # this will also magically create the spark job for us
            spark_job = form.save()
            return redirect(spark_job)
    else:
        form = NewSparkJobForm(
            request.user,
            initial=initial,
        )
    context = {
        'form': form,
    }
    return render(request, 'atmo/spark-job-new.html', context)


@login_required
def edit_spark_job(request, id):
    spark_job = get_object_or_404(SparkJob, created_by=request.user, pk=id)
    if request.method == 'POST':
        form = EditSparkJobForm(
            request.user,
            data=request.POST,
            files=request.FILES,
            instance=spark_job,
        )
        if form.is_valid():
            # this will also update the job for us
            spark_job = form.save()
            return redirect(spark_job)
    else:
        form = EditSparkJobForm(
            request.user,
            instance=spark_job,
        )
    context = {
        'form': form,
    }
    return render(request, 'atmo/spark-job-edit.html', context)


@login_required
def delete_spark_job(request, id):
    job = get_object_or_404(SparkJob, created_by=request.user, pk=id)
    if request.method == 'POST':
        form = DeleteSparkJobForm(
            request.user,
            data=request.POST,
            instance=job,
        )
        if form.is_valid():
            job.delete()
            return redirect('dashboard')
    else:
        form = DeleteSparkJobForm(
            request.user,
            instance=job,
        )
    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'atmo/spark-job-delete.html', context=context)


@login_required
def detail_spark_job(request, id):
    job = get_object_or_404(SparkJob, created_by=request.user, pk=id)
    delete_form = DeleteSparkJobForm(
        request.user,
        instance=job,
    )
    # hiding the confirmation input on the detail page
    delete_form.fields['confirmation'].widget = forms.HiddenInput()
    context = {
        'job': job,
        'delete_form': delete_form,
    }
    return render(request, 'atmo/spark-job-detail.html', context=context)
