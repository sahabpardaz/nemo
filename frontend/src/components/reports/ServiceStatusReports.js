import React from "react"
import { faCheck, faTimes } from "@fortawesome/free-solid-svg-icons"
import { ModalManager } from 'react-dynamic-modal'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import apiURLs from "../../apiURLs"
import DeleteModal from '../DeleteModal'
import ReportsAbs from "./ReportsAbs"
import EditDeleteActionButtons from "./EditDeleteActionButtons"
import utils from "../../utils"

export default class ServiceStatusReports extends ReportsAbs {

    getReportsURL() {
        return apiURLs.devopsMetricsServiceStatusReportsList(this.props.projectId, this.props.environmentId)
    }

    getNewReportPageURL() {
        return `/project/${this.props.projectId}/reports/service_status_report/new/?preferred_env=${this.props.environmentId}`
    }

    getItemsListComponent() {
        const reportRows = []
        for (let i = 0; i < this.state.reports.length; i++) {
            const report = this.state.reports[i]
            reportRows.push(<ServiceStatusReportRow
                key={report.id}
                id={report.id}
                up={report.status === "U"}
                time={utils.convertIsoTimestampToJalali(report.time)}
                projectId={this.props.projectId}
                environmentId={this.props.environmentId}
                onDeleted={() => this._onReportDeleted(report)}/>)
        }
        return (
            <table className="table">
                <thead>
                <tr>
                    <th className="text-left">Status</th>
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

class ServiceStatusReportRow extends React.Component {

    constructor(props) {
        super(props)

        this._deleteBtnClicked = this._deleteBtnClicked.bind(this)
    }

    _deleteBtnClicked() {
        ModalManager.open(
            <DeleteModal
                deleteURL={apiURLs.devopsMetricsServiceStatusReport(this.props.projectId, this.props.environmentId, this.props.id)}
                modelTitle={this.props.id}
                modelTypeName="Service Status Report"
                onSuccessful={this.props.onDeleted}
            />
        )
    }

    render() {
        let editUrl = `/project/${this.props.projectId}/reports/environment/${this.props.environmentId}/service_status_report/${this.props.id}/`
        return (
            <tr>
                {this.props.up
                    ? <td className="text-primary"><FontAwesomeIcon icon={faCheck}/> Up</td>
                    : <td className="text-muted"><FontAwesomeIcon icon={faTimes}/> Down</td>
                }
                <td>{this.props.time}</td>
                <td className="text-right">
                    <EditDeleteActionButtons editUrl={editUrl} onDeleteClicked={this._deleteBtnClicked} />
                </td>
            </tr>
        )
    }
}