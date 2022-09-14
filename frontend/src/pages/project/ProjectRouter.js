import React, { useEffect, useState } from 'react'
import { withRouter, Route } from "react-router-dom"
import Error from "../../components/Error"
import ContentHeader from "../../components/ContentHeader"
import GoalSingleView from './goal/GoalSingleView'
import GoalListView from './goal/GoalListView'
import CreateUpdateGoal, { CreateMode } from './goal/CreateUpdateGoal'
import Integration from './Integration'
import ReportListView from './reports/ListView'
import ServiceStatusReportEditView from './reports/ServiceStatusReportEditView'
import apiURLs from '../../apiURLs'
import DevopsGraphsPage from './DevopsGraphsPage'
import utils from '../../utils'
import DeploymentReportEditView from "./reports/DeploymentReportEditView"
import ChangeListEditView from "./reports/ChangeListEditView"
import { get_goal_item_choices_from_maturity_model } from "../../utils/item_choices_for_goal"
import MaturityModelItem from "./MaturityModelItem"
import MaturityModelPage from "./MaturityModelPage"
import Dashboard from './Dashboard'
import ReactTooltip from "react-tooltip"


export default withRouter((props) => {
    const projectId = props.match.params.id
    const [error, setError] = useState(null)
    const [project, setProject] = useState({
        id: projectId,
        default_environment: {
            id: null,
            name: null,
        },
        maturity_model: null,
        creator: {
            username: null,
        }
    })
    const [maturityModel, setMaturityModel] = useState({
        name: null,
        levels: [],
    })
    const [projectMaturityState, setprojectMaturityState] = useState({
        maturity_level_states: [],
    })

    useEffect(updateProjectInfo, [projectId])
    
    useEffect(ReactTooltip.rebuild)

    useEffect(updateMaturityModel, [project.maturity_model])

    useEffect(updateprojectMaturityState, [projectId])

    function updateMaturityModel() {
        if (project.maturity_model === null)
            return

        utils.requestGET(apiURLs.maturityModel(project.maturity_model))
            .then((result) => {
                setMaturityModel(result)
            })
    }

    function updateprojectMaturityState() {
        utils.requestGET(apiURLs.projectMaturityState(projectId))
            .then((result) => {
                setprojectMaturityState(result)
            })
    }

    function updateProjectInfo() {
        utils.requestGET(apiURLs.project(projectId))
            .then((result) => {
                setError(null)
                setProject({
                    id: result.id,
                    name: result.name,
                    creator: result.creator,
                    default_environment: result.default_environment,
                    maturity_model: result.maturity_model,
                })
            })
            .catch((errorBundle) => {
                if (errorBundle.response?.status === 404) {
                    setError("Project Not Found.")
                } else
                    setError("Failed to load project info from server.")
            })
    }

    if (error) {
        return (
            <div className="content-wrapper">
                <ContentHeader header={`Project ${projectId}`} />
                <div className="content">
                    <Error error={error} />
                </div>
            </div>
        )
    }

    const choices = projectMaturityState
        ? get_goal_item_choices_from_maturity_model(projectMaturityState.maturity_level_states)
        : []
    return (
        <div className="content-wrapper">
            <ContentHeader header={`Project ${project.name}`} />
            <div className="content">
                <Route exact path="/project/:project_id/goal/new">
                    <CreateUpdateGoal
                        mode={CreateMode}
                        project_id={projectId}
                        onRequestClose={() => true}
                        options={choices}
                        onSuccessful={updateProjectInfo}
                    />
                </Route>
                <Route path="/project/:project_id(\d+)/goal/:goal_id(\d+)">
                    <GoalSingleView
                        maturityLevels={maturityModel.levels}
                        maturityLevelStates={projectMaturityState.maturity_level_states}
                        onGoalChanged={updateProjectInfo} />
                </Route>
                <Route exact path="/project/:project_id/goal">
                    <GoalListView project={project} />
                </Route>
                <Route exact path="/project/:project_id/integration">
                    <Integration project={project} />
                </Route>
                <Route exact path="/project/:project_id/reports">
                    <ReportListView project={project} />
                </Route>
                <Route exact path="/project/:project_id(\d+)/reports/service_status_report/new">
                    <ServiceStatusReportEditView />
                </Route>
                <Route exact path="/project/:project_id(\d+)/reports/environment/:environment_id(\d+)/service_status_report/:report_id(\d+)/">
                    <ServiceStatusReportEditView />
                </Route>
                <Route exact path="/project/:project_id(\d+)/reports/deployment/new">
                    <DeploymentReportEditView />
                </Route>
                <Route exact path="/project/:project_id(\d+)/reports/environment/:environment_id(\d+)/deployment/:report_id(\d+)/">
                    <DeploymentReportEditView />
                </Route>
                <Route exact path="/project/:project_id(\d+)/reports/changelist/new">
                    <ChangeListEditView />
                </Route>
                <Route exact path="/project/:project_id(\d+)/reports/changelist/:report_id(\d+)/">
                    <ChangeListEditView />
                </Route>
                <Route exact path="/project/:project_id(\d+)/graphs">
                    <DevopsGraphsPage defaultEnvironmentId={project.default_environment.id} />
                </Route>
                <Route exact path="/project/:project_id/maturity-model">
                    <MaturityModelPage
                        project={project}
                        maturityModel={maturityModel}
                    />
                </Route>
                <Route exact path="/project/:project_id/dashboard">
                    <Dashboard
                        project={project}
                        maturityModel={maturityModel}
                        projectMaturityState={projectMaturityState}
                    />
                </Route>
                <Route exact path="/project/:project_id/maturity-model/item/:item_id">
                    <MaturityModelItem
                        project={project}
                        onItemChanged={updateProjectInfo}
                        projectMaturityState={projectMaturityState}
                    />
                </Route>
            </div>
        </div>
    )
})
