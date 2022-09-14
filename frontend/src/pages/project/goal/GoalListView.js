import React from 'react'
import { Link, withRouter } from 'react-router-dom'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faPlus } from "@fortawesome/free-solid-svg-icons"
import styles from "../../../css/nemo.module.css"
import 'react-circular-progressbar/dist/styles.css'
import apiURLs from '../../../apiURLs'
import utils from '../../../utils'

class GoalListView extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            loading: true,
            goals: [],
        }
    }

    componentDidUpdate(prevProps) {
        let currentProjectId = this.props.project.id
        if (currentProjectId !== prevProps.project.id) {
            this.setState({
                loading: true
            }, this.updateProjectGoalList)
        }
    }

    componentDidMount() {
        this.updateProjectGoalList()
    }

    updateProjectGoalList() {
        let project_goal_list_url = apiURLs.projectGoalsList(this.props.project.id)

        utils.requestGET(project_goal_list_url, { results: [] })
            .then((result) => {
                this.setState({
                    loading: false,
                    goals: result.results,
                })
            })
    }

    render() {
        const tableRows = []
        for (let goal of this.state.goals) {
            const levelsInvolved = []
            for (const level of goal.maturity_model_levels_involved) {
                levelsInvolved.push(
                    <div className="badge badge-pill badge-primary mr-2"
                         style={{ height: "50px", width: "50px" }}
                         key={level}>
                        <p style={{ marginTop: "17px" }}>{level}</p>
                    </div>
                )
            }

            const progress_percentage = 100 * goal.passed_maturity_model_items_count / goal.maturity_model_items.length
            let progress_color = `rgba(14, 159, 129, ${progress_percentage / 100})`
            let progress_description = `${goal.passed_maturity_model_items_count} / ${goal.maturity_model_items.length} Items Achieved`

            tableRows.push(
                <tr className={styles.itemTableRow} key={goal.id}
                    onClick={() => this.props.history.push(`/project/${this.props.project.id}/goal/${goal.id}`)}>
                    <td>
                        <ul className="list-inline">
                            {levelsInvolved}
                        </ul>
                    </td>
                    <td className="project_progress">
                        <div className="progress progress-sm">
                            <div className="progress-bar"
                                 style={{ width: `${progress_percentage}%`, backgroundColor: progress_color }}/>
                        </div>
                        <small>{progress_description}</small>
                    </td>
                    <td className="project-state">
                        <p>{utils.convertIsoTimestampToJalali(goal.due_date, false)}</p>
                    </td>
                    <td className="project-state">
                        <h6>{goal.creator}</h6>
                    </td>
                </tr>
            )
        }

        return (
            <div className="card">
                {(this.props.project.loading || this.state.loading) && <div className="overlay dark"/>}
                <div className="card-header">
                    <h3 className="card-title">Goals</h3>
                    <div className="card-tools">
                        <button type="button" className="btn btn-tool" data-card-widget="collapse" data-toggle="tooltip" title="Collapse">
                            <i className="fas fa-minus"></i></button>
                        <button type="button" className="btn btn-tool" data-card-widget="remove" data-toggle="tooltip" title="Remove">
                            <i className="fas fa-times"></i></button>
                    </div>
                </div>
                <div className="card-body p-0">
                    <table className="table projects">
                        <thead>
                        <tr>
                            <th>Levels Involved</th>
                            <th style={{ width: "30%" }}>Progress</th>
                            <th style={{ width: "8%" }} className={`text-center ${styles.dateColumn}`}>Due Date</th>
                            <th style={{ width: "8%" }} className="text-center">Creator</th>
                        </tr>
                        </thead>
                        <tbody>
                        {tableRows.length != 0 ? tableRows :
                            <tr className={styles.itemTableRow}>
                                <td className="project-state" colSpan="4">
                                    <h6>No goals found to show ...</h6>
                                </td>
                            </tr>
                        }
                        </tbody>
                    </table>
                </div>
                <div className="card-footer clearfix">
                    <Link to={`/project/${this.props.project.id}/goal/new`}>
                        <button type="button" className="btn btn-secondary btn-sm float-right">
                            <FontAwesomeIcon className="fas" icon={faPlus}/>
                            New Goal
                        </button>
                    </Link>
                </div>
            </div>
        )
    }
}

export default withRouter(GoalListView)