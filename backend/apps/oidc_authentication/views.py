from django.http.response import HttpResponseRedirect
from django.contrib.auth import logout
from django.utils.http import urlencode
from django.conf import settings
from rest_framework.views import APIView


class LogoutCallbackView(APIView):
    def get(self, request, *args, **kwargs):
        logout(request)
        return_url = self.get_logout_url(request)
        return HttpResponseRedirect(redirect_to=return_url)

    def get_logout_url(self, request):
        redirect_uri = request.build_absolute_uri('/')
        redirect_uri_parameter = urlencode({'redirect_uri': redirect_uri})
        return f'{settings.OIDC_ROOT_URL}/realms/{settings.OIDC_REALM}'\
            f'/protocol/openid-connect/logout?{redirect_uri_parameter}'
