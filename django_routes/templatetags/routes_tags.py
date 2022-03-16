from django.apps import apps
from django.db import models
from django.template import Library

from django_routes.helpers import URLHelper

register = Library()

_url_helper_registry = {}


@register.simple_tag(takes_context=True)
def object_url(context, namespace, instance, **kwargs):
    if isinstance(instance, models.Model):
        model = instance.__class__
    elif isinstance(instance, str):
        model = apps.get_model(instance)
    else:
        model = instance
    opts = model._meta
    slug = "%s_%s" % (opts.app_label, opts.model_name)
    helper = _url_helper_registry.get(slug, None)
    if not helper:
        helper = URLHelper(namespace, model)
        _url_helper_registry[slug] = helper
    return helper.get_url(**kwargs)
