import React from "react"
import { getColorFromFailureToSuccessColorsByPercentage } from "../utils/color_percentage"


export const LevelStatus = (props) => {
    const { name, passed_items_count, all_items_count } = props

    const percentage = 100 * passed_items_count / all_items_count
    const color = getColorFromFailureToSuccessColorsByPercentage(percentage)

    return (
        <div class="progress-group">
            <span class="progress-text">{name}</span>
            <span class="float-right"><b>{passed_items_count}</b>/{all_items_count} Items</span>
            <div class="progress progress-sm">
                <div class="progress-bar" style={{ width: `${percentage}%`, backgroundColor: color }}></div>
            </div>
        </div>
    )
}


export default (props) => {
    const { projectMaturityState } = props

    const levelStatus = []
    for (const maturityLevelState of projectMaturityState.maturity_level_states) {
        let enabled_items_count = 0
        let enabled_passed_items_count = 0
        for (const maturityItemState of maturityLevelState.maturity_item_states) {
            if (!maturityItemState.disabled) {
                enabled_items_count += 1
                if (maturityItemState.is_passed)
                    enabled_passed_items_count += 1
            }
        }
        levelStatus.push(
            <LevelStatus 
                name={maturityLevelState.name}
                passed_items_count={enabled_passed_items_count}
                all_items_count={enabled_items_count}
            />
        )

    }

    return (
        <div class="card">
            <div class="card-header">
                <h5 class="card-title">Maturity Model Status</h5>
            </div>
            <div class="card-body">
                {levelStatus}
            </div>
        </div>
    )
}