import React, { useEffect, useState } from 'react'
import { useParams, withRouter } from "react-router-dom"
import { faEye, faBorderNone } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import Error from '../../components/Error'
import {
    GITLAB_PROJECT_BY_ID_URL,
    SONAR_PROJECT_BY_KEY_URL,
} from '../../constants/integration_services'
import styles from "../../css/nemo.module.css"
import apiURLs from '../../apiURLs'
import utils from '../../utils'
import HelpMark from '../../components/HelpMark'
import ReactTooltip from "react-tooltip"
import EnvironmentListCard from '../../components/EnvironmentListCard'


export default withRouter((props) => {
    const { project_id } = useParams()
    const [sonarProjects, setSonarProjects] = useState()
    const [versionControl, setVersionControl] = useState()
    const [errorMessage, setErrorMessage] = useState()
    const [apiToken, setApiToken] = useState()

    useEffect(() => {
        let project_integration_sonar_url = apiURLs.projectIntegrationSonar(project_id)

        utils.requestGET(project_integration_sonar_url)
            .then(result => {
                setSonarProjects(result.results)
                setErrorMessage()
            })
            .catch(() => {
                setErrorMessage("Failed to get sonar projects info from server.")
            })
    }, [project_id])

    useEffect(() => {
        let project_integration_version_control_url = apiURLs.projectIntegrationGitlabProject(project_id)

        utils.requestGET(project_integration_version_control_url)
            .then(result => {
                setVersionControl(result.results)
                setErrorMessage() // FIX: it's gonna clear sonar projects fetching error message.
            })
            .catch(() => {
                setErrorMessage("Failed to get version control info from server.")
            })
    }, [project_id])

    useEffect(() => {
        utils.requestGET(apiURLs.projectAPIToken(project_id))
            .then(result => setApiToken(result.key))
    }, [project_id])

    useEffect(() => {
        ReactTooltip.rebuild()
    })

    if (errorMessage) {
        return (
            <Error error={errorMessage} />
        )
    }

    if (!versionControl || !sonarProjects) {
        return (
            <p>Loading ...</p>
        )
    }

    const sonarProjectRows = []
    for (let i = 0; i < sonarProjects.length; i++) {
        const sonarProject = sonarProjects[i]
        const sonarDashboardURL = encodeURI(SONAR_PROJECT_BY_KEY_URL
            .replace('{key}', sonarProject.project_key)
            .replace('{base_url}', getBaseURL(sonarProject.api_base_url)))
        sonarProjectRows.push(
            <tr key={i}>
                <td>{sonarProject.project_key}</td>
                <td className="text-right py-0 align-middle">
                    <div className="btn-group btn-group-sm">
                        <a href={sonarDashboardURL}
                            target="_blank"
                            className="btn btn-secondary">
                            <FontAwesomeIcon icon={faEye} />
                        </a>
                    </div>
                </td>
            </tr>
        )
    }

    return (
        <div className="container-fluid">
            <div className="row">
                <div className="col-md-4">
                    <GitlabProjectInfo gitlabProject={versionControl[0]} />
                    <div className="card card-primary">
                        <div className="card-header">
                            <h3 className="card-title">Project Auth Token</h3>
                        </div>
                        <div className="card-body p-0">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Project-wide authentication token <HelpMark title={"Use as an HTTP header like 'NEMO-PROJECT-TOKEN: <token>' for authenticating to nemo."} /></th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr key='0'>
                                        <td>{apiToken ?? 'No token! Contact the adminstrator.'}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div className="col-md-8">
                    <div className="card card-primary">
                        <div className="card-header">
                            <h3 className="card-title">Sonar Projects</h3>
                        </div>
                        <div className="card-body p-0">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Project Key</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sonarProjectRows.length != 0 ? sonarProjectRows :
                                        <tr className={styles.itemTableRow}>
                                            <td colSpan="2">
                                                <h6>There is no Sonar project integrated with this project.</h6>
                                            </td>
                                        </tr>
                                    }
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <EnvironmentListCard project_id={project_id} />
                </div>
            </div>
        </div>
    )
})

function getBaseURL(completeURL) {
    let pathArray = completeURL.split('/')
    let protocol = pathArray[0]
    let host = pathArray[2]
    let url = protocol + '//' + host
    return url
}

function GitlabProjectInfo({ gitlabProject }) {
    const gitlabProjectExists = !!gitlabProject.project_id

    return (
        <div className="card card-primary">
            <div className="card-header">
                <h3 className="card-title">Gitlab Project Info</h3>
                {gitlabProjectExists ?
                    <div className="card-tools">
                        <a href={GITLAB_PROJECT_BY_ID_URL.replace('{id}', gitlabProject.project_id)}
                            target="_blank"
                            className="btn btn-tool">
                            <FontAwesomeIcon icon={faEye} />
                        </a>
                    </div>
                    : ""}
            </div>
            <div className="card-body">
                {gitlabProjectExists ?
                    <>
                        <strong>Project Id</strong>
                        <p className="text-muted">
                            {gitlabProject.project_id}
                        </p>
                        <hr />
                        <strong>Default Branch</strong>
                        <p className="text-muted">
                            {gitlabProject.default_branch}
                        </p>
                        <hr />
                    </>
                    : <h6 className="text-muted">No Gitlab project is defined.</h6>
                }
            </div>
        </div>
    )
}
