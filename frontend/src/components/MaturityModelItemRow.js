import React, {useEffect} from 'react'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import {faCheck, faClock, faBong, faTimes, faSpinner} from "@fortawesome/free-solid-svg-icons"
import styles from "../css/nemo.module.css"
import HelpTexts from "../constants/HelpTexts"
import ReactTooltip from "react-tooltip"
import Badge from "./Badge"
import utils from '../utils'
import LoadingIcon from './icons/LoadingIcon'
import { EvaluationTypeKind } from '../utils/evaluationType'


export default (props) => {
    const {openModal, maturityItems, maturityItemStates, isSnapshot} = props
    const items = []

    useEffect(() => {
        ReactTooltip.rebuild()
    })

    for (let i = 0; i < maturityItems.length; i++) {
        const maturityItem = maturityItems[i]
        const maturityStateExists = !!maturityItemStates
        const maturityItemState = maturityStateExists ? maturityItemStates[i] : null
        let status
        if (!maturityStateExists) {
            status = <LoadingIcon />
        } else if (maturityItemState.disabled) {
            status = <b className="mr-1 text-muted">Disabled</b>
        } else if (maturityItemState.is_passed) {
            status = <FontAwesomeIcon icon={faCheck} className="mr-1 text-primary" />
        } else {
            status = <FontAwesomeIcon icon={faTimes} className="mr-1 text-danger" />
        }
        items.push(
            <tr className={maturityStateExists && openModal ? styles.itemTableRow : null}
                onClick={() => maturityStateExists && openModal ? openModal(maturityItemState) : {}}
                key={i}
            >
                <td>{maturityItem.code}</td>
                <td>{maturityItem.name}</td>
                <td>
                    {!isSnapshot && maturityStateExists &&
                    <div style={{float: 'right'}}>
                        {maturityItemState.maturity_item.evaluation_type.kind === EvaluationTypeKind.MANUAL &&
                            <Badge variant="primary" helpText={HelpTexts.MM_ITEM_BADGE_MANUAL_EVALUATION}>
                                Manual
                            </Badge>
                        }
                        {maturityItemState.maturity_item.evaluation_type.kind === EvaluationTypeKind.DORY &&
                            <Badge variant="primary" helpText={HelpTexts.MM_ITEM_BADGE_DORY_EVALUATION}>
                                Dory
                            </Badge>
                        }
                        {maturityItemState.closest_goal &&
                            <Badge variant="secondary" helpText={HelpTexts.MM_ITEM_BADGE_CLOSEST_GOAL}>
                                <FontAwesomeIcon icon={faClock}/> {utils.convertIsoTimestampToJalali(maturityItemState.closest_goal.due_date, false)}
                            </Badge>
                        }
                        {maturityItemState.latest_pending_evaluation_request_id &&
                            <Badge variant="warning" helpText={HelpTexts.MM_ITEM_BADGE_PENDING_EVALUATION_REQUEST}>
                                <FontAwesomeIcon icon={faBong}/> Evaluating
                            </Badge>
                        }
                    </div>
                    }
                </td>
                <td>{status}</td>
            </tr>
        )
    }

    return (
        <tbody>
        {items}
        </tbody>
    )
}
