import React from 'react'
import MaturityModelItemRow from './MaturityModelItemRow'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faAngleDown } from "@fortawesome/free-solid-svg-icons"
import HelpMark from './HelpMark'


export default (props) => {
    const { id, maturityLevel, maturityLevelState, openModal, isSnapshot } = props

    return (
        //Todo :
        // <div class={this.props.achieved === 'true' ? "card card-success card-outline collapsed-card" : "card"}>
        <div className="card card-outline">
            <div className="card-header">
                <h3 className="card-title">
                    {maturityLevel.name}
                    {(maturityLevel.description) &&
                        <HelpMark title={maturityLevel.description} />}
                </h3>
                <div className="card-tools">
                    <button type="button" className="btn btn-tool" data-card-widget="collapse">
                        <FontAwesomeIcon icon={faAngleDown} />
                    </button>
                </div>
            </div>
            <div className="card-body p-0">
                <table className="table">
                    <thead>
                        <tr>
                            <th style={{ width: "10%" }}>Code</th>
                            <th>Name</th>
                            <th style={{ width: "15%" }}></th>
                            <th style={{ width: "8%" }}>Status</th>
                        </tr>
                    </thead>
                    <MaturityModelItemRow
                        maturityItems={maturityLevel.items}
                        maturityItemStates={maturityLevelState?.maturity_item_states}
                        key={maturityLevel.items}
                        id={id}
                        openModal={openModal}
                        isSnapshot={isSnapshot}
                    />
                </table>
            </div>
        </div>
    )
}
