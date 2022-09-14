import React, { useEffect, useState } from 'react'
import { Row, Col, Card } from "react-bootstrap"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faBell } from "@fortawesome/free-solid-svg-icons"
import ProjectNotificationSwitch from './ProjectNotificationSwitch'
import theme from '../../styles/theme.module.scss'
import apiURLs from "../../apiURLs"
import utils from "../../utils"

export default () => {
    const [projectsNotifications, setProjectsNotifications] = useState([])

    useEffect(() => {
        utils.requestGET(apiURLs.userSettingsNotificationProjectsList())
            .then((result) => {
                setProjectsNotifications(result.results)
            })
    }, [])

    return (
        <Row className={`${theme.forecolor}`}>
            <Col>
                <Card className="card-primary">
                    <Card.Header>
                        <FontAwesomeIcon icon={faBell} className="fas nav-icon" />
                        <text className="ml-2">Notifications</text>
                    </Card.Header>
                    <Card.Body>
                        {projectsNotifications.length == 0 ? <Card.Text>There is no projects.</Card.Text> :
                            <>
                                <Card.Text>
                                You can turn the notifications on/off per project.
                                </Card.Text>
                                {projectsNotifications.map(projectNotification =>
                                    <ProjectNotificationSwitch
                                        key={projectNotification.project.id}
                                        project={projectNotification.project}
                                        receiveNotificationsDefaultValue={projectNotification.receive_notifications}
                                    />
                                )}
                            </>
                        }
                    </Card.Body>
                </Card>
            </Col>
        </Row>
    )
}

