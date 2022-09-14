import React, { useEffect, useState } from 'react'
import { withRouter, Link, useParams } from "react-router-dom"
import HelpMark from "../components/HelpMark"
import HelpTexts from "../constants/HelpTexts"
import styles from "../css/nemo.module.css"
import utils from "../utils"
import apiURLs from '../apiURLs'

export default withRouter((props) => {
    const { item_id, project_id, showViewMoreButton, isSnapshot } = props
    const [itemState, setItemState] = useState({
        "maturity_item": {
            "id": item_id,
            "name": "Loading...",
            "evaluation_type": {}
        }
    })
    const [color, setColor] = useState("gray")
    useEffect(() => {
        setColor(itemState.disabled ? "gray" : itemState.is_passed ? "success" : "danger")
    }, [itemState.disabled, itemState.is_passed])
    utils.useEffectAsync(async () => {
        const itemMaturityState = await utils.requestGET(apiURLs.projectItemMaturityState(project_id, item_id))
        setItemState(itemMaturityState)
    }, [item_id])

    return (
    <div className={`card card-outline card-${color}`}>
        <div className="ribbon-wrapper ribbon-lg">
            <div
                className={`ribbon text-lg bg-${color}`}>{itemState.disabled ? "Disabled" : (itemState.is_passed ? "Pass" : "Fail")}</div>
        </div>
        <div className="card-body box-profile">
            <h3 className="profile-username">{itemState.maturity_item.name}</h3>
            <br />
            <ul className="list-group list-group-unbordered">
                <li className="list-group-item">
                    <b>Code</b>
                    <a className="float-right">{itemState.maturity_item.code}</a>
                </li>
                {!itemState.disabled && itemState.latest_evaluation_report &&
                    <li className="list-group-item">
                        <div className={styles.itemDetailsFieldInlineLeft}>
                            <b>Expected Value</b><HelpMark title={HelpTexts.MM_ITEM_EXPECTED_VALUE} />
                            <a className="float-right">
                                {utils.getReadableValueByType(itemState.latest_evaluation_report.expected_value,
                                    itemState.latest_evaluation_report.value_type)}
                            </a>
                        </div>
                        <div className={styles.itemDetailsFieldInlineRight}>
                            <b>Current Value</b><HelpMark title={HelpTexts.MM_ITEM_CURRENT_VALUE} />
                            <a className="float-right">
                                {utils.getReadableValueByType(itemState.latest_evaluation_report.current_value,
                                    itemState.latest_evaluation_report.value_type)}
                            </a>
                        </div>
                    </li>
                }
                <li className="list-group-item">
                    <div className={styles.itemDetailsFieldInlineLeft}>
                        <b>Checking Period</b><HelpMark title={HelpTexts.MM_ITEM_CHECKING_PERIOD} />
                        <a className="float-right">{itemState.maturity_item.evaluation_type.checking_period_days} Days</a>
                    </div>
                    <div className={styles.itemDetailsFieldInlineRight}>
                        <b>Validity Period</b><HelpMark title={HelpTexts.MM_ITEM_VALIDITY_PERIOD} />
                        <a className="float-right">{itemState.maturity_item.evaluation_type.validity_period_days} Days</a>
                    </div>
                </li>
                {itemState.failure_reason &&
                <li className="list-group-item">
                    <b>Failure Reason</b>
                    <a className="float-right">{itemState.failure_reason}</a>
                </li>
                }
                {!itemState.disabled && !isSnapshot &&
                    <li className="list-group-item">
                        <b>Closest Goal</b>
                        {itemState.closest_goal ?
                            <Link className="float-right"
                                to={`/project/${project_id}/goal/${itemState.closest_goal.id}/`}>
                                {utils.convertIsoTimestampToJalali(itemState.closest_goal.due_date, false)}
                            </Link>
                            :
                            <a className="float-right">Not targeted</a>
                        }
                    </li>
                }
                <li className="list-group-item">
                    <b>Description</b>
                    <br /><a>{itemState.maturity_item.description}</a>
                </li>
            </ul>
        </div>
        {showViewMoreButton && !isSnapshot &&
        <div className="modal-footer justify-content-between">
            <button type="button" className="btn btn-secondary" onClick={event => props.history.push(`/project/${project_id}/maturity-model/item/${itemState.maturity_item.id}`)}>
                View more
            </button>
        </div>
        }
    </div>
    )
})