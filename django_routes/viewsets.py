from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.db.models import Model
from django.urls import path, re_path
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django_tables2.tables import Table, table_factory

from .helpers import ButtonHelper, PermissionHelper, URLHelper
from .views import InspectView, ListView

login_required_m = method_decorator(login_required)


class BaseViewSet:
    icon = ""
    prefix = None
    menu_label = None
    menu_icon = None
    menu_order = None

    def __init__(self, router=None):
        """Don't allow initialisation unless self.model is set to a valid model"""
        self.router = router

    @property
    def urls(self):
        return self.get_urls()

    def get_prefix(self):
        return "%s" % self.prefix

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

    def get_urls(self):
        """Utilised by 'register_webapp_urls' hook to register urls to router."""
        return []

    def has_view(self, view_name):
        return hasattr(self, view_name)


class BaseFormViewset:

    form_view_extra_css = []
    form_view_extra_js = []
    form_fields_exclude = []
    prepopulated_fields = {}
    success_url_name = "index"

    def get_success_url(self):
        if (self.success_url_name == "index" and self.has_view("index_view")) or (
            self.success_url_name == "create" and self.has_view("index_view")
        ):
            return self.url_helper.get_action_url(self.success_url_name)
        if (self.success_url_name == "edit" and self.has_view("index_view")) or (
            self.success_url_name == "inspect" and self.has_view("index_view")
        ):
            return self.url_helper.get_action_url(self.success_url_name, pk=self.pk)
        else:
            raise ImproperlyConfigured("success_url_name `index`, `create`, `edit`, `inspect`")

    def get_form_view_extra_css(self):
        return self.form_view_extra_css

    def get_form_view_extra_js(self):
        return self.form_view_extra_js


class ModelViewSet(BaseViewSet):
    model = None
    # Helper class
    url_helper_class = URLHelper
    button_helper_class = ButtonHelper
    permission_helper_class = PermissionHelper
    template_namespace = None

    def __init__(self, router=None):
        """Don't allow initialisation unless self.model is set to a valid model"""
        super().__init__(router=router)
        if not self.model or not issubclass(self.model, Model):
            raise ImproperlyConfigured(
                "The model attribute on your '%s' class must be set, and "
                "must be a valid Django model." % self.__class__.__name__
            )
        self.opts = self.model._meta
        self.namespace = self.router.namespace
        self.url_helper = self.get_url_helper_class()(self.namespace, self.model)
        self.permission_helper = self.get_permission_helper_class()(self.model)

    def get_queryset(self):
        """Returns a QuerySet of all model instances."""
        qs = self.model._default_manager.get_queryset()
        return qs

    def get_permission_helper_class(self):
        """Returns a permission_helper class to help with permission-based logic."""
        return self.permission_helper_class

    def get_permission_helper(self):
        return self.permission_helper

    def get_button_helper_class(self):
        """Returns a ButtonHelper class to help generate buttons for the given model."""
        return self.button_helper_class

    def get_button_helper(self):
        return self.button_helper

    def get_url_helper_class(self):
        return self.url_helper_class

    def get_url_helper(self):
        return self.url_helper

    def get_prefix(self):
        return "%s/%s/" % (str(self.opts.app_label).replace("_", "-"), self.opts.model_name)

    def get_templates(self, action="index"):
        """
        Utility function that provides a list of templates to try for a given
        view, when the template isn't overridden by one of the template
        attributes on the class.
        """
        namespace = self.router.namespace
        app_label = self.opts.app_label.lower()
        model_name = self.opts.model_name.lower()
        templates = [
            "%s/%s/%s/%s.html" % (namespace, app_label, model_name, action),
            "%s/%s/%s.html" % (namespace, model_name, action),
            "%s/%s.html" % (namespace, action),
        ]
        return templates


