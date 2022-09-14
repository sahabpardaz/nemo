import dataclasses
from rest_framework.exceptions import NotFound
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, action
from rest_condition import Or
from apps.dashboard.permissions import NestedModelsRelatedToProjectPermissions
from apps.dashboard.models import DoryEvaluation
from apps.dashboard.serializers import DoryEvaluationSerializer
from apps.devops_metrics.constants import PROJECT_ID_URL_PARAMETER
from apps.devops_metrics.permissions import NestedApiProjectTokenPermission


@permission_classes((Or(NestedApiProjectTokenPermission, NestedModelsRelatedToProjectPermissions),))
class DoryEvaluationViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = DoryEvaluationSerializer

    def get_queryset(self):
        return DoryEvaluation.objects.filter(project_id=self.kwargs[PROJECT_ID_URL_PARAMETER])

    @action(detail=True, url_path="maturity-item-result/(?P<item_code>.+)", name="dory-evaluation-maturity-item-result")
    def get_maturity_item_dory_result(self, request, item_code, *args, **kwargs):
        dory_evaluation = self.get_object()

        if not dory_evaluation.maturity_item_dory_results_file:
            raise NotFound(detail="Item result for this dory evaluation not found.")

        maturity_item_result = dory_evaluation.get_maturity_item_dory_result(item_code=item_code)
        if maturity_item_result is None:
            raise NotFound(detail=f"Item code {item_code} not found in this dory evaluation.")

        return Response(dataclasses.asdict(maturity_item_result))
