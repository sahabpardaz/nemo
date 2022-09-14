import React from "react"
import {Col, Container, Row} from "react-bootstrap"
import MaturityModel from "../../components/MaturityModel"


export default (props) => {
    const { project, maturityModel } = props

    return (
        <Container fluid>
            <Row>
                <Col md={12}>
                    <MaturityModel
                        projectId={project.id}
                        maturityModel={maturityModel}
                    />
                </Col>
            </Row>
        </Container>
    )
}