class ListViewSetMixin(ModelViewSet):
    index_public = True
    index_title = None
    index_view_extra_css = list()
    index_view_extra_js = list()
    index_view_class = ListView
    index_template_name = None

    paginate_by = 20
    paginate_orphans = 0
    paginator_class = Paginator
    filterset_fields = None
    filterset_class = None
    select_related = False
    ordering = ("pk",)

    def get_queryset(self):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site.
        """
        qs = super().get_queryset()
        ordering = self.get_ordering()
        if ordering:
            qs = qs.order_by(*ordering)
        select_related = self.get_select_related()
        if select_related:
            qs.select_related(*select_related)
        return qs

    def get_filterset_class(self):
        """Return self.filterset class, if None load default FilterView"""
        return self.filterset_class

    def get_ordering(self):
        return self.ordering or ()

    def get_select_related(self):
        return self.select_related

    def get_paginate_by(self):
        return self.paginate_by

    def get_paginator_class(self):
        return self.paginator_class

    def get_index_view_extra_css(self):
        css = []
        css.extend(self.index_view_extra_css)
        return css

    def get_index_view_extra_js(self):
        return self.index_view_extra_js

    def get_filterset_fields(self):
        """
        Returns a sequence containing the fields to be displayed as filters in the right sidebar
        in the list view.
        """
        return self.filterset_fields

    def get_index_title(self):
        return self.index_title or self.opts.verbose_name_plural.title()

    def get_index_template(self):
        return self.index_template_name or self.get_templates("index")

    def index_view(self, request):
        self.request = request
        kwargs = {
            "viewset": self,
            "title": self.get_index_title(),
        }
        view_class = self.index_view_class
        return view_class.as_view(**kwargs)(request)

    def get_urls(self):
        """
        Append urls to generic viewsets.
        """
        urls = super().get_urls()
        urls = urls + [
            path(
                self.url_helper.get_pattern("index"),
                self.index_view,
                name=self.url_helper.get_name("index"),
            ),
        ]
        return urls


class InspectViewSetMixin(BaseViewSet):

    inspect_public = True
    inspect_view_fields = []
    inspect_view_fields_exclude = []
    inspect_view_extra_css = []
    inspect_view_extra_js = []
    inspect_view_class = InspectView
    inspect_template_name = None

    def inspect_view(self, request, pk):
        self.request = request
        kwargs = {
            "viewset": self,
            "title": self.get_inspect_title(),
        }
        view_class = self.inspect_view_class
        return view_class.as_view(**kwargs)(request, pk=pk)

    def get_inspect_title(self):
        return self.index_title or "%s Detail" % self.opts.verbose_name.title()

    def get_inspect_template(self):
        return self.inspect_template_name or self.get_templates("inspect")

    def get_inspect_view_extra_css(self):
        return self.inspect_view_extra_css

    def get_inspect_view_extra_js(self):
        return self.inspect_view_extra_js

    def get_inspect_view_fields(self):
        """
        Return a list of field names, indicating the model fields that
        should be displayed in the 'inspect' view. Returns the value of the
        'inspect_view_fields' attribute if populated, otherwise a sensible
        list of fields is generated automatically, with any field named in
        'inspect_view_fields_exclude' not being included.
        """
        if not self.inspect_view_fields:
            found_fields = []
            for f in self.model._meta.get_fields():
                if f.name not in self.inspect_view_fields_exclude:
                    if f.concrete and (not f.is_relation or (not f.auto_created and f.related_model)):
                        found_fields.append(f.name)
            return found_fields
        return self.inspect_view_fields

    def get_urls(self):
        """
        Append urls to generic viewsets.
        """
        urls = super().get_urls()
        urls = urls + [
            re_path(
                self.url_helper.get_pattern("inspect", specific=True),
                self.inspect_view,
                name=self.url_helper.get_name("inspect"),
            ),
        ]
        return urls


class TableViewSetMixin(ListViewSetMixin):

    list_export = tuple()
    table_class = None
    table_template = "shared/table.html"
    table_add_buttons = None
    list_display = None
    list_display_exclude = None
    empty_value_display = "-"

    def get_table_class(self, request):
        table_class = self.table_class
        if not table_class:
            table_class = table_factory(
                table=Table,
                model=self.model,
                fields=self.get_list_display(request),
                exclude=self.get_list_display_exclude(request),
            )
        return table_class

    def get_table_kwargs(self, request):
        """
        Return a table object to use. The table has automatic support for
        sorting and pagination.
        """
        return {"template_name": self.get_table_template()}

    def get_table_template(self):
        return self.table_template

    def get_list_display(self, request):
        """
        Return a sequence containing the fields/method output
        to be displayed in the column view.
        """
        return self.list_display

    def get_list_display_exclude(self, request):
        """
        Return a sequence containing the fields/method output
        to be displayed in the list view.
        """
        return self.list_display_exclude

    def get_list_display_add_buttons(self, request):
        """
        Return the name of the field/method from list_display where
        action buttons should be added. Defaults to the first
        item from get_list_display()
        """
        return self.list_display_add_buttons or self.get_list_display(request)[0]

    def get_list_export(self, request):
        """
        Return a sequence containing the fields/method output to be displayed in spreadsheet exports.
        """
        return self.list_export

    def get_empty_value_display(self, field_name=None):
        """Return the empty_value_display value defined on ModelAdmin"""
        return mark_safe(self.empty_value_display)

    def get_extra_attrs_for_row(self, obj, context):
        """
        Return a dictionary of HTML attributes to be added to the `<tr>`
        element for the suppled `obj` when rendering the results table in
        `index_view`. `data-object-pk` is already added by default.
        """
        return {}

    def get_extra_class_names_for_field_col(self, obj, field_name):
        """
        Return a list of additional CSS class names to be added to the table
        cell's `class` attribute when rendering the output of `field_name` for
        `obj` in `index_view`.

        Must always return a list.
        """
        return []

    def get_extra_attrs_for_field_col(self, obj, field_name):
        """
        Return a dictionary of additional HTML attributes to be added to a
        table cell when rendering the output of `field_name` for `obj` in
        `index_view`.

        Must always return a dictionary.
        """
        return {}


class ReadOnlyViewSet(InspectViewSetMixin, ListViewSetMixin):
    pass
