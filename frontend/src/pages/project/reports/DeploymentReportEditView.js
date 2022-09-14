import React, { useState } from 'react'
import { withRouter } from "react-router-dom"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faArrowLeft, faCalendarAlt } from "@fortawesome/free-solid-svg-icons"
import { DatetimePickerTrigger } from 'imrc-datetime-picker'
import DropDown from '../../../components/DropDown'
import moment from 'moment-jalaali'
import apiURLs from '../../../apiURLs'
import utils from '../../../utils'
import { AsyncPaginate } from 'react-select-async-paginate'
import ListView from './ListView'
import sharedUtils from './sharedUtils'
import { FULL_DATETIME_J } from '../../../utils/moment_formats'

export default withRouter((props) => {

    const [id, setId] = useState(null)
    const [time, setTime] = useState(moment().format(FULL_DATETIME_J))
    const [status, setStatus] = useState('P')
    const [loadedChangeLists, setLoadedChangeLists] = useState([])
    const [selectedChangeListItem, setSelectedChangeListItem] = useState(null)
    const [loading, setLoading] = useState(true)
    const [errors, setErrors] = useState({})
    const [environments, setEnvironments] = useState([])
    const [selectedEnvId, setSelectedEnvId] = useState(new URLSearchParams(props.location.search).get('preferred_env'))

    utils.useEffectAsync(async () => {
        const { project_id, report_id } = props.match.params
        if (sharedUtils.isEditMode(props)) {
            const { environment_id } = props.match.params
            const url = apiURLs.devopsMetricsDeployment(project_id, environment_id, report_id)

            const jsonResult = await utils.requestGET(url, true, { time: moment(), status: 'P' })
            const time = moment(jsonResult.time).format(FULL_DATETIME_J)
            const changeListId = jsonResult.change_list
            const changeList = await utils.requestGET(apiURLs.devopsMetricsChangeList(project_id, changeListId), true, { commit_hash: "" })

            setId(report_id)
            setTime(time)
            setStatus(jsonResult.status)
            setSelectedChangeListItem(_convertToSelectItem(changeList))
            setSelectedEnvId(environment_id)
        }
        const environments = await utils.fetchEnvironmentsAsDropdownItems(project_id)
        setLoading(false)
        setEnvironments(environments)
    }, [])

    async function handleSave(event) {
        if (!selectedChangeListItem) {
            setErrors({ non_field_errors: 'No changelists selected' })
            return
        }
        const { project_id } = props.match.params
        let selectedChangeList = loadedChangeLists.find(c => c.id == selectedChangeListItem.value)
        if (!selectedChangeList)
            selectedChangeList = await utils.requestGET(apiURLs.devopsMetricsChangeList(project_id, selectedChangeListItem.value))

        const listUrl = apiURLs.devopsMetricsDeploymentsList(project_id, selectedEnvId)
        const body = {
            status: status,
            time: moment(time, FULL_DATETIME_J, true),
            commit_hash: selectedChangeList.commit_hash
        }
        await sharedUtils.saveReport(props, body, setErrors, ListView.TAB_CHANGE_LIST_REPORT, listUrl, id)
    }

    function _convertToSelectItem(changeList) {
        return {
            value: changeList.id,
            label: `(${changeList.commit_hash.substr(0, 7)}) ${changeList.title ?? ""}`
        }
    }

    async function loadOptions(search, loadedOptions) {
        const { project_id } = props.match.params
        const url = `${apiURLs.devopsMetricsChangeListsList(project_id)}?limit=7&offset=${loadedOptions.length}`
        const result = await utils.requestGET(url)
        setLoadedChangeLists(loadedChangeLists.concat(result.results))
        const items = result.results.map(_convertToSelectItem)
        return {
            options: items,
            hasMore: !!result.next,
        }
    }

    return (
        <div className="card card-primary">
            <div className="card-header">
                <h4 className="card-title">
                    {loading ?
                        'Loading...'
                        : (sharedUtils.isEditMode(props) ?
                            `Edit Deployment Report ${id}`
                            : 'Add New Deployment Report')}
                </h4>
                <button className="close" onClick={sharedUtils.getBackToReportListFunc(props, ListView.TAB_DEPLOYMENT_REPORT)}>
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
                    <label>Environment</label>
                    <div className="input-group">
                        <DropDown
                            items={environments}
                            onSelectionChanged={i => setSelectedEnvId(i.value)}
                            value={selectedEnvId}
                            disabled={sharedUtils.isEditMode(props)} />
                    </div>
                </div>
                <div className="form-group">
                    <label>Time</label>
                    <div className="input-group">
                        <input type="text"
                            value={time}
                            onChange={e => setTime(e.target.value)}
                        />
                        <DatetimePickerTrigger
                            moment={moment(time, FULL_DATETIME_J)}
                            onChange={value => setTime(value.format(FULL_DATETIME_J))}
                            isSolar={true}
                            lang="en"
                            showTimePicker={true}
                            closeOnSelectDay={false}>
                            <div className="input-group-append">
                                <span className="input-group-text">
                                    <FontAwesomeIcon icon={faCalendarAlt} />
                                </span>
                            </div>
                        </DatetimePickerTrigger>
                    </div>
                </div>
                <label>Status</label>
                <div className="form-group">
                    <DropDown
                        items={[
                            { label: 'Pass', value: 'P' },
                            { label: 'Fail', value: 'F' },
                        ]}
                        value={status}
                        onSelectionChanged={item => setStatus(item.value)} />
                </div>
                <label>ChangeList</label>
                <div className="form-group">
                    <AsyncPaginate
                        value={selectedChangeListItem}
                        loadOptions={loadOptions}
                        isSearchable={false}
                        onChange={item => setSelectedChangeListItem(item)}
                    />
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