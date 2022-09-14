import ChartAbs from './ChartAbs'
import utils from '../../utils'

export default class TimeToRestoreChart extends ChartAbs {

    constructor(props) {
        super(props, 'time-to-restore', 'Time To Restore')
    }

    formatYAxisValue(value) {
        return utils.getFormatedTimeDuration(value)
    }
}