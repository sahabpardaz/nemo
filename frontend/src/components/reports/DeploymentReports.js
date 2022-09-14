import React, { useState, useEffect } from "react"
import { faCheck, faTimes } from "@fortawesome/free-solid-svg-icons"
import moment from 'moment-jalaali'
import { ModalManager } from 'react-dynamic-modal'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import apiURLs from "../../apiURLs"
import DeleteModal from '../DeleteModal'
import ReportsAbs from "./ReportsAbs"
import utils from "../../utils"
import EditDeleteActionButtons from "./EditDeleteActionButtons"
import StringLimitedSize from "../LimitedSizeString"

export default class DeploymentReports extends ReportsAbs {

    getReportsURL() {
        return apiURLs.devopsMetricsDeploymentsList(this.props.projectId, this.props.environmentId)
    }

    getNewReportPageURL() {
        return `/project/${this.props.projectId}/reports/deployment/new/?preferred_env=${this.props.environmentId}`
    }

    getItemsListComponent() {
        const reportRows = []
        for (let i = 0; i < this.state.reports.length; i++) {
            const report = this.state.reports[i]
            reportRows.push(<DeploymentReportRow
                key={report.id}
                report={report}
                projectId={this.props.projectId}
                environmentId={this.props.environmentId}
                onDeleted={() => this._onReportDeleted(report)} />)
        }
        return (
            <table className="table">
                <thead>
                    <tr>
                        <th className="text-left">Status</th>
                        <th className="text-left">Changelist Title</th>
                        <th className="text-left">Commit</th>
                        <th className="text-left">Time</th>
                        <th className="text-right"></th>
                    </tr>
                </thead>
                <tbody>
                    {reportRows.length !== 0 ? reportRows :
                        <tr>
                            <td className="project-state" colSpan="4">
                                <h6>No reports to show.</h6>
                            </td>
                        </tr>
                    }
                </tbody>
            </table>
        )
    }
}

const DeploymentReportRow = props => {

    const emptyChangeList = {
        change_list_id: "",
        commit_hash: "",
        title: ""
    }
    const [changeList, setChangeList] = useState(emptyChangeList)

    useEffect(() => {
        (async () => {
            const result = await utils.requestGET(
                apiURLs.devopsMetricsChangeList(props.projectId, props.report.change_list),
                true,
                emptyChangeList)
            setChangeList(result)
        })()
    }, [props.report.change_list])

    function _deleteBtnClicked() {
        ModalManager.open(
            <DeleteModal
                deleteURL={apiURLs.devopsMetricsDeployment(props.projectId, props.environmentId, props.report.id)}
                modelTitle={props.report.id}
                modelTypeName="Deployment Report"
                onSuccessful={props.onDeleted}
            />
        )
    }

    let editUrl = `/project/${props.projectId}/reports/environment/${props.environmentId}/deployment/${props.report.id}/`

    return (
        <tr>
            {props.report.status === "P"
                ? <td className="text-primary"><FontAwesomeIcon icon={faCheck} /> Pass</td>
                : <td className="text-muted"><FontAwesomeIcon icon={faTimes} /> Fail</td>
            }
            <td><StringLimitedSize text={changeList.title} limitedSize={50}/></td>
            <td><StringLimitedSize text={changeList.commit_hash} limitedSize={8}/></td>
            <td>{utils.convertIsoTimestampToJalali(props.report.time)}</td>
            <td className="text-right">
                <EditDeleteActionButtons editUrl={editUrl} onDeleteClicked={_deleteBtnClicked} />
            </td>
        </tr>
    )
}