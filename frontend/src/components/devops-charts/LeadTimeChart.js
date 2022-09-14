import ChartAbs from './ChartAbs'
import utils from '../../utils'

export default class LeadTimeChart extends ChartAbs {

    constructor(props) {
        super(props, 'lead-time', 'Lead Time')
    }

    formatYAxisValue(value) {
        return utils.getFormatedTimeDuration(value)
    }
}