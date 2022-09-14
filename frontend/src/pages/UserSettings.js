import React from 'react'
import { Container } from "react-bootstrap"
import ContentHeader from "../components/ContentHeader"
import NotificationSettings from '../components/user/NotificationSettings'


export default () => {
    return (
        <div className="content-wrapper">
            <ContentHeader header="User Settings" />
            <div className="content">
                <Container fluid>
                    <NotificationSettings />
                </Container>
            </div>
        </div>
    )
}
