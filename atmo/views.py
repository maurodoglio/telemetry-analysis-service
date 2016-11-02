# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
import logging
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseServerError
from django.template import Context, loader, TemplateDoesNotExist
from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token

from .clusters.models import Cluster
from .jobs.models import SparkJob


logger = logging.getLogger("django")


@login_required
def dashboard(request):
    # allowed filters for clusters
    default_filter = 'active'
    clusters_filters = ['active', 'terminated', 'failed', 'all']

    # the cluster filter defaults to active ones
    clusters_shown = request.GET.get('clusters', default_filter)
    if clusters_shown not in clusters_filters:
        clusters_shown = default_filter

    clusters = getattr(Cluster.objects, clusters_shown)().filter(
        created_by=request.user
    ).order_by("-start_date")

    spark_jobs = SparkJob.objects.filter(
        created_by=request.user
    ).order_by("start_date")

    context = {
        'clusters': clusters,
        'clusters_shown': clusters_shown,
        'clusters_filters': clusters_filters,
        'spark_jobs': spark_jobs,
    }
    return render(request, 'atmo/dashboard.html', context=context)


@requires_csrf_token
def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: :template:`500.html`
    Context: None
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
    return HttpResponseServerError(template.render(Context({
        'request': request,
    })))
