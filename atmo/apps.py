from django.apps import AppConfig
from django.conf import settings
from .schedule import register_job_schedule

import session_csrf


class AtmoAppConfig(AppConfig):
    name = 'atmo'

    def ready(self):
        # The app is now ready. Include any monkey patches here.

        # Monkey patch CSRF to switch to session based CSRF. Session
        # based CSRF will prevent attacks from apps under the same
        # domain. If you're planning to host your app under it's own
        # domain you can remove session_csrf and use Django's CSRF
        # library. See also
        # https://github.com/mozilla/sugardough/issues/38
        session_csrf.monkeypatch()

        # Under some circumstances (e.g. when calling collectstatic)
        # REDIS_URL is not available and we can skip the job schedule registration.
        if not getattr(settings, 'REDIS_URL'):
            # Register rq scheduled jobs
            register_job_schedule()
