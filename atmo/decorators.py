# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
from functools import wraps

from django.shortcuts import get_object_or_404
from django.utils.decorators import available_attrs
from guardian.utils import get_403_or_None


def permission_granted(perm, klass, **params):
    """
    A decorator that will raise a 404 if an object with the given
    view parameters isn't found or if the request user doesn't have
    the given permission for the object.

    E.g. for checking if the request user is allowed to change a user
    with the given username::

        @permission_granted('auth.user_change', User)
        def change_user(request, username):
            # can use get() directly since get_object_or_404 was already called
            # in the decorator and would have raised a Http404 if not found
            user = User.objects.get(username=username)
            return render(request, 'change_user.html', context={'user': user})

    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            obj = get_object_or_404(klass, **kwargs)
            get_403_or_None(request, perms=[perm], obj=obj, return_403=True)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
