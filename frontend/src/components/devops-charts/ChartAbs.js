import React from "react"
import { Line } from 'react-chartjs-2'
import utils from "../../utils"
import apiURLs from "../../apiURLs"
import Spinner from 'react-bootstrap/Spinner'
import _ from 'lodash'

export default class ChartAbs extends React.Component {

    constructor(props, metricName, metricTitle) {
        super(props)
        this.metricName = metricName
        this.metricTitle = metricTitle
        this.state = {
            labels: [],
            datasets: [],
            loading: true
        }
        this.canvasRef = React.createRef()
        this.fetchData = utils.debounce(this.fetchData, 700, this)
    }

    formatYAxisValue(value) {
        utils.throwAbstractMethodNotImplemented()
    }

    componentDidUpdate(prevProps) {
        if (!_.isEqual(prevProps.environments, this.props.environments)
            || prevProps.fromDate !== this.props.fromDate
            || prevProps.toDate !== this.props.toDate
            || prevProps.checkingPeriodDays !== this.props.checkingPeriodDays
            || !prevProps.isSelected) {
            if (this.props.isSelected) {
                this.fetchData()
            }
        }
    }

    getChartData() {
        return {
            labels: this.state.labels,
            datasets: this.state.datasets
        }
    }

    getChartOptions() {
        return {
            scales: {
                yAxes: [{
                    ticks: {
                        suggestedMin: 0,
                        callback: this.formatYAxisValue
                    },
                }],
            },
            tooltips: {
                enabled: true,
                callbacks: {
                    label: (tooltipItem, data) => {
                        const label = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index]
                        return this.formatYAxisValue(label)
                    }
                }
            },
        }
    }

    async fetchData() {
        this.setState({loading: true})
        let datasets = []
        let labels
        for (const environment of this.props.environments) {
            let data = await utils.requestGET(
                apiURLs.devopsMetricsChartURL(this.metricName,
                    this.props.projectId,
                    environment.value,
                    this.props.fromDate,
                    this.props.toDate,
                    this.props.checkingPeriodDays
                ), true)

            if (!labels)
                labels = data.map(d => utils.convertIsoTimestampToJalali(d.date, false))

            datasets.push({
                label: environment.label,
                data: data.map(d => d.value),
                fill: false,
                borderColor: environment.color,
            })
        }
        this.setState({
            labels: labels ?? [],
            datasets: datasets,
            loading: false,
        })
    }

    render() {
        if (this.state.loading === true)
            return (
                <Spinner animation="border" />
            )
        else
            return (
                <Line
                    data={this.getChartData()}
                    options={this.getChartOptions()}
                />
            )
    }
}
