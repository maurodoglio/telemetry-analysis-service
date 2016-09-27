# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
from django.core.management.base import BaseCommand
from django.utils import timezone
from atmo.workers.models import Worker


class Command(BaseCommand):
    help = 'Delete expired workers'

    def handle(self, *args, **options):
        now = timezone.now()

        for worker in Worker.objects.all():
            if worker.end_date >= now:  # the worker is expired
                worker.delete()
