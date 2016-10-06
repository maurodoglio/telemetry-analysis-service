"""
WSGI config for atmo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atmo.settings')  # NOQA

from django.core.wsgi import get_wsgi_application

import newrelic.agent
from decouple import config


application = get_wsgi_application()

# Add NewRelic
default_ini = os.path.join(os.path.dirname(__file__), '..', 'newrelic.ini')
newrelic_ini = config('NEW_RELIC_CONFIG_FILE', default=default_ini)
newrelic_license_key = config('NEW_RELIC_LICENSE_KEY', default=None)
if newrelic_ini and newrelic_license_key:
    newrelic.agent.initialize(newrelic_ini)
    application = newrelic.agent.wsgi_application()(application)
