const apiURL = window.AppConfig.API_URL

const authMod = window.AppConfig.AUTH_MOD

const DOCUMENTATION_ROOT = `${apiURL}/api/v1/documentation`
const API_ROOT = `${apiURL}/api/v1/dashboard`
const DEVOPSMETRICS_API_ROOT = `${apiURL}/api/v1/devops-metrics`
const AUTHENTICATION_ROOT_SSO = `${apiURL}/api/authentication`
const AUTHENTICATION_ROOT_OIDC = `${apiURL}/api/oidc`


class ApiURLs {

    getEditUrlFromListUrl(listURL, itemId) {
        if (listURL.endsWith('/'))
            return `${listURL}${itemId}/`
        else
            return `${listURL}/${itemId}/`

    }

    swagger() { return `${DOCUMENTATION_ROOT}/swagger/` }

    login() { 
        if(authMod == window.AuthMod.OIDC){
            return `${AUTHENTICATION_ROOT_OIDC}/authenticate/`
        }
    }

    logout() { 
        if(authMod == window.AuthMod.OIDC){
            return `${AUTHENTICATION_ROOT_OIDC}/logout`
        }
    }

    user() { return `${API_ROOT}/user/` }

    userSettingsNotificationProjectsList() { return `${API_ROOT}/user/settings/notification/project/` }

    userSettingsNotificationProjectChange(projectId) { return `${API_ROOT}/user/settings/notification/project/${projectId}/` }

    visitsCount() { return `${API_ROOT}/visits-count/` }

    projectsList() { return `${API_ROOT}/project/` }

    project(projectId) { return this.getEditUrlFromListUrl(this.projectsList(), projectId) }

    evaluationRequestList(projectId) { return `${this.project(projectId)}/evaluation/` }

    evaluationRequest(projectId, evaluationRequestId) { return this.getEditUrlFromListUrl(this.evaluationRequestList(projectId), evaluationRequestId) }

    toggleRequestList(projectId) { return `${this.project(projectId)}/maturity-model-item-constraint/` }

    toggleRequest(projectId, toggleRequestId) { return this.getEditUrlFromListUrl(this.toggleRequestList(projectId), toggleRequestId) }

    projectMaturityState(projectId) { return `${this.project(projectId)}/maturity-state/` }

    maturtiyItemDoryResult(projectId, doryEvaluationId, itemCode) { return `${this.project(projectId)}/dory-evaluation/${doryEvaluationId}/maturity-item-result/${itemCode}/` }

    projectItemMaturityState(projectId, itemId) { return `${this.project(projectId)}/maturity-item-state/${itemId}/` }

    projectGoalsList(projectId) { return `${this.project(projectId)}/goal/` }

    projectGoal(projectId, goalId) { return this.getEditUrlFromListUrl(this.projectGoalsList(projectId), goalId) }

    projectIntegrationSonar(projectId) { return `${this.project(projectId)}/integration/sonar/` }

    projectIntegrationGitlabProject(projectId) { return `${this.project(projectId)}/integration/gitlab-project/` }

    projectOverallCoverage(projectId) { return `${this.project(projectId)}/metric/overall-coverage/` }

    projectIncrementalCoverage(projectId) { return `${this.project(projectId)}/metric/incremental-coverage/` }

    projectAPIToken(projectId) { return `${this.project(projectId)}/api-token/` }

    projectGraphs(projectId) { return `${this.project(projectId)}/graphs/` }

    projectGraphURLForDailyCoverage(projectId, fromDate = null, toDate = null, checkingPeriodDays = null) {
        let url = `${this.projectGraphs(projectId)}/daily-coverage/`
        let parameters = [
            `period_start_date=${fromDate}`,
            `period_end_date=${toDate}`,
            `checking_period_days=${checkingPeriodDays}`]
        let queryString = parameters
            .filter(p => !p.endsWith('null'))
            .join('&')
        if (queryString)
            url = `${url}?${queryString}`
        return url
    }

    maturityModelList() { return `${API_ROOT}/maturity-model/` }

    maturityModel(maturityModelId) { return this.getEditUrlFromListUrl(this.maturityModelList(), maturityModelId) }

    evaluationReportList(projectId, itemId) { return `${this.project(projectId)}item/${itemId}/evaluation-report/` }

    evaluationReport(projectId, itemId, evaluationReportId) { return this.getEditUrlFromListUrl(this.evaluationReportList(projectId, itemId), evaluationReportId) }

    devopsMetricsProject(projectId) { return `${DEVOPSMETRICS_API_ROOT}/project/${projectId}/` }

    devopsMetricsEnvironmentsList(projectId) { return `${this.devopsMetricsProject(projectId)}/environment/` }

    devopsMetricsEnvironment(projectId, environmentId) { return this.getEditUrlFromListUrl(this.devopsMetricsEnvironmentsList(projectId), environmentId) }

    devopsMetricsStatistics(projectId, environmentId) { return `${this.devopsMetricsEnvironment(projectId, environmentId)}/statistics/` }

    devopsMetricsServiceStatusReportsList(projectId, environmentId) { return `${this.devopsMetricsEnvironment(projectId, environmentId)}/report/` }

    devopsMetricsServiceStatusReport(projectId, environmentId, reportId) { return this.getEditUrlFromListUrl(this.devopsMetricsServiceStatusReportsList(projectId, environmentId), reportId) }

    devopsMetricsDeploymentsList(projectId, environmentId) { return `${this.devopsMetricsEnvironment(projectId, environmentId)}/deployment/` }

    devopsMetricsDeployment(projectId, environmentId, deploymentId) { return this.getEditUrlFromListUrl(this.devopsMetricsDeploymentsList(projectId, environmentId), deploymentId) }

    devopsMetricsChangeListsList(projectId) { return `${this.devopsMetricsProject(projectId)}/changelist/` }

    devopsMetricsChangeList(projectId, changeListId) { return this.getEditUrlFromListUrl(this.devopsMetricsChangeListsList(projectId), changeListId) }

    devopsMetricsChartURL(metricName, projectId, environmentId, fromDate = null, toDate = null, checkingPeriodDays = null) {
        let url = `${this.devopsMetricsEnvironment(projectId, environmentId)}/metric/${metricName}/`
        let parameters = [
            `period_start_date=${fromDate}`,
            `period_end_date=${toDate}`,
            `checking_period_days=${checkingPeriodDays}`]
        let queryString = parameters
            .filter(p => !p.endsWith('null'))
            .join('&')
        if (queryString)
            url = `${url}?${queryString}`
        return url
    }

    devopsMetricsChangeFailureRateChart(projectId, environmentId, fromDate = null, toDate = null, checkingPeriodDays = null) { return this.devopsMetricsChartURL('change-failure-rate', projectId, environmentId, fromDate, toDate, checkingPeriodDays) }

    devopsMetricsLeadTimeChart(projectId, environmentId, fromDate = null, toDate = null, checkingPeriodDays = null) { return this.devopsMetricsChartURL('lead-time', projectId, environmentId, fromDate, toDate, checkingPeriodDays) }

    devopsMetricsTimeToRestoreChart(projectId, environmentId, fromDate = null, toDate = null, checkingPeriodDays = null) { return this.devopsMetricsChartURL('time-to-restore', projectId, environmentId, fromDate, toDate, checkingPeriodDays) }

    devopsMetricsDeploymentFrequencyChart(projectId, environmentId, fromDate = null, toDate = null, checkingPeriodDays = null) { return this.devopsMetricsChartURL('deployment-frequency', projectId, environmentId, fromDate, toDate, checkingPeriodDays) }

}

export default new ApiURLs()