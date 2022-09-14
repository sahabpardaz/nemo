import ChartAbs from './ChartAbs'
import utils from '../../utils'

export default class ChangeFailureRateChart extends ChartAbs {

    constructor(props) {
        super(props, 'change-failure-rate', 'Change Failure Rate')
    }

    formatYAxisValue(value) {
        return utils.getFormatedPercentage(value) + "%"
    }
}