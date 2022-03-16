from django.contrib.admin.utils import quote
from django.utils.encoding import force_str
from django.utils.translation import gettext as _


class ButtonHelper:

    default_button_classnames = ["button"]
    add_button_classnames = ["bicolor", "icon", "icon-plus"]
    inspect_button_classnames = []
    edit_button_classnames = []
    delete_button_classnames = ["no"]

    def __init__(self, viewset, request):
        self.viewset = viewset
        self.request = request
        self.model = viewset.model
        self.opts = viewset.opts
        self.verbose_name = force_str(self.opts.verbose_name)
        self.verbose_name_plural = force_str(self.opts.verbose_name_plural)
        self.permission_helper = viewset.permission_helper
        self.url_helper = viewset.url_helper

    def finalise_classname(self, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        combined = self.default_button_classnames + classnames_add
        finalised = [cn for cn in combined if cn not in classnames_exclude]
        return " ".join(finalised)

    def add_button(self, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.add_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            "url": self.url_helper.create_url,
            "label": _("Add %s") % self.verbose_name,
            "classname": cn,
            "title": _("Add a new %s") % self.verbose_name,
        }

    def inspect_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.inspect_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            "url": self.url_helper.get_action_url("inspect", quote(pk)),
            "label": _("Inspect"),
            "classname": cn,
            "title": _("Inspect this %s") % self.verbose_name,
        }

    def edit_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            "url": self.url_helper.get_action_url("edit", quote(pk)),
            "label": _("Edit"),
            "classname": cn,
            "title": _("Edit this %s") % self.verbose_name,
        }

    def delete_button(self, pk, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.delete_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            "url": self.url_helper.get_action_url("delete", quote(pk)),
            "label": _("Delete"),
            "classname": cn,
            "title": _("Delete this %s") % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None, classnames_exclude=None):
        if exclude is None:
            exclude = []
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        ph = self.permission_helper
        usr = self.request.user
        pk = getattr(obj, self.opts.pk.attname)
        btns = []
        if "inspect" not in exclude and ph.user_can_inspect_obj(usr, obj):
            btns.append(self.inspect_button(pk, classnames_add, classnames_exclude))
        if "edit" not in exclude and ph.user_can_edit_obj(usr, obj):
            btns.append(self.edit_button(pk, classnames_add, classnames_exclude))
        if "delete" not in exclude and ph.user_can_delete_obj(usr, obj):
            btns.append(self.delete_button(pk, classnames_add, classnames_exclude))
        return btns
