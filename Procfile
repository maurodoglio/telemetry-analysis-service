release: python manage.py migrate
web: gunicorn atmo.wsgi:application --workers 4 --log-file -
worker: python manage.py rqworker default
# django-rq doesn't support rqscheduler retry mode yet
# so we need to use the original startup script
scheduler: rqscheduler --url=$REDIS_URL
