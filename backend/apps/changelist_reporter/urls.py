from django.urls import path, include
from rest_framework import routers
from rest_framework_extensions.routers import NestedRouterMixin
from apps.changelist_reporter.views import Gitlab, GitlabMergeRequestReport


class NestedDefaultRouter(NestedRouterMixin, routers.DefaultRouter):
    pass


router = NestedDefaultRouter()
router.register('gitlab', Gitlab, basename='gitlab')
router.register('gitlab-merge-request', GitlabMergeRequestReport, basename='gitlab-merge-request')


urlpatterns = [
    path('', include(router.urls)),
]
