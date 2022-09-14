import React from 'react'
import { withRouter } from 'react-router-dom'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faCalendarAlt, faArrowLeft } from "@fortawesome/free-solid-svg-icons"
import apiURLs from '../../../apiURLs'
import moment from 'moment-jalaali'
import { toast } from 'react-toastify'
import DropdownTreeSelect from "react-dropdown-tree-select"
import "imrc-datetime-picker/dist/imrc-datetime-picker.css"
import { DatetimePicker } from 'imrc-datetime-picker'
import utils from '../../../utils'


export const CreateMode = "CREATE"
export const UpdateMode = "UPDATE"

class CreateUpdateGoal extends React.Component {
    constructor(props) {
        super()

        let creation_time = moment()
        if (props.mode === UpdateMode) {
            creation_time = moment(props.creation_time)
        }

        let due_date = creation_time.clone().add(1, 'days')
        if (props.mode === UpdateMode) {
            due_date = moment(props.due_date)
        }

        this.state = {
            mode: props.mode === UpdateMode ? UpdateMode : CreateMode,
            targeted_items: props.targeted_items ? props.targeted_items : [],
            options: props.options,
            due_date: due_date,
            creation_time: creation_time,
            errors: null,
        }
        this.backUrl = props.mode === UpdateMode ?
            `/project/${props.project_id}/goal/${props.goal_id}` :
            `/project/${props.project_id}/goal`

        this.backToGoalList = this.backToGoalList.bind(this)
        this.onTargetedItemsChanged = this.onTargetedItemsChanged.bind(this)
    }

    componentDidUpdate(prevProps) {
        let currentOptions = this.props.options
        if (currentOptions !== prevProps.options) {
            this.setState({
                options: currentOptions
            })
        }
    }

    handleSubmit(event) {
        event.preventDefault()
        let url
        let method
        let successful_status_code
        let successful_message
        if (this.state.mode === UpdateMode) {
            url = apiURLs.projectGoal(this.props.project_id, this.props.goal_id)
            method = 'PUT'
            successful_message = `Goal ${this.props.goal_id} was edited.`
        } else {
            url = apiURLs.projectGoalsList(this.props.project_id)
            method = 'POST'
            successful_message = "New goal was added."
        }
        this.requestServer(url, method, successful_message)
    }

    requestServer(url, method, successful_message) {
        let dueDate = this.state.due_date.format('YYYY-MM-DD')

        utils.request(url, method, {
            'due_date': dueDate,
            'maturity_model_items': this.state.targeted_items
        }, false).then(jsonResult => {
            this.props.onSuccessful()
            this.backToGoalList()
            toast.success(successful_message)
        }).catch(result => {
            if (result.response?.status == 400)
                this.setState({ errors: result.jsonResult })
        })
    }

    backToGoalList() {
        this.props.history.push(this.backUrl)
    }

    onTargetedItemsChanged(currentNode, selectedNodes) {
        const itemIds = []
        for (const node of selectedNodes) {
            itemIds.push(...node.ids)
        }
        this.setState({ targeted_items: itemIds })
    }


    render() {
        const { mode, due_date, options, targeted_items, creation_time } = this.state
        const errors = []
        for (const error in this.state.errors) {
            errors.push(
                <p key={errors.length}>
                    <b>{error} : </b>
                    {this.state.errors[error]}
                </p>
            )
        }

        // Apply targeted items to item targeting options
        for (const level of options) {
            for (const item of level.children) {
                if (targeted_items.includes(item.ids[0]))
                    item.checked = true
                else
                    item.checked = false
            }
        }

        let minDate = creation_time.clone().add(1, 'days')

        return (
            <div className="card card-primary">
                <div className="card-header">
                    <h4 className="card-title">{mode.charAt(0).toUpperCase() + mode.toLowerCase().substring(1)} Goal</h4>
                    <button type="button" className="close" onClick={this.backToGoalList}>
                        <FontAwesomeIcon icon={faArrowLeft} />
                    </button>
                </div>
                <div className="card-body">
                    {this.state.errors &&
                        <div className="callout callout-danger">
                            {errors}
                        </div>
                    }
                    <div className="form-group">
                        <label>Due Date</label>
                        <div className="input-group">
                            <div className="input-group-prepend">
                                <span className="input-group-text">
                                    <FontAwesomeIcon icon={faCalendarAlt} />
                                </span>
                            </div>
                            <DatetimePicker
                                moment={due_date}
                                onChange={value => this.setState({ due_date: value })}
                                isSolar={true}
                                isOpen={true}
                                showTimePicker={false}
                                minDate={minDate}
                            />
                        </div>
                    </div>
                    <div className="form-group">
                        <label>Items</label>
                        <DropdownTreeSelect
                            data={options}
                            onChange={this.onTargetedItemsChanged}
                            showPartiallySelected='true'
                            texts={{ placeholder: 'Select ...' }}
                        />
                    </div>
                </div>
                <div className="card-footer justify-content-between">
                    <button type="button" className="btn btn-primary" onClick={event => this.handleSubmit(event)}>
                        Submit
                    </button>
                </div>
            </div>
        )
    }
}

export default withRouter(CreateUpdateGoal)
