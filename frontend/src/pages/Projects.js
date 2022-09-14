import React from "react"
import Error from "../components/Error"
import ContentHeader from "../components/ContentHeader"
import { Link } from 'react-router-dom'
import apiURLs from "../apiURLs"
import utils from "../utils"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import {faFrown} from "@fortawesome/free-solid-svg-icons"

class Projects extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            error: null,
            projects: []
        }
        this.componentDidMount = this.componentDidMount.bind(this)
    }

    componentDidMount() {
        utils.requestGET(apiURLs.projectsList())
            .then((result) => {
                this.setState({
                    error: null,
                    projects: result.results
                })
            })
            .catch((errorBundle) => {
                switch (errorBundle.response?.status) {
                    case 404:
                        this.setState({
                            error: "No projects found"
                        })
                        break
                    case 403:
                        this.setState({
                            error: null,
                            projects: []
                        })
                }
            })
    }

    render() {
        const { error, projects } = this.state

        if (error) {
            return (
                <div className="content-wrapper">
                    <div className="content">
                        <ContentHeader header="Projects" />
                        <Error error={error} />
                    </div>
                </div>
            )
        }

        let projects_rows = []
        if (projects) {
            for (let i = 0, len = projects.length; i < len; i++) {
                projects_rows.push(
                    <tr key={i}>
                        <td>{i + 1}</td>
                        <td>
                            <Link to={`/project/${projects[i].id}/dashboard`}>{projects[i].name}</Link>
                        </td>
                    </tr>
                )
            }
        }

        return (
            <div className="content-wrapper">
                <ContentHeader header="Projects" />
                <div className="content">
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">Projects</h3>
                        </div>
                        <div className="card-body p-0">
                            <table className="table table-striped projects">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Name</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {projects_rows.length != 0 ? projects_rows :
                                        <tr>
                                            <td className="project-state" colSpan="2">
                                                <FontAwesomeIcon icon={faFrown} size="8x" style={{color: "#adb5bd"}}/>
                                                <h5>No projects found to show.</h5>
                                                <h6>Or you have no access to any projects.</h6>
                                            </td>
                                        </tr>
                                    }
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

        )
    }
}

export default Projects