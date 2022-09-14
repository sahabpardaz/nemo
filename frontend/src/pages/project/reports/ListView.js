import React from "react"
import { withRouter } from "react-router-dom"
import DropDown from "../../../components/DropDown"
import { toast } from 'react-toastify'
import utils from '../../../utils'
import Tabs from "react-bootstrap/Tabs"
import Tab from "react-bootstrap/Tab"
import ServiceStatusReports from "../../../components/reports/ServiceStatusReports"
import DeploymentReports from "../../../components/reports/DeploymentReports"
import ChangeListReports from "../../../components/reports/ChangeListReports"


class ListView extends React.Component {

    static get TAB_SERVICE_STATUS_REPORT() {
        return '#ServiceStatusReport'
    }

    static get TAB_DEPLOYMENT_REPORT() {
        return '#deploymentReport'
    }

    static get TAB_CHANGE_LIST_REPORT() {
        return '#changeListReport'
    }

    constructor(props) {
        super(props)

        this.state = {
            error: null,
            loading: true,
            environments: [],
            selected_env_id: null,
            selectedTab: window.location.hash || ListView.TAB_SERVICE_STATUS_REPORT,
        }
    }

    componentDidMount() {
        this._updateEnvironments()
            .then(() => this.setState({ loading: false }))
            .catch(err => {
                console.error(err)
                toast.error("Failed to update environments.")
            })
    }

    componentDidUpdate(prevProps) {
        if (prevProps.project.default_environment === null && this.props.project.default_environment !== null) {
            this.setState({selected_env_id: this.props.project.default_environment})
        }
    }

    async _updateEnvironments() {
        const environmentItems = await utils.fetchEnvironmentsAsDropdownItems(this.props.project.id)
        this.setState({
            environments: environmentItems,
            selected_env_id: this.props.project.default_environment.id,
        })
    }

    render() {
        return (
            <>
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Reports</h3>
                    </div>
                    <div className="card-body">
                        <DropDown
                            disabled={this.state.selectedTab === ListView.TAB_CHANGE_LIST_REPORT}
                            items={this.state.environments}
                            onSelectionChanged={item => this.setState({ selected_env_id: item.value })}
                            value={this.state.selected_env_id}/>
                    </div>
                </div>

                <Tabs
                    onSelect={key => this.setState({ selectedTab: key })}
                    activeKey={this.state.selectedTab}>
                    <Tab
                        eventKey={ListView.TAB_SERVICE_STATUS_REPORT}
                        title='Service Status'
                        onEntered={() => window.location.hash = ListView.TAB_SERVICE_STATUS_REPORT}>
                        <ServiceStatusReports
                            projectId={this.props.project.id}
                            environmentId={this.state.selected_env_id}
                        />
                    </Tab>
                    <Tab
                        eventKey={ListView.TAB_DEPLOYMENT_REPORT}
                        title='Deployment'
                        onEntered={() => window.location.hash = ListView.TAB_DEPLOYMENT_REPORT}>
                        <DeploymentReports
                            projectId={this.props.project.id}
                            environmentId={this.state.selected_env_id}
                        />
                    </Tab>
                    <Tab
                        eventKey={ListView.TAB_CHANGE_LIST_REPORT}
                        title='ChangeList'
                        onEntered={() => window.location.hash = ListView.TAB_CHANGE_LIST_REPORT}>
                        <ChangeListReports
                            projectId={this.props.project.id}
                        />
                    </Tab>
                </Tabs>
            </>
        )
    }
}

export default withRouter(ListView)