import logging
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect

from session_csrf import anonymous_csrf

from analysis_service.base import forms
from analysis_service.base import models
from analysis_service.base.util import provisioning


logger = logging.getLogger("django")


@login_required
def dashboard(request):
    username = request.user.email.split("@")[0]
    return render(request, 'analysis_service/dashboard.jinja', context={
        "active_clusters": models.Cluster.objects.filter(created_by=request.user)
                                                 .order_by("creation_date"),
        "new_cluster_form": forms.NewClusterForm(initial={
            "identifier": "{}-telemetry-analysis".format(username),
            "size": 1,
        }),
        "active_workers": models.Worker.objects.filter(created_by=request.user)
                                               .order_by("creation_date"),
        "new_worker_form": forms.NewWorkerForm(initial={
            "identifier": "{}-telemetry-worker".format(username),
        }),
    })


@anonymous_csrf
def login(request):
    if request.user.is_authenticated():
        return redirect(dashboard)
    return render(request, 'analysis_service/login.jinja')


@login_required
@anonymous_csrf
@require_POST
def new_cluster(request):
    form = forms.NewClusterForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseBadRequest(form.errors.as_json(escape_html=True))

    provisioning.cluster_start(
        request.user.email,
        form.cleaned_data["identifier"],
        form.cleaned_data["size"],
        form.cleaned_data["public_key"]
    )
    form.save(request.user)
    return HttpResponseRedirect("/")


@login_required
@anonymous_csrf
@require_POST
def new_worker(request):
    form = forms.NewWorkerForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseBadRequest(form.errors.as_json(escape_html=True))

    provisioning.worker_start(
        request.user.email,
        form.cleaned_data["identifier"],
        form.cleaned_data["public_key"]
    )
    form.save(request.user)
    return HttpResponseRedirect("/")
