import React, { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import ToggleRequestForm from '../../components/forms/maturity-model/ToggleRequestForm'
import EvaluationRequestForm from '../../components/forms/maturity-model/EvaluationRequestForm'
import MaturityModelItemStatusCard from '../../components/MaturityModelItemStatusCard'
import EvaluationReportsCard from '../../components/EvaluationReportsCard'
import { EvaluationTypeKind } from "../../utils/evaluationType"


export default (props) => {
    const { project, onItemChanged, projectMaturityState } = props
    const { project_id, item_id } = useParams()
    const [itemState, setItemState] = useState(null)
    const [error, setErrors] = useState("loading")

    useEffect(() => {
        let found = false
        for (const maturityLevelState of projectMaturityState.maturity_level_states) {
            for (const maturityItemState of maturityLevelState.maturity_item_states) {
                if (maturityItemState.maturity_item.id == item_id) {
                    setItemState(maturityItemState)
                    setErrors(null)
                    found = true
                }
            }
        }
        if (found == false) {
            setErrors("Item not found")
        }
    }, [project_id, item_id, projectMaturityState.maturity_level_states])

    if (error)
        return error

    return (
        <div className="container-fluid">
            <div className="row">
                <div className="col-md-12">
                    <MaturityModelItemStatusCard
                        item_id={itemState.maturity_item.id} project_id={project_id} showViewMoreButton={false}
                    />
                    <ToggleRequestForm
                        maturityModelItemId={itemState.maturity_item.id}
                        disabled={itemState.disabled}
                        project_id={project_id}
                        onSuccess={onItemChanged}
                        latestPendingToggleRequestId={itemState.latest_pending_toggle_request_id}
                    />
                    {!itemState.disabled &&
                        [
                            EvaluationTypeKind.MANUAL,
                            EvaluationTypeKind.DORY
                        ].includes(itemState.maturity_item.evaluation_type.kind) &&
                    <EvaluationRequestForm
                        maturityModelItemId={itemState.maturity_item.id}
                        project_id={project_id}
                        onSuccess={onItemChanged}
                        latestPendingEvaluationRequestId={itemState.latest_pending_evaluation_request_id}
                    />
                    }
                    <EvaluationReportsCard project_id={project_id} item_id={item_id} item_code={itemState.maturity_item.code} />
                </div>
            </div>
        </div>
    )
}