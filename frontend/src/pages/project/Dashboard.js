import React, { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { Col, Container, Row } from "react-bootstrap"
import CoverageWidget from "../../components/coverage/CoverageWidget"
import apiURLs from "../../apiURLs"
import ProjectProfile from "../../components/ProjectProfile"
import DevOpsMetricsWidget from "../../components/DevOpsMetricsWidget"
import theme from '../../styles/theme.module.scss'
import MaturityModelStatus from "../../components/MaturityModelStatus"

export default (props) => {
    const { project, maturityModel, projectMaturityState } = props
    const { project_id } = useParams()
    const [rightColumnItemsCount, setRightColumnItemsCount] = useState(0)

    const incrementRightColumnItemsCount = () => {
        setRightColumnItemsCount(rightColumnItemsCount => rightColumnItemsCount + 1)
    }

    useEffect(() => {
        setRightColumnItemsCount(0)
    }, [project_id])

    return (
        <>
            <Container fluid>
                <Row>
                    <ProjectProfile
                        projectId={project.id}
                        projectName={project.name}
                        defaultEnvironment={project.default_environment}
                        maturityModel={maturityModel}
                        creatorName={project.creator.username}
                        achievedLevel={projectMaturityState.achieved_level}
                        passedItemsCount={projectMaturityState.passed_enabled_items_count}
                    />
                </Row>
                <Row className={`${theme.forecolor}`}>
                    <DevOpsMetricsWidget
                        project_id={project.id}
                        environment_id={project.default_environment.id}
                    />
                </Row>
                <Row>
                    <Col md={rightColumnItemsCount ? 10 : 12}>
                        <MaturityModelStatus project={project} projectMaturityState={projectMaturityState} />
                    </Col>
                    <Col md={rightColumnItemsCount ? 2 : 0}>
                        <Row>
                            <Col>
                                <CoverageWidget
                                    title="Overall Coverage"
                                    metricUrl={apiURLs.projectOverallCoverage(project.id)}
                                    onComponentWillBeRendered={incrementRightColumnItemsCount}
                                />
                                <CoverageWidget
                                    title="Incremental Coverage"
                                    metricUrl={apiURLs.projectIncrementalCoverage(project.id)}
                                    onComponentWillBeRendered={incrementRightColumnItemsCount}
                                />
                            </Col>
                        </Row>
                    </Col>
                </Row>
            </Container>
        </>
    )
}
