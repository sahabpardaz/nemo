import React, { useState } from 'react'
import { withRouter } from "react-router-dom"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faArrowLeft, faCalendarAlt } from "@fortawesome/free-solid-svg-icons"
import { DatetimePickerTrigger } from 'imrc-datetime-picker'
import moment from 'moment-jalaali'
import apiURLs from '../../../apiURLs'
import utils from '../../../utils'
import ListView from './ListView'
import InputWithError from "../../../components/InputWithError"
import sharedUtils from './sharedUtils'
import { FULL_DATETIME_J } from '../../../utils/moment_formats'


export default withRouter((props) => {

    const [id, setId] = useState(null)
    const [changeListId, setChangeListId] = useState(null)
    const [title, setTitle] = useState(null)
    const [commitHash, setCommitHash] = useState(null)
    const [time, setTime] = useState(moment().format(FULL_DATETIME_J))
    const [loading, setLoading] = useState(true)
    const [errors, setErrors] = useState({})

    utils.useEffectAsync(async () => {
        if (sharedUtils.isEditMode(props)) {
            const { project_id, report_id } = props.match.params
            const url = apiURLs.devopsMetricsChangeList(project_id, report_id)

            const jsonResult = await utils.requestGET(url, true, { time: moment(), status: 'U' })
            const time = moment(jsonResult.time).format(FULL_DATETIME_J)
            setId(report_id)
            setChangeListId(jsonResult.change_list_id)
            setTitle(jsonResult.title)
            setTime(time)
            setCommitHash(jsonResult.commit_hash)
        }
        setLoading(false)
    })

    async function handleSave(event) {
        const listUrl = apiURLs.devopsMetricsChangeListsList(props.match.params.project_id)
        const body = {
            change_list_id: changeListId,
            title: title,
            commit_hash: commitHash,
            time: moment(time, FULL_DATETIME_J, true),
        }
        await sharedUtils.saveReport(props, body, setErrors, ListView.TAB_CHANGE_LIST_REPORT, listUrl, id)
    }

    return (
        <div className="card card-primary">
            <div className="card-header">
                <h4 className="card-title">
                    {loading ?
                        'Loading...'
                        : (sharedUtils.isEditMode(props) ?
                            `Edit ChangeList Report ${id}`
                            : 'Add New ChangeList Report')}
                </h4>
                <button className="close" onClick={sharedUtils.getBackToReportListFunc(props, ListView.TAB_CHANGE_LIST_REPORT)}>
                    <FontAwesomeIcon icon={faArrowLeft} />
                </button>
            </div>
            <div className="card-body">
                {errors.non_field_errors &&
                    <div class="callout callout-danger">
                        {errors.non_field_errors}
                    </div>
                }
                <div className="form-group">
                    <label>ID</label>
                    <InputWithError className="form-control" placeholder="Changelist identifier"
                        value={changeListId} onChange={event => setChangeListId(event.target.value)}
                        error={errors.change_list_id} />
                </div>
                <div className="form-group">
                    <label>Title</label>
                    <InputWithError className="form-control" placeholder="Changelist title"
                        value={title} onChange={event => setTitle(event.target.value)}
                        error={errors.title} />
                </div>

                <div className="form-group">
                    <label>Commit hash</label>
                    <InputWithError className="form-control" placeholder="Commit hash"
                        value={commitHash} onChange={event => setCommitHash(event.target.value)}
                        error={errors.commit_hash} />
                </div>
                <div className="form-group">
                    <label>Time</label>
                    <DatetimePickerTrigger
                        appendToBody={true}
                        moment={moment(time, FULL_DATETIME_J)}
                        onChange={value => setTime(value.format(FULL_DATETIME_J))}
                        isSolar={true}
                        closeOnSelectDay={false}>

                        <div className="input-group">
                            <div className="input-group-prepend">
                                <span className="input-group-text"><FontAwesomeIcon icon={faCalendarAlt} /></span>
                            </div>
                            <InputWithError type="text"
                                className="form-control float-right"
                                value={time}
                                onChange={e => setTime(e.target.value)}
                                error={errors.time}
                            />
                        </div>
                    </DatetimePickerTrigger>
                </div>
            </div>
            <div className="card-footer justify-content-between">
                <button type="button" disabled={loading} className="btn btn-primary" onClick={handleSave}>
                    Save
                    </button>
            </div>
        </div>
    )
})
