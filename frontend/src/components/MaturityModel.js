import React, { useEffect, useState } from 'react'
import MaturityModelLevel from './MaturityModelLevel'
import MaturityModelItemStatusCard from './MaturityModelItemStatusCard'
import ReactTooltip from "react-tooltip"
import styles from "../css/nemo.module.css"
import { Row, Col, Form } from "react-bootstrap"
import { DatetimePickerTrigger } from 'imrc-datetime-picker'
import { FULL_DATE, FULL_DATE_J } from '../utils/moment_formats'
import { faCalendarAlt, faSpinner } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import moment from 'moment-jalaali'
import utils from '../utils'
import apiURLs from '../apiURLs'
import HelpMark from "./HelpMark"
import HelpTexts from '../constants/HelpTexts'
import ResponsiveModal from './ResponsiveModal'


export default (props) => {
    const { projectId, maturityModel } = props
    const [openedItemState, setOpenedItemState] = useState(null)
    const currentTime = moment()
    const [snapshotTime, setSnapshotTime] = useState(currentTime)
    const [projectMaturityState, setProjectMaturityState] = useState()

    const isMaturityStateLoaded = !!projectMaturityState

    useEffect(updateprojectMaturityState, [projectId, snapshotTime, maturityModel])

    function isSnapshotMode() {
        return snapshotTime.format(FULL_DATE_J) !== currentTime.format(FULL_DATE_J)
    }

    function updateprojectMaturityState() {
        let projectMaturityStateUrl = new URL(apiURLs.projectMaturityState(projectId))
        if (isSnapshotMode()) {
            projectMaturityStateUrl.search = new URLSearchParams({snapshot_time: snapshotTime.endOf('day').toISOString()})
        }
        utils.requestGET(projectMaturityStateUrl)
            .then((result) => {
                setProjectMaturityState(result)
            })
    }

    const levelComponents = []
    const isSnapshot = isSnapshotMode()
    for (let i = 0; i < maturityModel.levels.length; i++) {
        const maturityLevel = maturityModel.levels[i]
        const maturityLevelState = projectMaturityState?.maturity_level_states[i]
        levelComponents.push(
            <MaturityModelLevel
                achieved='true'
                maturityLevel={maturityLevel}
                maturityLevelState={maturityLevelState}
                key={maturityLevel}
                id={maturityLevel.name}
                openModal={setOpenedItemState}
                isSnapshot={isSnapshot}
            />
        )
    }

    return (
        <>
            {isMaturityStateLoaded ?
            <div class="container-fluid">
                <h2 class="text-center display-4">{projectMaturityState.achieved_level}</h2>
            </div>
            :
            <div class="container-fluid text-center">
                <FontAwesomeIcon icon={faSpinner} className="mr-1 text-gray fa-spin" size="3x"/>
            </div>
            }
            <div className="card">
                <div className="card-body">
                    {isSnapshot &&
                    <div class="ribbon-wrapper ribbon-lg">
                        <div class="ribbon bg-danger">
                            Snapshot
                        </div>
                    </div>
                    }
                    <Row>
                        <Col md={12}>
                            <Form.Label>Snapshot Date <HelpMark title={HelpTexts.MM_SNAPSHOT_DATE} /></Form.Label>
                            <DatetimePickerTrigger
                                moment={snapshotTime}
                                onChange={setSnapshotTime}
                                isSolar={true}
                                lang="en"
                                showTimePicker={false}
                                closeOnSelectDay={true}
                                maxDate={currentTime}
                            >
                                <div className="input-group">
                                    <input type="text" value={snapshotTime.format(FULL_DATE_J)} className="form-control" />
                                    <div className="input-group-append">
                                        <span className="input-group-text">
                                            <FontAwesomeIcon icon={faCalendarAlt} />
                                        </span>
                                    </div>
                                </div>
                            </DatetimePickerTrigger>
                        </Col>
                    </Row>
                </div>
            </div>
            {levelComponents}
            {openedItemState &&
                <>
                    <ReactTooltip className={styles.generalTooltip} />
                    <ResponsiveModal 
                        open={openedItemState}
                        onClose={() => setOpenedItemState(null)}
                        onAnimationEnd={() => ReactTooltip.rebuild()}
                    >
                        <MaturityModelItemStatusCard
                            item_id={openedItemState.maturity_item.id}
                            project_id={projectId}
                            showViewMoreButton={true}
                            isSnapshot={isSnapshot}
                        />
                    </ResponsiveModal>
                </>
            }
        </>
    )
}
