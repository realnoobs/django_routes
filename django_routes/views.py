# from django.contrib.admin.utils import quote
# from django.contrib.auth.decorators import login_required
# from django.core.exceptions import PermissionDenied
# from django.http.response import HttpResponseRedirect
# from django.utils.decorators import method_decorator
# from django.utils.functional import cached_property
from django.utils.text import capfirst

# from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View

# from django.views.generic.detail import BaseDetailView, SingleObjectMixin
# from django.views.generic.edit import BaseCreateView, BaseDeleteView, BaseUpdateView
# from django.views.generic.list import MultipleObjectMixin

# from django_filters.views import FilterMixin

# from . import consts, messages, utils


class SiteContext(ContextMixin):
    title = ""
    subtitle = ""
    meta_title = None
    meta_description = None

    def get_title(self):
        return capfirst(self.title)

    def get_subtitle(self):
        return capfirst(self.subtitle)

    def get_meta_title(self):
        return self.meta_title or self.get_page_title()

    def get_meta_description(self):
        return self.meta_description or self.get_page_title()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = {
            "view": self,
            "title": self.get_title(),
            "subtitle": self.get_subtitle(),
            "meta_title": self.get_meta_title(),
            "meta_decription": self.get_meta_description(),
        }
        context.update(kwargs)
        return context


class SiteView(ContextMixin, TemplateResponseMixin, View):
    def has_permission(self, request):
        pass

    def dispatch(self, request, *args, **kwargs):
        self.has_permission(request)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
