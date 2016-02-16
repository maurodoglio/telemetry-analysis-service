from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from session_csrf import anonymous_csrf

@login_required
def dashboard(request):
    return render(request, 'analysis_service/dashboard.jinja')

@anonymous_csrf
def login(request):
    if request.user.is_authenticated():
        return redirect(dashboard)
    return render(request, 'analysis_service/login.jinja')