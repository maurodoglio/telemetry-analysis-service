from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views import static

from analysis_service.base import views

urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^login/', views.login, name='login'),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^new-cluster/', views.new_cluster),
    url(r'^new-worker/', views.new_worker),
    url(r'^new-scheduled-spark/', views.new_scheduled_spark),

    # contribute.json url
    url(r'^(?P<path>contribute\.json)$', static.serve, {'document_root': settings.ROOT}),

    url(r'', include('django_browserid.urls')),
]
