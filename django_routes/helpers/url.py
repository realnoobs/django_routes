from django.contrib.admin.utils import quote as admin_quote
from django.urls import reverse
from django.utils.functional import cached_property


class URLHelper:

    basename = "webrun"

    def __init__(self, model):
        self.model = model
        self.opts = model._meta

    def _get_action_url_pattern(self, action):
        if action == "index":
            return r"^%s/%s/$" % (
                self.opts.app_label,
                self.opts.model_name,
            )
        return r"^%s/%s/%s/$" % (
            self.opts.app_label,
            self.opts.model_name,
            action,
        )

    def _get_object_specific_action_url_pattern(self, action):
        return r"^%s/%s/%s/(?P<pk>[-\w]+)/$" % (self.opts.app_label, self.opts.model_name, action)

    def get_basename(self):
        return self.basename

    def get_action_url_pattern(self, action):
        if action in ("create", "choose_parent", "index"):
            return self._get_action_url_pattern(action)
        return self._get_object_specific_action_url_pattern(action)

    def get_action_url_name(self, action):
        return "%s_%s_%s_%s" % (self.get_basename(), self.opts.app_label, self.opts.model_name, action)

    def get_action_url(self, action, *args, **kwargs):
        if action in ("create", "index"):
            return reverse(self.get_action_url_name(action))
        url_name = self.get_action_url_name(action)
        return reverse(url_name, args=args, kwargs=kwargs)

    @cached_property
    def index_url(self):
        return self.get_action_url("index")

    @cached_property
    def create_url(self):
        return self.get_action_url("create")


# Subclasses should define url_helper and permission_helper
class URLFinder:
    def __init__(self, user):
        self.user = user

    def get_edit_url(self, instance):
        if self.permission_helper.user_can_edit_obj(self.user, instance):
            return self.url_helper.get_action_url("edit", admin_quote(instance.pk))
