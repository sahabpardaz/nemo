import React from "react"
import { faPlus } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { Link } from "react-router-dom"
import InfiniteScroll from "react-infinite-scroller"
import utils from "../../utils"
import { toast } from "react-toastify"

export default class ReportsAbs extends React.Component {

    static get defaultProps() {
        return {
            itemsPerFetch: 10
        }
    }

    constructor(props) {
        super(props)
        if (new.target === ReportsAbs)
            throw new TypeError("ReportsAbs class is abstract")

        this.state = {
            reports: [],
            hasMoreReports: true,
        }

        this._onReportDeleted = this._onReportDeleted.bind(this)
        this._loadMoreReports = this._loadMoreReports.bind(this)
    }

    getReportsURL() {
        utils.throwAbstractMethodNotImplemented()
    }

    getNewReportPageURL() {
        utils.throwAbstractMethodNotImplemented()
    }

    getItemsListComponent() {
        utils.throwAbstractMethodNotImplemented()
    }

    componentDidUpdate(prevProps, prevState) {
        if (
            prevProps.environmentId !== this.props.environmentId ||
            prevProps.projectId !== this.props.projectId
        ) {
            // noinspection JSIgnoredPromiseFromCall
            this._reloadReports()
        }
    }

    componentDidMount() {
        if (this.propsLoaded()) {
            // noinspection JSIgnoredPromiseFromCall
            this._reloadReports()
        }
    }

    _onReportDeleted(report) {
        this.setState((state, props) => {
            const reports = []
            for (let r of state.reports) {
                if (r.id !== report.id)
                    reports.push(r)
            }
            return {reports: reports}
        })
    }

    propsLoaded() {
        return !!(this.props.projectId && this.props.environmentId)
    }

    async _reloadReports() {
        if (!this.propsLoaded()) {
            this.setState({reports: [], hasMoreReports: false})
        } else {
            const jsonResp = await utils.requestGET(`${this.getReportsURL()}?limit=${this.props.itemsPerFetch}`)
            this.setState({reports: jsonResp.results, hasMoreReports: !!jsonResp.next})
        }
    }

    async _loadMoreReports() {
        if (!this.propsLoaded())
            return
        this.setState({hasMoreReports: false})
        const currentReports = this.state.reports
        try {
            const jsonResp = await utils.requestGET(`${this.getReportsURL()}?limit=${this.props.itemsPerFetch}&offset=${currentReports.length}`)
            this.setState({
                reports: currentReports.concat(jsonResp.results),
                hasMoreReports: !!jsonResp.next
            })
        } catch (err) {
            console.error(err)
            toast.error("Failed to load more reports. Error: " + err.message)
        }
    }

    render() {
        return (
            <div className="card">
                <div className="card-header">
                    <Link to={this.getNewReportPageURL()}>
                        <button type="button" className="btn btn-primary btn-sm float-right">
                            <FontAwesomeIcon className="fas" icon={faPlus}/>
                            New Report
                        </button>
                    </Link>
                </div>
                <div className="card-body p-0">
                    <InfiniteScroll
                        pageStart={0}
                        loadMore={this._loadMoreReports}
                        hasMore={this.state.hasMoreReports}
                        loader={<h4 key="-1">Loading ...</h4>}>
                        {this.getItemsListComponent()}
                    </InfiniteScroll>
                </div>
            </div>
        )
    }
}
