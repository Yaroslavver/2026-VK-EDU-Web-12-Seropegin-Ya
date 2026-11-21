from django.utils.functional import SimpleLazyObject

from .sidebar import get_sidebar


def sidebar(request):
    return {'sidebar': SimpleLazyObject(get_sidebar)}
