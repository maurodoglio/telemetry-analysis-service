# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
import logging
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .clusters.models import Cluster
from .jobs.forms import NewSparkJobForm, EditSparkJobForm, DeleteSparkJobForm
from .jobs.models import SparkJob


logger = logging.getLogger("django")


@login_required
def dashboard(request):
    username = request.user.email.split("@")[0]
    clusters = (Cluster.objects.filter(created_by=request.user)
                               .filter(end_date__gt=timezone.now() - timedelta(days=1))
                               .order_by("-start_date"))
    jobs = SparkJob.objects.filter(created_by=request.user).order_by("start_date")
    context = {
        "active_clusters": clusters,
        "user_spark_jobs": jobs,
        "new_spark_job_form": NewSparkJobForm(request.user, initial={
            "identifier": "{}-telemetry-scheduled-task".format(username),
            "size": 1,
            "interval_in_hours": 24 * 7,
            "job_timeout": 24,
            "start_date": datetime.now(),
        }),
        "edit_spark_job_form": EditSparkJobForm(request.user),
        "delete_spark_job_form": DeleteSparkJobForm(request.user),
    }
    return render(request, 'atmo/dashboard.html', context=context)
