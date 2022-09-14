import React, { useState } from 'react'
import { Form } from "react-bootstrap"
import { toast } from 'react-toastify'
import apiURLs from "../../apiURLs"
import utils from "../../utils"


export default (props) => {
    const { project, receiveNotificationsDefaultValue } = props
    const [receiveNotifications, setReceiveNotifications] = useState(receiveNotificationsDefaultValue)

    function changeNotificationStatus(event) {
        event.persist()
        const newStatusOfReceiveNotifications = event.target.checked
        utils.request(apiURLs.userSettingsNotificationProjectChange(project.id), 'PATCH', {
            'receive_notifications': newStatusOfReceiveNotifications,
        }, true)
            .then(() => {
                setReceiveNotifications(newStatusOfReceiveNotifications)
                toast.success(`Notifcations ${newStatusOfReceiveNotifications ? "enabled" : "disabled"} for ${project.name}.`)
            })
    }

    return (
        <Form.Group>
            <Form.Check
                type="switch"
                id={project.id}
                label={project.name}
                checked={receiveNotifications}
                onChange={changeNotificationStatus}
            />
        </Form.Group>
    )
}
