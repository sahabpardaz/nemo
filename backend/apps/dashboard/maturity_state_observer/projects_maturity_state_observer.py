from typing import List, Optional

from celery.utils.log import get_task_logger

from apps.dashboard.models import Project, ProjectMaturityItemState
from apps.dashboard.models.project_maturity_state import ProjectMaturityState
from apps.dashboard.project_retrieve_utils import get_project_maturity_state
from apps.utils.key_value_storage import KeyValueStorage
from apps.utils.key_value_storage import InMemoryStorage

logger = get_task_logger(__name__)


class ProjectsMaturityStateObserver:
    def __init__(self, storage: KeyValueStorage = None) -> None:
        """

        Args:
            storage (KeyValueStorage, optional): A KeyValueStorage. Defaults to InMemoryStorage.\n
            Note that the storage should be persistent, at least in the period between consecutive observations. Otherwise it will not detect possible changes to the maturity state.
        """
        if storage is None:
            self.storage = InMemoryStorage()
        else:
            self.storage = storage

    def update_project_maturity_states(self) -> None:
        for project in Project.objects.all():
            self._update_project_state(project)

    def _update_project_state(self, project: Project) -> None:
        maturity_state = get_project_maturity_state(project)
        self.storage.put(project.pk, maturity_state)

    def get_newly_failed_items(self, project: Project) -> List[ProjectMaturityItemState]:
        maturity_state_old = self.storage.get(project.pk)
        if maturity_state_old is None:
            return []
        maturity_state_new = get_project_maturity_state(project)
        newly_failed_items = []
        try:
            for level_new in maturity_state_new.maturity_level_states:
                for item_new in level_new.maturity_item_states:
                    if not item_new.is_passed:
                        code = item_new.maturity_item.code
                        item_old = self._find_item_by_code(maturity_state_old, code)
                        if item_old is None or item_old.is_passed:
                            newly_failed_items.append(item_new)
        except AttributeError as e:
            logger.error("Encountered AttributeError while working with the cached ProjectMaturityState. "
                         "It may be because of a schema change in the ProjectMaturityState class (or its children). "
                         "If this is the case, just skip this error. "
                         "Otherwise, or if this error is seen again in the future, check the error details.\n"
                         f"Error message: {str(e)}")
        return newly_failed_items

    def _find_item_by_code(self, maturity_state: ProjectMaturityState, code: str) -> Optional[ProjectMaturityItemState]:
        for l in maturity_state.maturity_level_states:
            for i in l.maturity_item_states:
                if i.maturity_item.code == code:
                    return i
        return None
