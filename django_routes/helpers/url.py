from django.contrib.admin.utils import quote as admin_quote
from django.urls import reverse
from django.utils.functional import cached_property


class URLHelper:
    def __init__(self, namespace, model):
        self.namespace = namespace
        self.model = model
        self.opts = model._meta

    def get_pattern(self, action, specific=False):
        if specific:
            return r"^%s/(?P<pk>[-\w]+)/$" % action
        else:
            return "" if action == "index" else r"^%s/$" % action

    def get_name(self, action):
        return "%s_%s_%s_%s" % (
            self.namespace,
            self.opts.app_label,
            self.opts.model_name,
            action,
        )

    def get_url(self, action, *args, **kwargs):
        if action in ("create", "index"):
            return reverse(self.get_name(action))
        url_name = self.get_name(action)
        return reverse(url_name, args=args, kwargs=kwargs)

    @cached_property
    def index_url(self):
        return self.get_url("index")

    @cached_property
    def create_url(self):
        return self.get_url("create")


# Subclasses should define url_helper and permission_helper
class URLFinder:
    def __init__(self, user):
        self.user = user

    def get_edit_url(self, instance):
        if self.permission_helper.user_can_edit_obj(self.user, instance):
            return self.url_helper.get_url("edit", admin_quote(instance.pk))
