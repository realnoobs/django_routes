from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission


class PermissionHelper:
    """
    Provides permission-related helper functions to help determine what a
    user can do with a 'typical' model (where permissions are granted
    model-wide), and to a specific instance of that model.
    """

    def __init__(self, model):
        self.model = model
        self.opts = model._meta

    def get_all_model_permissions(self):
        """
        Return a queryset of all Permission objects pertaining to the `model`
        specified at initialisation.
        """

        return Permission.objects.filter(
            content_type__app_label=self.opts.app_label,
            content_type__model=self.opts.model_name,
        )

    def get_perm_codename(self, action):
        return get_permission_codename(action, self.opts)

    def user_has_specific_permission(self, user, perm_codename):
        """
        Combine `perm_codename` with `self.opts.app_label` to call the provided
        Django user's built-in `has_perm` method.
        """
        return user.has_perm("%s.%s" % (self.opts.app_label, perm_codename))

    def user_has_any_permissions(self, user):
        """
        Return a boolean to indicate whether `user` has any model-wide
        permissions
        """
        for perm in self.get_all_model_permissions().values("codename"):
            if self.user_has_specific_permission(user, perm["codename"]):
                return True
        return False

    def user_can_list(self, user):
        """
        Return a boolean to indicate whether `user` is permitted to access the
        list view for self.model
        """
        return self.user_has_any_permissions(user)

    def user_can_create(self, user):
        """
        Return a boolean to indicate whether `user` is permitted to create new
        instances of `self.model`
        """
        perm_codename = self.get_perm_codename("add")
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_inspect_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'inspect'
        a specific `self.model` instance.
        """
        return self.user_has_any_permissions(user)

    def user_can_edit_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'change'
        a specific `self.model` instance.
        """
        perm_codename = self.get_perm_codename("change")
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_delete_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'delete'
        a specific `self.model` instance.
        """
        perm_codename = self.get_perm_codename("delete")
        return self.user_has_specific_permission(user, perm_codename)

    def user_can_unpublish_obj(self, user, obj):
        return False

    def user_can_copy_obj(self, user, obj):
        return False

    def user_is_owner_or_admin(self, user, obj, owner_field):
        obj_owner = getattr(obj, owner_field, None)
        if (obj_owner and obj_owner is user) or user.is_superadmin:
            return True
        else:
            return False

    def user_is_member(self, group_name):
        """Return a boolean to indicate whether `user` is a member of a
        specific `group` instance."""
        return False
