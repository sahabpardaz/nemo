import json
import logging
from itertools import groupby
from typing import Tuple, Union
from abc import abstractmethod, ABC
import requests
from requests.auth import HTTPBasicAuth
from rest_framework import serializers
from apps.dashboard.models import (
    SonarProject,
    CoverageReport,
)
from apps.dashboard.serializers import CoverageReportSerializer
from apps.dashboard.data_collectors.base import DataCollector
from apps.dashboard.data_collectors.registry import register

logger = logging.getLogger(__name__)


class SonarTestCoverageCollectorBase(DataCollector, ABC):
    MAX_ATTEMPTS_TO_GET_COVERAGE = 3
    MULTI_VERSION_DELIMITER = ','

    class _MaxRetriesExceededToGetVersion(Exception):
        pass

    @abstractmethod
    def get_coverage_metric_key(self):
        raise NotImplementedError

    @abstractmethod
    def get_lines_to_cover_metric_key(self):
        raise NotImplementedError

    @abstractmethod
    def get_metric_value(self, measures, metric_key):
        raise NotImplementedError

    @abstractmethod
    def _get_coverage_type(self):
        raise NotImplementedError

    def get_average_coverage(self, sonar_projects):
        summed_up_coverage = 0
        total_lines_to_cover = 0
        for sonar_project in sonar_projects:
            response = self.get_project_details_from_sonar(sonar_project)
            if not response.ok:
                logger.error(
                    f"Error getting metrics from sonar. Status code: {response.status_code}\n"
                    f"Response: {response.text}")
                return None

            response_json = json.loads(response.text)
            component = response_json.get('component')
            measures = component.get('measures')
            if len(measures) > 0:
                coverage = self.get_metric_value(
                    measures, self.get_coverage_metric_key())
                coverage = float(coverage)
                lines_to_cover = self.get_metric_value(
                    measures, self.get_lines_to_cover_metric_key())
                lines_to_cover = int(lines_to_cover)
                summed_up_coverage += coverage * lines_to_cover
                total_lines_to_cover += lines_to_cover

        return 0 if total_lines_to_cover == 0 else summed_up_coverage / total_lines_to_cover

    @staticmethod
    def get_auth(sonar_project):
        if sonar_project.auth_token:
            return HTTPBasicAuth(username=sonar_project.auth_token, password='')
        return None

    @staticmethod
    def get_project_version_from_sonar(sonar_projects) -> str:
        """
        Returns joined sonar projects versions with delimiter by order of sonar_project id
        """
        versions_inorder = []
        for sonar_project in sorted(sonar_projects, key=lambda x: x.id):
            url = f"{sonar_project.api_base_url}/components/show"
            params = {
                'component': sonar_project.project_key,
                'branch': sonar_project.coverage_branch,
            }
            auth = SonarTestCoverageCollectorBase.get_auth(sonar_project)
            response = requests.get(
                url=url,
                params=params,
                auth=auth,
            )
            response.raise_for_status()
            sonar_version = json.loads(response.text)['component'].get('version')
            versions_inorder.append(f"{sonar_project.project_key}:{sonar_version}")
        return SonarTestCoverageCollectorBase.MULTI_VERSION_DELIMITER.join(versions_inorder)

    def get_project_details_from_sonar(self, sonar_project):
        url = f"{sonar_project.api_base_url}/measures/component"
        params = {
            'metricKeys': f'{self.get_coverage_metric_key()},{self.get_lines_to_cover_metric_key()}',
            'component': f'{sonar_project.project_key}',
            'branch': sonar_project.coverage_branch,
        }
        auth = SonarTestCoverageCollectorBase.get_auth(sonar_project)
        response = requests.get(url=url,
                                params=params,
                                auth=auth)
        return response

    def collect_and_save_data(self):
        all_sonar_projects = SonarProject.objects.order_by('nemo_project_id')
        all_sonar_projects_grouped = groupby(all_sonar_projects, lambda p: p.nemo_project_id)
        for project_id, sonar_projects in all_sonar_projects_grouped:
            sonar_projects = list(sonar_projects)
            try:
                coverage, version = self.get_coverage_and_version(sonar_projects)
                self.save_coverage_report(project_id, coverage, version)
            except self._MaxRetriesExceededToGetVersion:
                logger.warning(
                    f"Reached maximum retries ({self.MAX_ATTEMPTS_TO_GET_COVERAGE}) to get unique versions from sonar"
                )
            except Exception:
                logger.exception(
                    f"Something wrong happened in collecting/saving "
                    f"sonar coverage with type {self._get_coverage_type()} for project {project_id}"
                )

    def save_coverage_report(self, project_id, value, version: str):
        try:
            CoverageReportSerializer.validate_and_save(
                data={
                    'version': version,
                    'coverage_type': self._get_coverage_type(),
                    'value': value,
                },
                context={
                    'project_id': project_id,
                }
            )
        except serializers.ValidationError as validation_error:
            version_field_error_codes = [error.code for error in validation_error.detail.get('version')]
            if not (
                len(version_field_error_codes) == 1 and
                CoverageReport.DUPLICATE_COVERAGE_REPORT_ERROR_CODE in version_field_error_codes
            ):
                raise

    def get_coverage_and_version(self, sonar_projects) -> Tuple[Union[None, int, float], str]:
        """
        This method solves this scenario:
            Project X reports coverage with value 50 and versions [1.1.0, 1.0.0]
            Nemo gets version list with values [1.1.0, 1.0.0]
            Project X reports another coverage with value 60 and versions: [2.0.0, 1.1.0]
            Nemo gets coverage value 60
            Nemo incorrectly saves CoverageReport with value 60 and versions [1.1.0, 1.0.0]
        """
        attempts = 0
        while attempts < self.MAX_ATTEMPTS_TO_GET_COVERAGE:
            attempts += 1
            version_before = self.get_project_version_from_sonar(sonar_projects)
            coverage = self.get_average_coverage(sonar_projects)
            version_after = self.get_project_version_from_sonar(sonar_projects)
            if version_after == version_before:
                return coverage, version_after
        raise self._MaxRetriesExceededToGetVersion


@register()
class OverallTestCoverageCollector(SonarTestCoverageCollectorBase):
    def get_coverage_metric_key(self):
        return 'coverage'

    def get_lines_to_cover_metric_key(self):
        return 'lines_to_cover'

    def get_metric_value(self, measures, metric_key):
        for measure in measures:
            if measure.get('metric') == metric_key:
                return measure.get('value')
        logger.warning(
            f'No such metric ({metric_key}) found in the given measures.')
        return "0"

    def _get_coverage_type(self):
        return CoverageReport.TYPE_OVERALL


@register()
class IncrementalTestCoverageCollector(SonarTestCoverageCollectorBase):
    def get_coverage_metric_key(self):
        return 'new_coverage'

    def get_lines_to_cover_metric_key(self):
        return 'new_lines_to_cover'

    def get_metric_value(self, measures, metric_key):
        for measure in measures:
            if measure.get('metric') == metric_key:
                return measure.get('periods')[0].get('value')
        logger.warning(
            f'No such metric ({metric_key}) found in the given measures.')
        return "0"

    def _get_coverage_type(self):
        return CoverageReport.TYPE_INCREMENTAL
