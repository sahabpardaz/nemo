import React, {useEffect, useState} from "react"
import { toast } from 'react-toastify'
import apiURLs from '../../../apiURLs'
import utils from '../../../utils'
import InlineForm, { parseErrors } from '../InlineForm'
import {ModalManager} from "react-dynamic-modal"
import DeleteModal from "../../DeleteModal"


export default (props) => {
    const { maturityModelItemId, project_id, onSuccess, latestPendingEvaluationRequestId } = props
    const [ fieldValue, setFieldValue ] = useState("")
    const [ errors, setErrors ] = useState(null)

    let cardTitle = "Request to evaluate item"
    if (latestPendingEvaluationRequestId != null)
        cardTitle = "Current evaluation request"

    useEffect(() => {
        if (latestPendingEvaluationRequestId != null) {
            getEvaluationRequestDescription(latestPendingEvaluationRequestId).then((desc) => setFieldValue(desc))
        } else {
            setFieldValue("")
        }
    }, [latestPendingEvaluationRequestId])

    function onSubmit(event) {
        event.preventDefault()
        if (latestPendingEvaluationRequestId == null)
            createEvaluationRequest()
        else
            updateEvaluationRequest()
    }

    function createEvaluationRequest() {
        let apiUrl, method, successMessage, body
        apiUrl = apiURLs.evaluationRequestList(project_id)
        method = 'POST'
        successMessage = "Evaluation request has been sent."
        body = {
            'maturity_model_item': maturityModelItemId,
            'description': fieldValue,
        }
        request(apiUrl, method, successMessage, body)
    }

    function updateEvaluationRequest() {
        let apiUrl, method, successMessage, body
        apiUrl = apiURLs.evaluationRequest(project_id, latestPendingEvaluationRequestId)
        method = 'PATCH'
        successMessage = "Evaluation request has been edited."
        body = {
            'description': fieldValue,
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
                deleteURL={apiURLs.evaluationRequest(project_id, latestPendingEvaluationRequestId)}
                modelTitle={latestPendingEvaluationRequestId}
                modelTypeName="evaluation request"
                onSuccessful={() => onSuccess()}
            />
        )
    }

    async function getEvaluationRequestDescription(evaluationRequestId) {
        let jsonResult = await utils.request(apiURLs.evaluationRequest(project_id, evaluationRequestId), 'GET', null, true)
        return jsonResult.description
    }

    return (
        <InlineForm
            cardTitle={cardTitle}
            fieldErrors={errors}
            fieldValue={fieldValue}
            fieldPlaceholder="Reason that you think this item should be pass ..."
            setFieldValue={setFieldValue}
            onSubmit={onSubmit}
            onDelete={latestPendingEvaluationRequestId ? () => openDeleteModal() : null}
        />
    )
}
