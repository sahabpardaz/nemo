import apiURLs from "../../apiURLs"
import ChartAbs from './ChartAbs'
import utils from '../../utils'

export default class DailyCoverageChart extends ChartAbs {

    constructor(props) {
        super(props, 'daily-coverage', 'Daily Coverage')
    }

    formatYAxisValue(value) {
        return utils.getFormatedPercentage(value) + "%"
    }

    async fetchData() {
        this.setState({loading: true})
        let datasets = []
        let labels
        let data = await utils.requestGET(
            apiURLs.projectGraphURLForDailyCoverage(
                this.props.projectId,
                this.props.fromDate,
                this.props.toDate,
                this.props.checkingPeriodDays
            ), true)
        const coverageTypes = [
            {
                key: "overall",
                label: "Overall Coverage",
                color: "green"
            },
            {
                key: "incremental",
                label: "Incremental Coverage",
                color: "orange"
            }
        ]
        for (const coverageType of coverageTypes) {
            if (!labels)
                labels = data[coverageType.key].map(d => utils.convertIsoTimestampToJalali(d.date, false))
            datasets.push({
                label: coverageType.label,
                data: data[coverageType.key].map(d => d.value),
                fill: false,
                borderColor: coverageType.color,
            })
        }
        this.setState({
            labels: labels ?? [],
            datasets: datasets,
            loading: false,
        })
    }

}