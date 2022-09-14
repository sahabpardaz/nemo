from django.urls import include, path
from apps.oidc_authentication.views import LogoutCallbackView

urlpatterns = [
    path('logout/', LogoutCallbackView.as_view(), name='logout'),
    path('', include('mozilla_django_oidc.urls')),
]
