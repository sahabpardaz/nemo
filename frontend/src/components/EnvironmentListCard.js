import React, { useEffect, useState } from 'react'
import { Card, Table } from "react-bootstrap"
import apiURLs from '../apiURLs'
import utils from '../utils'
import Badge from "./Badge"
import HelpTexts from "../constants/HelpTexts"
import ReactTooltip from "react-tooltip"


export default (props) => {
    const { project_id } = props
    const [environments, setEnvironments] = useState([])
    const [defaultEnvironmentId, setDefaultEnvironmentId] = useState()

    useEffect(getEnvironments, [project_id])

    useEffect(getProjectDefaultEnvironment, [project_id])

    useEffect(() => {
        ReactTooltip.rebuild()
    })

    function getEnvironments() {
        utils.requestGET(apiURLs.devopsMetricsEnvironmentsList(project_id))
            .then((response) => {
                setEnvironments(response.results)
            })
    }

    function getProjectDefaultEnvironment() {
        utils.requestGET(apiURLs.project(project_id))
            .then((response) => {
                setDefaultEnvironmentId(response.default_environment.id)
            })
    }

    function EnvironmentTableRow({environment}) {
        return (
            <tr>
                <td>{environment.id}</td>
                <td>{environment.name}</td>
                <td>{environment.description}</td>
                <td>
                    {environment.id === defaultEnvironmentId &&
                        <Badge variant="primary" helpText={HelpTexts.PROJECT_DEFAULT_ENVIRONMENT}>
                            Default
                        </Badge>
                    }
                </td>
            </tr>
        )
    }

    const environmentsTableRows = environments.map(e => <EnvironmentTableRow environment={e} />)

    return (
        <Card className="card-primary">
            <Card.Header>
                <Card.Title>
                    Environments
                </Card.Title>
            </Card.Header>
            <Card.Body className="p-0">
                <Table className="table-head-fixed" hover>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Description</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {environmentsTableRows}
                    </tbody>
                </Table>
            </Card.Body>
        </Card>
    )
}
