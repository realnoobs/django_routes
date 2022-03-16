import logging

from django.contrib import messages
from django.contrib.admin.utils import quote
from django.shortcuts import redirect

# from django.contrib.auth.decorators import login_required
# from django.core.exceptions import PermissionDenied
# from django.http.response import HttpResponseRedirect
# from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View

# from django.views.generic.detail import BaseDetailView, SingleObjectMixin
# from django.views.generic.edit import BaseCreateView, BaseDeleteView, BaseUpdateView
from django.views.generic.detail import (
    SingleObjectMixin,
    SingleObjectTemplateResponseMixin,
)
from django.views.generic.list import MultipleObjectMixin
from django_filters.views import FilterMixin

# from django_hookup import core as hookup

before_inspect_hook_name = "BEFORE_INSPECT_VIEW_HOOK"
after_inspect_hook_name = "AFTER_INSPECT_VIEW_HOOK"

logger = logging.getLogger("engine")


class SiteContext(ContextMixin):
    title = ""
    subtitle = ""
    meta_title = None
    meta_description = None

    def get_title(self):
        return self.title

    def get_subtitle(self):
        return self.subtitle

    def get_meta_title(self):
        return self.meta_title or self.get_title()

    def get_meta_description(self):
        return self.meta_description or self.get_title()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "view": self,
                "title": self.get_title(),
                "subtitle": self.get_subtitle(),
                "meta_title": self.get_meta_title(),
                "meta_decription": self.get_meta_description(),
            }
        )
        return context


class BaseView(TemplateResponseMixin, SiteContext, View):
    def __init__(self, title="", subtitle="", meta_title=None, meta_description=None, extra_context=None, **kwargs):
        self.title = title
        self.subtitle = subtitle
        self.meta_title = meta_title
        self.meta_description = meta_description
        super().__init__(extra_context=extra_context, **kwargs)

    def has_permission(self, request):
        pass

    def dispatch(self, request, *args, **kwargs):
        self.has_permission(request)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class SiteView(BaseView):
    viewset = None
    model = None

    def __init__(self, viewset, **kwargs):
        self.viewset = viewset
        self.namespace = viewset.namespace
        self.url_helper = viewset.url_helper
        self.permission_helper = viewset.permission_helper
        self.model = getattr(self.viewset, "model", None)
        self.opts = self.model._meta
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "model": self.model,
                "opts": self.opts,
            }
        )
        return context


class ModelView(SiteView):
    model = None

    def __init__(self, viewset, **kwargs):
        self.model = viewset.model
        super().__init__(viewset, **kwargs)


class ListView(FilterMixin, MultipleObjectMixin, ModelView):
    def __init__(self, viewset, **kwargs):
        self.queryset = viewset.get_queryset()
        self.ordering = viewset.get_ordering()
        self.paginator_class = viewset.get_paginator_class()
        self.paginate_by = viewset.paginate_by
        self.paginate_orphans = viewset.paginate_orphans
        self.filterset_class = viewset.get_filterset_class()
        self.filterset_fields = viewset.get_filterset_fields()
        super().__init__(viewset, **kwargs)

    @cached_property
    def index_url(self):
        return self.url_helper.get_url("index")

    def get_template_names(self):
        return self.viewset.get_templates(action="index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)

        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()

        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)
        return self.render_to_response(context)


class InstanceSpecificMixin(SingleObjectMixin):
    """A base view for displaying a single object."""

    def __init__(self, viewset, **kwargs):
        self.queryset = viewset.get_queryset()
        super().__init__(viewset, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_page_subtitle(self):
        return self.object

    @cached_property
    def index_url(self):
        return self.url_helper.get_url("index")

    @cached_property
    def edit_url(self):
        return self.url_helper.get_url("edit", quote(self.object.id))

    @cached_property
    def delete_url(self):
        return self.url_helper.get_url("delete", quote(self.object.id))

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class InspectView(SingleObjectTemplateResponseMixin, InstanceSpecificMixin, ModelView):
    """A view for displaying a object detail."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"action": "inspect"})
        return context

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_inspect_obj(user, self.object) or self.viewset.inspect_public

    def get_template_names(self):
        """
        Return a list of inspect template names defined in viewset.
        """
        return self.viewset.get_inspect_template()


class DeleteView(InspectView):
    """A view for displaying an object deletion view."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"action": "delete"})
        return context

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_delete_obj(user, self.object)

    def get_template_names(self):
        """
        Return a list of delete template names defined in viewset.
        """
        return self.viewset.get_delete_template()

    def get_success_message(self):
        return _("%s deleted!") % self.object

    def post(self, request):
        try:
            self.object.delete()
            msg = self.get_success_message()
            messages.success(request, msg)
        except Exception as err:
            logger.error(err)
            messages.error(request, _("Object deletion failed!"))
        return redirect(self.index_url)
