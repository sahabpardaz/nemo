import React, { useState } from "react"
import { faAngleLeft, faAngleRight, faCheck, faTimes, faFile } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import utils from "../utils"
import apiURLs from "../apiURLs"
import HelpMark from "./HelpMark"
import styles from "../css/nemo.module.css"
import MaturityItemDoryResult from "./MaturityItemDoryResult"
import ResponsiveModal from "./ResponsiveModal"


export default ({ project_id, item_id, item_code, reports_per_page = 10 }) => {
    const [evaluationReports, setEvaluationReports] = useState([])
    const [pageIndex, setPageIndex] = useState(0)
    const [mayHaveMorePreviousReports, setMayHaveMorePreviousReports] = useState(true)
    const [error, setError] = useState("Loading...")
    const [expandedReportId, setExpandedReportId] = useState()
    const [viewLogModalOpened, setViewLogModalOpened] = useState(false)

    if (!(reports_per_page > 0))
        throw Error("'Reports per page' should be a number greater than 0.")

    utils.useEffectAsync(async () => {
        try {
            const result = await utils.requestGET(
                `${apiURLs.evaluationReportList(project_id, item_id)}?limit=${reports_per_page}&offset=${pageIndex * reports_per_page}`,
                true)
            if (result.results.length === 0) {
                if (pageIndex === 0)
                    setError('No evaluation reports found.')
                else
                    setError('No more evaluation reports found.')
                setMayHaveMorePreviousReports(false)
                return
            } else {
                if (pageIndex === 0)
                    setExpandedReportId(result.results[0].id)
                if (result.results.length < reports_per_page) {
                    setMayHaveMorePreviousReports(false)
                } else {
                    setMayHaveMorePreviousReports(true)
                }
            }
            setEvaluationReports(result.results)
            setError(null)
        } catch (e) {
            setError('Failed to fetch Evaluation Report!')
        }
    }, [project_id, item_id, pageIndex])

    function previousBtnClick() {
        setPageIndex(pageIndex + 1)
    }

    function nextBtnClick() {
        setPageIndex(pageIndex - 1)
    }

    const reportRows = evaluationReports.map(r => <ReportRow
        report={r}
        expanded={r.id === expandedReportId}
        onClick={() => setExpandedReportId(r.id)}
    />)

    return (
        <>
            <div className="card card-outline">
                <div className="card-header">
                    <h3 className="card-title">Latest Evaluation Reports</h3>
                    
                    <div className="card-tools">
                        <button type="button" className="btn btn-outline-info mr-3" onClick={() => setViewLogModalOpened(true)}>
                            <FontAwesomeIcon icon={faFile} className="fas nav-icon" /> View Dory Evaluation Logs
                        </button>
                        <span>Page {pageIndex + 1}&ensp;</span>
                        <HelpMark title={mayHaveMorePreviousReports ? "Older page" : "No more older reports."}>
                            <button type="button" disabled={!mayHaveMorePreviousReports} className="btn btn-outline-primary" onClick={previousBtnClick}>
                                <FontAwesomeIcon icon={faAngleLeft} className="fas nav-icon" />
                            </button>
                        </HelpMark>
                        <HelpMark title={pageIndex === 0 ? "Already at the latest page." : "Newer page"}>
                            <button type="button" disabled={pageIndex === 0} className="btn btn-outline-primary" onClick={nextBtnClick}>
                                <FontAwesomeIcon icon={faAngleRight} className="fas nav-icon" />
                            </button>
                        </HelpMark>
                    </div>
                </div>
                <div className="card-body p-0">
                    {error ? <span>{error}</span>
                        : <>
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Status</th>
                                        <th>Time</th>
                                        <th>Expected Value</th>
                                        <th>Current Value</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {reportRows}
                                </tbody>
                            </table>
                        </>
                    }
                </div>
            </div>
            <ResponsiveModal
                open={viewLogModalOpened}
                onClose={() => setViewLogModalOpened(false)}
            >
                <MaturityItemDoryResult
                    project_id={project_id}
                    item_code={item_code}
                />
            </ResponsiveModal>
        </>
    )
}

function ReportRow({ expanded = false, report, onClick = () => { } }) {

    function isPassed() {
        return report?.status === 'P'
    }

    return <>
        <tr data-widget="expandable-table" aria-expanded={expanded} onClick={onClick} className={styles.itemTableRow}>
            <td><FontAwesomeIcon icon={isPassed() ? faCheck : faTimes}
                className={"text-" + (isPassed() ? "primary" : "danger")} /></td>
            <td>{utils.convertIsoTimestampToJalali(report.latest_evaluation_time)}</td>
            <td>{utils.getReadableValueByType(report.expected_value ?? "N/A", report.value_type)}</td>
            <td>{utils.getReadableValueByType(report.current_value ?? "N/A", report.value_type)}</td>
        </tr>
        <tr className={"expandable-body" + (expanded ? "" : " d-none")}>
            <td colSpan="5">
                {report.description ?
                    <>
                        <label>Description</label>
                        <textarea className="form-control-plaintext"
                                placeholder="No description."
                                style={{height: '100px'}}
                                readOnly>{report.description}</textarea>
                    </>
                    : <p className="text-muted">No description.</p>
                }
            </td>
        </tr>
    </>
}