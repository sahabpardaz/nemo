from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="Nemo API",
        default_version='v1',
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


admin.site.site_header = 'Nemo Administration'
admin.site.index_title = f'Welcome To {admin.site.site_header}'
admin.site.site_title = 'Nemo Admin Panel'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('apps.oidc_authentication.urls')),
    path('v1/devops-metrics/', include('apps.devops_metrics.urls'), name='project'),
    path('v1/dashboard/', include('apps.dashboard.urls')),
    path('v1/changelist-reporter/', include('apps.changelist_reporter.urls')),
    path('v1/documentation/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger'),
    path('v1/documentation/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('prometheus/', include('django_prometheus.urls')),  # TODO Issue #12213: Secure the endpoint
] + static(settings.STATIC_SUFFIX, document_root=settings.STATIC_ROOT)
