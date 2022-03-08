from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model

from .helpers import ButtonHelper, PermissionHelper, URLHelper


class GenericViewSet:

    icon = ""
    model = None
    menu_label = None
    menu_icon = None
    menu_order = None
    # Helper class

    url_helper_class = URLHelper
    button_helper_class = ButtonHelper
    permission_helper_class = PermissionHelper
    template_namespace = None

    def __init__(self, parent=None):
        """Don't allow initialisation unless self.model is set to a valid model"""
        if not self.model or not issubclass(self.model, Model):
            raise ImproperlyConfigured(
                "The model attribute on your '%s' class must be set, and "
                "must be a valid Django model." % self.__class__.__name__
            )
        self.parent = parent
        self.opts = self.model._meta
        self.url_helper = self.get_url_helper_class()(self.model)
        self.permission_helper = self.get_permission_helper_class()(self.model)

    def get_queryset(self, request):
        """Returns a QuerySet of all model instances."""
        qs = self.model._default_manager.get_queryset()
        return qs

    def get_permission_helper_class(self):
        """Returns a permission_helper class to help with permission-based logic."""
        return self.permission_helper_class

    def get_permission_helper(self):
        return self.permission_helper_class(self.model)

    def get_button_helper_class(self):
        """Returns a ButtonHelper class to help generate buttons for the given model."""
        return self.button_helper_class

    def get_button_helper(self, view, request):
        return self.button_helper_class(view, request)

    def get_url_helper_class(self):
        return self.url_helper_class

    def get_url_helper(self):
        return self.url_helper_class(self.model)

    def get_menu_label(self):
        """Returns the label text to be used for the menu item."""
        return self.menu_label or self.opts.verbose_name_plural.title()

    def get_menu_icon(self):
        return self.menu_icon

    def get_menu_order(self):
        """
        Returns the 'order' to be applied to the menu item. 000 being first
        place. Where ViewSetGroup is used, the menu_order value should be
        applied to that, and any ModelAdmin classes added to 'items'
        attribute will be ordered automatically, based on their order in that
        sequence.
        """
        return self.menu_order or 999

    def get_templates(self, action="index"):
        """
        Utility function that provides a list of templates to try for a given
        view, when the template isn't overridden by one of the template
        attributes on the class.
        """
        namespace = self.get_template_namespace()
        app_label = self.opts.app_label.lower()
        model_name = self.opts.model_name.lower()
        if namespace:
            return [
                "%s/%s/%s/%s.html" % (namespace, app_label, model_name, action),
                "%s/%s/%s.html" % (namespace, app_label, action),
                "%s/%s.html" % (namespace, action),
            ]
        else:
            return [
                "%s/%s/%s.html" % (app_label, model_name, action),
                "%s/%s.html" % (app_label, action),
                "%s.html" % (action),
            ]

    def get_template_namespace(self):
        return self.template_namespace

    def get_urls(self):
        """Utilised by 'register_webapp_urls' hook to register urls to router."""
        return tuple()

    def has_view(self, view_name):
        return hasattr(self, view_name)
