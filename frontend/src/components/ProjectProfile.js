import React from 'react'
import HelpMark from './HelpMark'
import HelpTexts from '../constants/HelpTexts'
import theme from '../styles/theme.module.scss'
import {Container, Col, Row} from "react-bootstrap"


export default (props) => {
    const { defaultEnvironment, maturityModel, projectId, projectName, creatorName, achievedLevel, passedItemsCount } = props

    return (
        <Container fluid>
            <div className="card widget-user">
                <div className={`widget-user-header ${theme.bg_dark}`}>
                    <h1>{projectName}</h1>
                    <h5 className="widget-user-desc">{achievedLevel}</h5>
                </div>
                <Row>
                    <Col className="border-right">
                        <div className="description-block">
                            <span className={`description-text ${theme.forecolor_gray_dark}`}>Id</span>
                            <h5 className="description-header">{projectId}</h5>
                        </div>
                    </Col>
                    <Col className="border-right">
                        <div className="description-block">
                            <span className={`description-text ${theme.forecolor_gray_dark}`}>Creator</span>
                            <h5 className="description-header">{creatorName}</h5>
                        </div>
                    </Col>
                    <Col className="border-right">
                        <div className="description-block">
                            <span className={`description-text ${theme.forecolor_gray_dark}`}>Maturity Model
                                            </span>
                            <h5 className="description-header">
                                {maturityModel.description
                                    ? (
                                        <HelpMark title={maturityModel.description} >
                                            {maturityModel.name}
                                        </HelpMark>
                                    )
                                    : maturityModel.name
                                }
                            </h5>
                        </div>
                    </Col>
                    <Col className="border-right">
                        <div className="description-block">
                            <span className={`description-text ${theme.forecolor_gray_dark}`}>Default Environment
                                            <HelpMark title={HelpTexts.PROJECT_DEFAULT_ENVIRONMENT} />
                            </span>
                            <h5 className="description-header">
                                {defaultEnvironment.description
                                    ? (
                                        <HelpMark title={defaultEnvironment.description} >
                                            {defaultEnvironment.name}
                                        </HelpMark>
                                    )
                                    : defaultEnvironment.name
                                }
                            </h5>
                        </div>
                    </Col>
                    <Col>
                        <div className="description-block">
                            <span className={`description-text ${theme.forecolor_gray_dark}`}>Passed Items</span>
                            <h5 className="description-header">{passedItemsCount}</h5>
                        </div>
                    </Col>
                </Row>
            </div>
        </Container>
    )
}