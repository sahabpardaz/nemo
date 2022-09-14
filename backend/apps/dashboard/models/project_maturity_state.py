from typing import List, Optional
from dataclasses import dataclass
from apps.dashboard.models import Project, EvaluationReport
from apps.dashboard.models.goal import Goal
from apps.dashboard.models.maturity_model import MaturityModelItem, MaturityModelLevel


@dataclass
class ProjectMaturityItemState:
    maturity_item: MaturityModelItem
    is_disabled: bool
    is_passed: Optional[bool] = None
    latest_evaluation_report: Optional[EvaluationReport] = None
    failure_reason: Optional[str] = None
    closest_goal: Optional[Goal] = None
    latest_pending_evaluation_request_id: Optional[int] = None
    latest_pending_toggle_request_id: Optional[int] = None


@dataclass
class ProjectMaturityLevelState:
    maturity_level: MaturityModelLevel
    maturity_item_states: List[ProjectMaturityItemState]


@dataclass
class ProjectMaturityState:
    project: Project
    maturity_level_states: List[ProjectMaturityLevelState]

    @property
    def achieved_level_index(self) -> Optional[int]:
        achieved_level_index = None
        for index, level in enumerate(self.maturity_level_states):
            if all(item.is_passed or item.is_disabled for item in level.maturity_item_states):
                achieved_level_index = index
            else:
                break
        return achieved_level_index

    @property
    def passed_enabled_items_count(self) -> int:
        return len([i for l in self.maturity_level_states for i in l.maturity_item_states
                    if not i.is_disabled and i.is_passed])
