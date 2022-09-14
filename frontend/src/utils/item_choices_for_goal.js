export const get_goal_item_choices_from_maturity_model = (maturityLevelStates) => {
    let choices = []
    for (const maturityLevelState of maturityLevelStates) {
        let children = []
        let maturityItemIds = []
        for (const maturityItemState of maturityLevelState.maturity_item_states) {
            const has_pending_eval_request = !!maturityItemState.latest_pending_evaluation_request_id
            if (maturityItemState.disabled || has_pending_eval_request)
                continue
            maturityItemIds.push(maturityItemState.maturity_item.id)
            children.push(
                {
                    label: `[${maturityItemState.maturity_item.code}] ${maturityItemState.maturity_item.name}`,
                    ids: [maturityItemState.maturity_item.id],
                }
            )
        }
        if (children.length === 0)
            continue
        choices.push(
            {
                label: maturityLevelState.name,
                children: children,
                ids: maturityItemIds,
            }
        )
    }
    return choices
}