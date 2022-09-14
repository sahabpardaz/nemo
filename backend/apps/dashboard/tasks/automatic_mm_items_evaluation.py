import celery

from apps.dashboard import constants
from apps.dashboard.models import MaturityModelItem, Project
from apps.dashboard.evaluators import EvaluatorRunner
from apps.dashboard.evaluators.registry import evaluator_registry


class AutomaticMMItemsEvaluation(celery.Task):
    name = constants.TASK_EVALUATE_AUTOMATIC_MM_ITEMS

    def run(self, *args, **kwargs):
        maturity_model_items = MaturityModelItem.objects.all()
        projects = Project.objects.all()
        evaluator_runner = EvaluatorRunner(projects, maturity_model_items, evaluator_registry)
        evaluator_runner.run()
