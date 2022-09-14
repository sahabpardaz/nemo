import requests
import dateutil
from rest_framework import serializers
from celery.utils.log import get_task_logger
from requests.exceptions import HTTPError
from backend.celery import app
from apps.devops_metrics.serializers import ChangeListSerializer
from apps.changelist_reporter.constants import GITLAB_API_PAGINATION_PER_PAGE, GITLAB_BASE_URL
from apps.changelist_reporter.models import ChangeListReport


logger = get_task_logger(__name__)


@app.task(name="Get changelists from gitlab and Report them to devopsmetrics")
def get_gitlab_changelists_and_report_to_devopsmetrics(nemo_project_id,
                                                       gitlab_project_id,
                                                       gitlab_project_default_branch,
                                                       gitlab_project_token,
                                                       gitlab_project_merge_request_merged_after=None):
    try:
        all_merge_requests = get_all_merge_requests_from_gitlab(gitlab_project_id,
                                                                gitlab_project_default_branch,
                                                                gitlab_project_token)
    except HTTPError as http_error:
        logger.exception(f'An error occured when trying to get merge requests from Gitlab', http_error)
        return

    change_list_reports = []
    for merge_request in all_merge_requests:
        change_list_reports.append(
            ChangeListReport.from_gitlab_merge_request_json(merge_request))

    if gitlab_project_merge_request_merged_after is not None:
        change_list_reports = filter_change_list_reports_merged_after_specific_time(change_list_reports,
                                                                                    gitlab_project_merge_request_merged_after)

    status_of_reported_change_lists_to_devopsmetrics = report_to_devopsmetrics(
        nemo_project_id,
        change_list_reports
    )
    logger.debug(f"Details of project {nemo_project_id} reported changelists : {status_of_reported_change_lists_to_devopsmetrics}")

    return f"{len(status_of_reported_change_lists_to_devopsmetrics)} changelists was reported to project {nemo_project_id}"


def filter_change_list_reports_merged_after_specific_time(change_list_reports_to_filter, specific_time):
    filtered_change_list_reports = []
    for change_list_report in change_list_reports_to_filter:
        if change_list_report.merge_time >= dateutil.parser.parse(specific_time):
            filtered_change_list_reports.append(change_list_report)
    return filtered_change_list_reports


def report_to_devopsmetrics(nemo_project_id, change_lists):
    for change_list in change_lists:
        data = {
            'title': change_list.title,
            'change_list_id': change_list.id,
            'commit_hash': change_list.commit_sha,
            "time": change_list.merge_time,
        }
        saving_status = "FAILED"
        saving_details = None
        try:
            ChangeListSerializer.validate_and_save(
                data=data,
                context={
                    'project_id': nemo_project_id
                }
            )
            saving_status = "SUCCESSFUL"
        except ValueError:
            logger.exception(
                "Some errors happened in saving changelist."
                f"(details: {data})"
            )
        except serializers.ValidationError as e:
            saving_details = e.detail

        change_list.report = {
            "status": saving_status,
            "details": saving_details
        }

    return change_lists


@app.task(name="Handle gitlab merge request report")
def add_gitlab_merge_request_report(nemo_project_id,
                                    gitlab_project_token,
                                    gitlab_project_id,
                                    gitlab_project_default_branch,
                                    gitlab_merge_request_commit_hash):
    try:
        all_merge_requests = get_all_merge_requests_from_gitlab(gitlab_project_id,
                                                                gitlab_project_default_branch,
                                                                gitlab_project_token)
    except HTTPError as http_error:
        logger.exception(f'An error occured when trying to get merge requests from Gitlab, ', http_error)
        return

    for merge_request in all_merge_requests:
        if merge_request.get('merge_commit_sha') == gitlab_merge_request_commit_hash or \
           merge_request.get('squash_commit_sha') == gitlab_merge_request_commit_hash or \
           merge_request.get('sha') == gitlab_merge_request_commit_hash:

            merge_request_of_specified_commit_hash = merge_request
            break
    else:
        return f"Merge request related to {gitlab_merge_request_commit_hash}" \
               f"for project {nemo_project_id} not found."

    change_list = ChangeListReport.from_gitlab_merge_request_json(merge_request_of_specified_commit_hash)

    report_to_devopsmetrics(nemo_project_id, [change_list])

    return f"Changelist {change_list.id} of project {nemo_project_id} was reported to DevOpsMetrics"


def get_all_merge_requests_from_gitlab(gitlab_project_id,
                                       gitlab_project_default_branch,
                                       gitlab_project_token):
    """
    Returns:
        List of Gitlab merge request(json)
    Raises:
        requests.exceptions.HTTPError: if the HTTP request returned an unsuccessful status code.
    """
    merge_requests = []
    next_page = 1
    while next_page:
        gitlab_api_merge_requests_url = f"{GITLAB_BASE_URL}/api/v4/projects/{gitlab_project_id}/merge_requests"
        response = requests.get(gitlab_api_merge_requests_url,
                                params={
                                    "target_branch": gitlab_project_default_branch,
                                    "state": "merged",
                                    "scope": "all",
                                    "per_page": GITLAB_API_PAGINATION_PER_PAGE,
                                    "page": next_page
                                },
                                headers={"PRIVATE-TOKEN": gitlab_project_token})
        response.raise_for_status()
        merge_requests += response.json()
        next_page = response.headers.get('X-Next-Page')

    return merge_requests
