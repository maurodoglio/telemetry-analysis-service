from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect

from session_csrf import anonymous_csrf

from analysis_service.base.forms import NewClusterForm
from analysis_service.base.util import cluster


@login_required
def dashboard(request):
    username = request.user.email.split("@")[0]
    return render(request, 'analysis_service/dashboard.jinja', context={
        "new_cluster_form": NewClusterForm(initial={"identifier": "{}-telemetry-analysis".format(username), "size": 1})
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
    form = NewClusterForm(request.POST, request.FILES)
    if form.is_valid():
        with open("/app/aaaaaaaaa.txt", "w") as f: f.write(str(form.cleaned_data))
        return HttpResponseRedirect("/")
    return HttpResponseBadRequest("Invalid form submission")
