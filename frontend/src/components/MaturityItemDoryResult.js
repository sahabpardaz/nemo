import React, { useState } from 'react'
import { withRouter } from "react-router-dom"
import utils from "../utils"
import apiURLs from '../apiURLs'
import Error from './Error'
import LoadingIcon from './icons/LoadingIcon'


export default withRouter((props) => {
    const { item_code, project_id } = props
    const [doryEvaluationLog, setDoryEvaluationLog] = useState()
    const [doryEvaluationId, setDoryEvaluationId] = useState()
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState()

    function viewLog() {
        setIsLoading(true)
        utils.requestGET(apiURLs.maturtiyItemDoryResult(project_id, doryEvaluationId, item_code), false)
            .then(response => {
                setDoryEvaluationLog(response.description)
                setError()
                setIsLoading(false)
            })
            .catch((errorBundle) => {
                if (errorBundle.response?.status === 404) {
                    setDoryEvaluationLog()
                    setError("Dory evaluation not found.")
                }
                setIsLoading(false)
            })
    }

    return (
        <div className="card card-outline card-info">
            <div class="card-header">
                <h3 class="card-title">
                    <i class="fas fa-edit"></i>
                    View Dory evaluation logs for item {item_code}
                </h3>
            </div>
            <div className="card-body box-profile">
                <div className="form-group">
                    <div class="input-group">
                        <input
                            type="text" class="form-control"
                            placeholder="Dory Evaluation ID (IDs can be found in evaluation reports' descriptions)"
                            value={doryEvaluationId} onChange={e => setDoryEvaluationId(e.target.value)}
                        />
                        <span class="input-group-append">
                            <button type="button" class="btn btn-info btn-flat" onClick={viewLog}>
                                View Log
                            </button>
                        </span>
                    </div>
                    {isLoading ? <LoadingIcon /> :
                        error ? <Error error={error} /> :
                            <textarea
                                className="form-control-plaintext"
                                placeholder="No description."
                                rows="10"
                                readOnly>
                                {doryEvaluationLog}
                            </textarea>
                    }
                </div>
            </div>
        </div>
    )
})
