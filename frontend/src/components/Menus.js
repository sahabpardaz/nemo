import React, { useEffect, useState } from "react"
import { Link, NavLink, withRouter } from "react-router-dom"
import {
    faAngleRight,
    faFile,
    faUserCog,
    faTachometerAlt
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import apiURLs from "../apiURLs"
import utils from "../utils"


function UserProfile(props) {
    const { name } = props
    return (
        <div className="user-panel mt-3 pb-3 mb-3 d-flex">
            <div className="image">
                <img src="/dist/img/user-placeholder.jpeg"
                    className="img-circle elevation-2" alt="User" />
            </div>
            <div className="info">
                <a className="d-block">{name}</a>
            </div>
        </div>
    )
}

function getProjectIdFromUrl(url) {
    let projectIdCaptureRegex = /\/project\/(\d+)\/?.*/g
    let capturedParameters = projectIdCaptureRegex.exec(url)
    if (capturedParameters) {
        return parseInt(capturedParameters[1])
    }
    return -1
}

function ProjectMenu(props) {
    const { project, isOpen, setOpened } = props
    return (
        <li key={project.id} className="nav-item has-treeview">
            <Link to={`/project/${project.id}/dashboard`}
                className={`nav-link ${isOpen ? "active" : ""}`}
                onClick={() => setOpened(project.id)}
            >
                <FontAwesomeIcon icon={faTachometerAlt} className="nav-icon fas" />
                <p>{project.name}</p>
            </Link>
            <ul className="nav nav-treeview"
                style={isOpen ? { display: "block" } : { display: "none" }}
            >
                <ProjectSubMenuItem
                    project_id={project.id}
                    sub_url="/dashboard"
                    menu_title="Dashboard"
                />
                <ProjectSubMenuItem
                    project_id={project.id}
                    sub_url="/maturity-model"
                    menu_title="Maturity Model"
                />
                <ProjectSubMenuItem
                    project_id={project.id}
                    sub_url="/goal"
                    menu_title="Goals"
                />
                <ProjectSubMenuItem
                    project_id={project.id}
                    sub_url="/integration"
                    menu_title="Integration"
                />
                <ProjectSubMenuItem
                    project_id={project.id}
                    sub_url="/reports"
                    menu_title="Reports"
                />
                <ProjectSubMenuItem
                    project_id={project.id}
                    sub_url="/graphs"
                    menu_title="Graphs"
                />
            </ul>
        </li>
    )
}

function ProjectSubMenuItem(props) {
    const { project_id, sub_url, menu_title } = props
    return (
        <li className="nav-item">
            <NavLink
                className="nav-link"
                to={`/project/${project_id}${sub_url}`}
            >
                <FontAwesomeIcon icon={faAngleRight} className="far nav-icon" />
                <p>{menu_title}</p>
            </NavLink>
        </li>
    )
}

export default withRouter((props) => {
    const [projects, setProjects] = useState([])
    const [loaded, setLoaded] = useState(false)
    const [name, setName] = useState()
    const [openedProjectId, setOpenedProjectId] = useState(
        getProjectIdFromUrl(props.location.pathname)
    )
    const [visitsCount, setVisitsCount] = useState()

    useEffect(() => {
        utils.requestGET(apiURLs.projectsList(), { results: [] })
            .then(res => {
                setProjects(res.results)
                setLoaded(true)
            })
    }, [])

    useEffect(() => {
        utils.requestGET(apiURLs.visitsCount())
            .then(res => {
                setVisitsCount(res)
            })
    }, [])

    useEffect(() => {
        utils.requestGET(apiURLs.user(), true)
            .then(result => {
                setName(`${result.first_name} ${result.last_name}`)
            })
    }, [])

    const projectMenus = []
    for (const project of projects) {
        const menuIsOpen = project.id === openedProjectId || projects.length <= 1
        projectMenus.push(
            <ProjectMenu
                key={project.id}
                project={project}
                isOpen={menuIsOpen}
                setOpened={setOpenedProjectId}
            />
        )
    }

    return (
        <aside className="main-sidebar sidebar-dark-primary elevation-4">
            <NavLink to="/" className="brand-link">
                <img src="/dist/img/logo-white-bg.png" alt="Nemo Logo"
                    className="brand-image img-circle elevation-3" />
                <span className="brand-text font-weight-light">Nemo Dashboard</span>
            </NavLink>
            {/* Override height due to visits count */}
            <div className="sidebar" style={{ height: "calc(100vh - 7rem - 1px)" }}>
                <UserProfile name={name} />
                <nav className="mt-2">
                    <ul className="nav nav-pills nav-sidebar flex-column nav-child-indent nav-flat">
                        {projects.length > 0 &&
                            <>
                                <li className="nav-header">
                                    <NavLink to="/project">PROJECTS</NavLink>
                                </li>
                                {projectMenus}
                            </>
                        }
                        <li className="nav-header">OTHER</li>
                        <li className="nav-item">
                            <NavLink to={"/user/settings"}
                                className="nav-link">
                                <FontAwesomeIcon icon={faUserCog} className="fas nav-icon" />
                                <p>User Settings</p>
                            </NavLink>
                        </li>
                        <li className="nav-item">
                            <NavLink to={"/maturity-model-import-export"}
                                className="nav-link">
                                <FontAwesomeIcon icon={faFile} className="fas nav-icon" />
                                <p>MaturityModel</p>
                            </NavLink>
                        </li>
                    </ul>
                </nav>
            </div>
            <div>
                <span className='p-3 text-white-50'>{visitsCount?.count ?? 'Unknown'} visits in the last {visitsCount?.checking_period_days ?? ''} days</span>
                <br />
                {visitsCount && visitsCount.checking_period_days > 0 ?
                    <span className='p-3 text-white-50'>{Math.round(visitsCount.count / visitsCount.checking_period_days)} daily visits by average</span>
                    : null}
            </div>
        </aside>
    )
})
