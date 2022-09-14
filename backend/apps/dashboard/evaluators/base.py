from abc import ABC, abstractmethod
from typing import Optional
from apps.dashboard.models import EvaluationReport, Project, MaturityModelItem


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, project: Project, maturity_model_item: MaturityModelItem) -> Optional[EvaluationReport]:
        pass
