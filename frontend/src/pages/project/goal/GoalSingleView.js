import React, { useEffect, useState } from 'react'
import { Link, Route, useHistory, useParams } from "react-router-dom"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faEdit, faTrash } from "@fortawesome/free-solid-svg-icons"
import { buildStyles, CircularProgressbarWithChildren } from 'react-circular-progressbar'
import 'react-circular-progressbar/dist/styles.css'
import DeleteModal from '../../../components/DeleteModal'
import { ModalManager } from 'react-dynamic-modal'
import Error from '../../../components/Error'
import CreateUpdateGoal, { UpdateMode } from './CreateUpdateGoal'
import apiURLs from '../../../apiURLs'
import utils from '../../../utils'
import { get_goal_item_choices_from_maturity_model } from "../../../utils/item_choices_for_goal"
import MaturityModelLevel from '../../../components/MaturityModelLevel'

export default (props) => {
    const history = useHistory()
    const { project_id, goal_id } = useParams()
    const { maturityLevels, maturityLevelStates, onGoalChanged } = props
    const [errorMessage, setErrorMessage] = useState()
    const [loaded, setLoaded] = useState(false)
    const [goal, setGoal] = useState()

    const fetchGoal = () => {
        let project_goal_single_url = apiURLs.projectGoal(project_id, goal_id)

        utils.requestGET(project_goal_single_url)
            .then(result => {
                setGoal(result)
                setLoaded(true)
                setErrorMessage()
            })
            .catch(() => {
                setErrorMessage("Failed to load project goal info from server.")
                setLoaded(true)
            })
    }

    useEffect(fetchGoal, [project_id, goal_id])

    const openDeleteGoalModal = () => {
        ModalManager.open(
            <DeleteModal
                deleteURL={apiURLs.projectGoal(project_id, goal.id)}
                modelTitle={goal.id}
                modelTypeName="Goal"
                onSuccessful={() => {
                    onGoalChanged()
                    history.push(`/project/${project_id}/goal`)
                }}
            />
        )
    }

    if (!loaded) {
        return (
            <p>Loading ...</p>
        )
    }

    if (errorMessage) {
        return (
            <Error error={errorMessage}/>
        )
    }

    let choices = get_goal_item_choices_from_maturity_model(maturityLevelStates)

    const levelComponents = []
    for (let i = 0; i < maturityLevels.length; i++) {
        const maturityLevelState = maturityLevelStates[i]
        const maturityLevel = maturityLevels[i]
        let maturityLevelStateInGoal = JSON.parse(JSON.stringify(maturityLevelState))
        let maturityLevelInGoal = JSON.parse(JSON.stringify(maturityLevel))
        maturityLevelStateInGoal.maturity_item_states = maturityLevelState.maturity_item_states
            .filter(itemState => goal.maturity_model_items.includes(itemState.id))
        maturityLevelInGoal.items = maturityLevel.items
            .filter(item => goal.maturity_model_items.includes(item.id))
        if (maturityLevelStateInGoal.maturity_item_states.length === 0)
            continue
        for (const i of maturityLevelStateInGoal.maturity_item_states)
            i.closest_goal = null

        levelComponents.push(
            <MaturityModelLevel
                maturityLevel={maturityLevelInGoal}
                maturityLevelState={maturityLevelStateInGoal}
                key={maturityLevelState}/>
        )
    }

    return (
        <>
            <Route exact path="/project/:project_id(\d+)/goal/:goal_id(\d+)/edit">
                <CreateUpdateGoal
                    mode={UpdateMode}
                    goal_id={goal.id}
                    due_date={goal.due_date}
                    targeted_items={goal.maturity_model_items}
                    creation_time={goal.creation_time}
                    project_id={project_id}
                    options={choices}
                    onSuccessful={() => {
                        onGoalChanged()
                        setLoaded(false)
                        fetchGoal()
                    }}
                />
            </Route>
            <Route exact path="/project/:project_id(\d+)/goal/:goal_id(\d+)">
                <div className="container-fluid">
                    <div className="row">
                        <div className="col-md-2">
                            <div className="card">
                                <div className="card-body box-profile">
                                    <ul className="list-group list-group-unbordered mb-2">
                                        <div className="text-center">
                                            <CircularProgressbarWithChildren
                                                value={goal.passed_maturity_model_items_count}
                                                maxValue={goal.maturity_model_items.length}
                                                styles={buildStyles({
                                                    strokeLinecap: 'butt',
                                                    textSize: '16px',
                                                    pathColor: '#0e9f81',
                                                })}>
                                                <h3 className="profile-username text-center">
                                                    {goal.passed_maturity_model_items_count} / {goal.maturity_model_items.length}
                                                </h3>
                                            </CircularProgressbarWithChildren>
                                            <p className="text-muted text-center">Items Achieved</p>
                                        </div>
                                        <li className="list-group-item">
                                            <b>Status</b> <a className="float-right">{goal.status}</a>
                                        </li>
                                        <li className="list-group-item">
                                            <b>Due Date</b> <a className="float-right">{utils.convertIsoTimestampToJalali(goal.due_date, false)}</a>
                                        </li>
                                        <li className="list-group-item">
                                            <b>Creation Time</b> <a className="float-right">{utils.convertIsoTimestampToJalali(goal.creation_time, false)}</a>
                                        </li>
                                        <li className="list-group-item">
                                            <b>Creator</b> <a className="float-right">{goal.creator}</a>
                                        </li>
                                    </ul>

                                    <Link to={`/project/${project_id}/goal/${goal_id}/edit`}>
                                        <button type="button" className="btn btn-default btn-block">
                                            <FontAwesomeIcon icon={faEdit} className="mr-2"/>
                                            Edit
                                        </button>
                                    </Link>
                                    <button type="button" className="btn btn-default btn-block" onClick={openDeleteGoalModal}>
                                        <FontAwesomeIcon icon={faTrash} className="mr-2"/>
                                        Delete
                                    </button>
                                </div>

                            </div>
                        </div>
                        <div className="col-md-10">
                            {levelComponents}
                        </div>
                    </div>
                </div>
            </Route>
        </>
    )
}
