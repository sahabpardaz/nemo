import utils from '../../utils'
import ChartAbs from './ChartAbs'

export default class DeploymentFrequencyChart extends ChartAbs {

    constructor(props) {
        super(props, 'deployment-frequency', 'Deployment Frequency')
    }

    formatYAxisValue(value) {
        return utils.getFormatedTimeDuration(value)
    }
}