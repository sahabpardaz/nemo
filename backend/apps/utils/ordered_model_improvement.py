
from threading import local as ThreadLocal
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from ordered_model.admin import OrderedInlineMixin


class ImprovedOrderedInlineMixin(OrderedInlineMixin):
    """An improvement on the ordered_model.admin.OrderedInlineMixin
    By default, it could not be used in nested inlines.
    This implementation resolves the related problems.
    """

    def __init__(self, *args, **kwargs):
        # let's define this so there's no chance of AttributeErrors
        self._request_local = ThreadLocal()
        self._request_local.request = None
        super(ImprovedOrderedInlineMixin, self).__init__(*args, **kwargs)

    def _get_request(self):
        return self._request_local.request

    def _set_request(self, request):
        self._request_local.request = request

    def get_fieldsets(self, request, *args, **kwargs):
        # stash the request
        self._set_request(request)
        # call the parent view method with all the original args
        return super(ImprovedOrderedInlineMixin, self).get_fieldsets(request, *args, **kwargs)

    def _get_admin_id_from_request(self, request):
        from django.urls import resolve
        resolved = resolve(request.path_info)
        if 'object_id' in resolved.kwargs:
            return resolved.kwargs['object_id']
        if resolved.args:
            return resolved.args[0]
        return None

    def _get_admin_id(self, obj):
        return self._get_admin_id_from_request(self._get_request())

    #Overriding parent method
    def move_up_down_links(self, obj):
        if not obj.id:
            return ""
        admin_id = self._get_admin_id(obj)

        # Find the fields which refer to the parent model of this inline, and
        # use one of them if they aren't None.
        order_with_respect_to = obj._get_order_with_respect_to_filter_kwargs() or []
        fields = [
            str(value.pk)
            for value in order_with_respect_to.values()
            if value.__class__ is self.parent_model
            and value is not None
            and value.pk is not None
        ]

        if fields:
            model_info = self._get_model_info()
            return render_to_string(
                "ordered_model/admin/order_controls.html",
                {
                    "app_label": model_info["app"],
                    "model_name": model_info["model"],
                    "module_name": model_info["model"],  # backwards compat
                    "object_id": obj.pk,
                    "urls": {
                        "up": reverse(
                            "{admin_name}:{app}_{model}_change_order_inline".format(
                                admin_name=self.admin_site.name, **model_info
                            ),
                            args=[admin_id, obj.id, "up"],
                        ),
                        "down": reverse(
                            "{admin_name}:{app}_{model}_change_order_inline".format(
                                admin_name=self.admin_site.name, **model_info
                            ),
                            args=[admin_id, obj.id, "down"],
                        ),
                        "top": reverse(
                            "{admin_name}:{app}_{model}_change_order_inline".format(
                                admin_name=self.admin_site.name, **model_info
                            ),
                            args=[admin_id, obj.id, "top"],
                        ),
                        "bottom": reverse(
                            "{admin_name}:{app}_{model}_change_order_inline".format(
                                admin_name=self.admin_site.name, **model_info
                            ),
                            args=[admin_id, obj.id, "bottom"],
                        ),
                    },
                    "query_string": self.request_query_string,
                },
            )
        return ""

    move_up_down_links.short_description = _("Move")
