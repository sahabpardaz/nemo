import React, { useState, useEffect } from "react"
import { toast } from 'react-toastify'
import apiURLs from '../../../apiURLs'
import utils from '../../../utils'
import InlineForm, { parseErrors } from '../InlineForm'
import {ModalManager} from "react-dynamic-modal"
import DeleteModal from "../../DeleteModal"


export default (props) => {
    const { maturityModelItemId, disabled, project_id, onSuccess, latestPendingToggleRequestId } = props
    const [ fieldValue, setFieldValue ] = useState("")
    const [ errors, setErrors ] = useState(null)

    const action = disabled ? "enable" : "disable"

    let cardTitle = `Request to ${action} item`
    if (latestPendingToggleRequestId != null)
        cardTitle = `Current request to ${action} item`

    useEffect(() => {
        if (latestPendingToggleRequestId != null) {
            getToggleRequestReason(latestPendingToggleRequestId).then((reason) => setFieldValue(reason))
        } else {
            setFieldValue("")
        }
    }, [latestPendingToggleRequestId])

    function onSubmit(event) {
        event.preventDefault()
        if (latestPendingToggleRequestId == null)
            createToggleRequest()
        else
            updateToggleRequest()
    }

    function createToggleRequest() {
        let apiUrl, method, successMessage, body
        apiUrl = apiURLs.toggleRequestList(project_id)
        method = 'POST'
        successMessage = `Request to ${action} item has been sent.`
        body = {
            'maturity_model_item': maturityModelItemId,
            'reason': fieldValue,
            'disable': !disabled,
        }
        request(apiUrl, method, successMessage, body)
    }

    function updateToggleRequest() {
        let apiUrl, method, successMessage, body
        apiUrl = apiURLs.toggleRequest(project_id, latestPendingToggleRequestId)
        method = 'PATCH'
        successMessage = `Request to ${action} item has been edited.`
        body = {
            'reason': fieldValue,
        }
        request(apiUrl, method, successMessage, body)
    }

    function request(apiUrl, method, successMessage, body) {
        utils.request(apiUrl, method, body, false)
            .then(jsonResult => {
                toast.success(successMessage)
                setErrors(null)
                onSuccess()
            }).catch(result => {
            if (result.response.status === 400)
                setErrors(parseErrors(result.jsonResult))
        })
    }

    const openDeleteModal = () => {
        ModalManager.open(
            <DeleteModal
                deleteURL={apiURLs.toggleRequest(project_id, latestPendingToggleRequestId)}
                modelTitle={latestPendingToggleRequestId}
                modelTypeName={`${action} request`}
                onSuccessful={() => onSuccess()}
            />
        )
    }

    async function getToggleRequestReason(toggleRequestId) {
        let jsonResult = await utils.request(apiURLs.toggleRequest(project_id, toggleRequestId), 'GET', null, true)
        return jsonResult.reason
    }

    return (
        <InlineForm 
            cardTitle={cardTitle}
            fieldErrors={errors}
            fieldValue={fieldValue}
            fieldPlaceholder={`Reason that you think this item should be ${disabled ? "enabled" : "disabled"} ...`}
            setFieldValue={setFieldValue}
            onSubmit={onSubmit}
            onDelete={latestPendingToggleRequestId ? () => openDeleteModal() : null}
        />
    )
}
