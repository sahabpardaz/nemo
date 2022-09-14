import React from 'react'
import { faPercent, faRetweet, faServer, faTag } from "@fortawesome/free-solid-svg-icons"
import Error from "./Error"
import HelpTexts from '../constants/HelpTexts'
import apiURLs from '../apiURLs'
import utils from '../utils'
import Tile from "./Tile"
import { Col } from "react-bootstrap"
import HelpMark from "./HelpMark"
import ReactTooltip from "react-tooltip"

class DevOpsMetricsWidget extends React.Component {

    static get defaultProps() {
        return {
            checking_period_days: window.AppConfig.DEFAULT_CHECKING_PERIOD_DAYS
        }
    }

    constructor(props) {
        super(props)
        this.state = {
            error: null,
            loading: true,
            devops_metrics: {
                "lead_time": "Loading ...",
                "time_to_restore": "Loading ...",
                "change_failure_rate": "Loading ...",
                "deployment_frequency": "Loading ..."
            }
        }

        this.componentDidMount = this.componentDidMount.bind(this)
        this.componentDidUpdate = this.componentDidUpdate.bind(this)
        this.updateDevOpsMetrics = this.updateDevOpsMetrics.bind(this)
    }

    componentDidMount() {
        this.updateDevOpsMetrics()
    }

    componentDidUpdate(prevProps) {
        let currentProjectId = this.props.project_id
        let currentEnvironmentId = this.props.environment_id
        let checkingPeriodDays = this.props.checking_period_days

        if (
            currentProjectId !== prevProps.project_id ||
            currentEnvironmentId !== prevProps.environment_id ||
            checkingPeriodDays !== prevProps.checking_period_days
        ) {
            this.setState({
                error: null,
                loading: true
            }, this.updateDevOpsMetrics)
        }

        ReactTooltip.rebuild()
    }

    updateDevOpsMetrics() {
        if (this.props.environment_id) {
            let devopsmetrics_statistics_url = new URL(apiURLs.devopsMetricsStatistics(this.props.project_id, this.props.environment_id))
            devopsmetrics_statistics_url.search = new URLSearchParams({ checking_period_days: this.props.checking_period_days })
            utils.requestGET(devopsmetrics_statistics_url, {
                "lead_time": "Failed to load!",
                "time_to_restore": "Failed to load!",
                "change_failure_rate": "Failed to load!",
                "deployment_frequency": "Failed to load!"
            }).then(result => {
                this.setState({
                    error: null,
                    loading: false,
                    devops_metrics: result
                })
            })
        }
    }

    __add_deploy_not_enough_explanation_if_needed(metricValue) {
        const DEPLOYMENT_NOT_ENOUGH_MSG = 'Deployments not enough to calculate.'
        // TODO: The below dummy-check is gonna switch to a more clean way of determining the widget status, when issue #11983 is fixed.
        if (metricValue === DEPLOYMENT_NOT_ENOUGH_MSG)
            return (
                <HelpMark
                    title={`There are not enough reported deployments in the last ${this.props.checking_period_days} days. Please try reporting your deployments`}>
                    {DEPLOYMENT_NOT_ENOUGH_MSG}
                </HelpMark>
            )
        else
            return metricValue
    }

    render() {
        if (this.state.error) {
            return (
                <Error error={this.state.error} />
            )
        }

        const lead_time = this.__add_deploy_not_enough_explanation_if_needed(utils.getFormatedTimeDuration(this.state.devops_metrics.lead_time))
        const deployment_frequency = this.__add_deploy_not_enough_explanation_if_needed(utils.getFormatedTimeDuration(this.state.devops_metrics.deployment_frequency))
        const time_to_restore = this.__add_deploy_not_enough_explanation_if_needed(utils.getFormatedTimeDuration(this.state.devops_metrics.time_to_restore))
        const change_failure_rate = this.__add_deploy_not_enough_explanation_if_needed(utils.getFormatedPercentage(this.state.devops_metrics.change_failure_rate))

        return (
            <>
                <Col>
                    <Tile
                        title="Lead Time"
                        title_help_text={HelpTexts.LEAD_TIME}
                        content={lead_time}
                        loading={this.state.loading}
                        icon={faTag}
                    />
                </Col>
                <Col>
                    <Tile
                        title="Deployment Frequency"
                        title_help_text={HelpTexts.DEPLOYMENT_FREQUENCY}
                        content={deployment_frequency}
                        loading={this.state.loading}
                        icon={faServer}
                    />
                </Col>
                <Col>
                    <Tile
                        title="Change Failure Rate"
                        title_help_text={HelpTexts.CHANGE_FAILURE_RATE}
                        content={change_failure_rate}
                        loading={this.state.loading}
                        icon={faPercent}
                    />
                </Col>
                <Col>
                    <Tile
                        title="Time To Restore"
                        title_help_text={HelpTexts.TIME_TO_RESTORE}
                        content={time_to_restore}
                        loading={this.state.loading}
                        icon={faRetweet}
                    />
                </Col>
            </>
        )
    }
}

export default DevOpsMetricsWidget