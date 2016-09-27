# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
from django.core.management import call_command


def delete_clusters():
    call_command('delete_clusters')


def update_clusters_info():
    call_command('update_clusters_info')
