import React from "react"
import { ModalManager } from 'react-dynamic-modal'
import apiURLs from "../../apiURLs"
import DeleteModal from '../DeleteModal'
import ReportsAbs from "./ReportsAbs"
import EditDeleteActionButtons from "./EditDeleteActionButtons"
import StringLimitedSize from "../LimitedSizeString"
import utils from "../../utils"


export default class ChangeListReports extends ReportsAbs {

    getReportsURL() {
        return apiURLs.devopsMetricsChangeListsList(this.props.projectId)
    }

    getNewReportPageURL() {
        return `/project/${this.props.projectId}/reports/changelist/new/`
    }

    // Override
    componentDidUpdate(prevProps, prevState) {
        if (prevProps.projectId !== this.props.projectId) {
            // noinspection JSIgnoredPromiseFromCall
            this._reloadReports()
        }
    }

    // Override
    propsLoaded() {
        return !!this.props.projectId
    }

    getItemsListComponent() {
        const reportRows = []
        for (let i = 0; i < this.state.reports.length; i++) {
            const report = this.state.reports[i]
            reportRows.push(<ChangeListReportRow
                key={report.id}
                id={report.id}
                change_list_id={report.change_list_id}
                title={report.title}
                commit_hash={report.commit_hash}
                time={utils.convertIsoTimestampToJalali(report.time)}
                projectId={this.props.projectId}
                onDeleted={() => this._onReportDeleted(report)}/>)
        }
        return (
            <table className="table">
                <thead>
                <tr>
                    <th className="text-left">ID</th>
                    <th className="text-left">Title</th>
                    <th className="text-left">Commit Hash</th>
                    <th className="text-left">Time</th>
                    <th className="text-right"/>
                </tr>
                </thead>
                <tbody>
                {reportRows.length !== 0 ? reportRows :
                    <tr>
                        <td className="project-state" colSpan="5">
                            <h6>No reports to show.</h6>
                        </td>
                    </tr>
                }
                </tbody>
            </table>
        )
    }
}


class ChangeListReportRow extends React.Component {

    constructor(props) {
        super(props)
        this._deleteBtnClicked = this._deleteBtnClicked.bind(this)
    }

    _deleteBtnClicked() {
        ModalManager.open(
            <DeleteModal
                deleteURL={apiURLs.devopsMetricsChangeList(this.props.projectId, this.props.id)}
                modelTitle={this.props.id}
                modelTypeName="ChangeList Report"
                onSuccessful={this.props.onDeleted}
            />
        )
    }

    render() {
        const editUrl = `/project/${this.props.projectId}/reports/changelist/${this.props.id}/`
        return (
            <tr>
                <td><StringLimitedSize text={this.props.change_list_id} limitedSize={8}/></td>
                <td><StringLimitedSize text={this.props.title} limitedSize={50}/></td>
                <td><StringLimitedSize text={this.props.commit_hash} limitedSize={8}/></td>
                <td>{this.props.time}</td>
                <td className="text-right">
                    <EditDeleteActionButtons editUrl={editUrl} onDeleteClicked={this._deleteBtnClicked} />
                </td>
            </tr>
        )
    }
}