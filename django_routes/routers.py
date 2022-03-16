"""
Routers provide a convenient and consistent way of automatically
determining the URL conf for your Web.

They are used by simply instantiating a Router class, and then registering
all the required ViewSets with that router.

For example, you might have a `urls.py` that looks something like this:

    router = DefaultRouter()
    router.register(UserViewSet)
    router.register(AccountViewsetGroup)
    urlpatterns = router.urls

"""

from audioop import reverse
from inspect import isclass
from logging import getLogger

from django.core.exceptions import ImproperlyConfigured
from django.urls.conf import include, path
from django.views import View
from django_hookup import core as hookup

from .settings import routers_settings
from .views import BaseView

logger = getLogger("site_routers")


class DefaultIndexView(BaseView):
    template_name = "index.html"


class BaseRouter:

    namespace = None

    def __init__(self):
        self.registry = []
        if self.namespace is None:
            raise ImproperlyConfigured(
                "%s router namespace required!" % self.__class__.__name__,
            )

    def register(self, viewset_class):
        viewset = viewset_class(router=self)
        self.registry.append(viewset)

        # invalidate the urls cache
        if hasattr(self, "_urls"):
            del self._urls

    def get_urls(self):
        """
        Return a list of URL patterns, given the registered viewsets.
        """
        raise NotImplementedError("get_urls must be overridden")

    @property
    def urls(self):
        if not hasattr(self, "_urls"):
            self._urls = self.get_urls()
        return self._urls


class SimpleRouter(BaseRouter):
    def get_urls(self):
        """
        Use the registered viewsets to generate a list of URL patterns.
        """
        urls = []
        for viewset in self.registry:
            urls.append(path("%s" % viewset.get_prefix(), include(viewset.urls)))
        return urls


class DefaultRouter(SimpleRouter):
    """
    The default router extends the SimpleRouter, but also adds in a default
    API root view, and adds format suffix patterns to the URLs.
    """

    index_enabled = True
    index_view_name = "index"
    index_view_class = DefaultIndexView
    site_view_hook_name = "REGISTER_SITE_VIEW"
    site_path_hook_name = "REGISTER_SITE_PATH"

    def each_context(self, request):
        """
        Return a dictionary of variables to put in the template context for
        *every* page in this router site.
        """
        return {
            "site_title": routers_settings.SITE_TITLE,
            "site_header": routers_settings.SITE_HEADER,
            "site_url": reverse("%s_%s" % (self.namespace, self.index_view_name)),
        }

    def get_index_view_class(self):
        """
        Return a basic root view.
        """
        return self.index_view_class

    def get_hooked_views(self):
        # Get registered custom admin view
        funcs = hookup.get_hooks(self.site_view_hook_name)
        urls = []
        for func in funcs:
            url_path, view, name = func()
            if isclass(view):
                if not issubclass(view, View):
                    raise ImproperlyConfigured("%s must be subclass of View" % view)
                route = path(url_path, view.as_view(), name=name)
            elif callable(view):
                route = path(url_path, view, name=name)
            else:
                raise ImproperlyConfigured("%s must be View or function" % view)
            urls.append(route)
        return urls

    def get_hooked_paths(self):
        urls = []
        funcs = hookup.get_hooks(self.site_path_hook_name)
        for func in funcs:
            urls.append(func())
        return urls

    def get_urls(self):
        """
        Generate the list of URL patterns, including a default root view
        for the API, and appending `.json` style format suffixes.
        """
        urls = super().get_urls()
        if self.index_enabled:
            urls += (
                path(
                    "",
                    self.get_index_view_class().as_view(),
                    name=self.index_view_name,
                ),
            )
        urls += self.get_hooked_views()
        urls += self.get_hooked_paths()
        return urls


class AuthenticationRouter(SimpleRouter):
    def get_urls(self):
        try:
            from allauth.urls import urlpatterns

            urls = super().get_urls()
            urls += list(urlpatterns)
            return urls
        except Exception as err:
            logger.error(err)
            return []


class Site(DefaultRouter):

    namespace = "website"
    authentication_router_class = AuthenticationRouter

    def __init__(self):
        super().__init__()

    def index_view(self, request):
        context = self.each_context(request)
        context.update(
            {
                "title": routers_settings.INDEX_TITLE,
            }
        )
        return self.get_index_view_class().as_view(extra_context=context)(request)

    def get_authentication_router(self):
        return self.authentication_router_class()

    def get_authentication_urls(self):
        return self.get_authentication_router().get_urls()

    def get_urls(self):
        """
        Generate the list of URL patterns, including a default root view
        for the API, and appending `.json` style format suffixes.
        """
        urls = super().get_urls()
        urls += self.get_authentication_urls()
        return urls
