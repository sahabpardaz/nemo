import React, {useState, useEffect} from 'react'
import { withRouter } from "react-router-dom"
import utils from '../../utils'
import Tabs from 'react-bootstrap/Tabs'
import Tab from 'react-bootstrap/Tab'
import Form from 'react-bootstrap/Form'
import LeadTimeChart from '../../components/devops-charts/LeadTimeChart'
import DeploymentFrequencyChart from '../../components/devops-charts/DeploymentFrequencyChart'
import ChangeFailureRateChart from '../../components/devops-charts/ChangeFailureRateChart'
import TimeToRestoreChart from '../../components/devops-charts/TimeToRestoreChart'
import DailyCoverageChart from '../../components/devops-charts/DailyCoverageChart'
import { DatetimePickerTrigger } from 'imrc-datetime-picker'
import moment from 'moment-jalaali'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCalendarAlt } from '@fortawesome/free-solid-svg-icons'
import DevOpsMetricsWidget from '../../components/DevOpsMetricsWidget'
import { Container, Row, Col } from "react-bootstrap"
import theme from '../../styles/theme.module.scss'
import Select from "react-select"
import chroma from 'chroma-js'
import stc from 'string-to-color'
import useUrlSearchParameter from '../../components/UrlSearchParameter'
import { FULL_DATE, FULL_DATE_J } from '../../utils/moment_formats'


const DEFAULT_CHECKING_PERIOD_DAYS = window.AppConfig.DEFAULT_CHECKING_PERIOD_DAYS

// https://codesandbox.io/s/x7sjq?module=/example&file=/example.js:27-58
const colourStyles = {
    control: styles => ({ ...styles, backgroundColor: 'white' }),
    option: (styles, { data, isDisabled, isFocused, isSelected }) => {
        const color = chroma(data.color)
        return {
            ...styles,
            backgroundColor: isDisabled
                ? null
                : isSelected
                    ? data.color
                    : isFocused
                        ? color.alpha(0.1).css()
                        : null,
            color: isDisabled
                ? '#ccc'
                : isSelected
                    ? chroma.contrast(color, 'white') > 2
                        ? 'white'
                        : 'black'
                    : data.color,
            cursor: isDisabled ? 'not-allowed' : 'default',

            ':active': {
                ...styles[':active'],
                backgroundColor: !isDisabled && (isSelected ? data.color : color.alpha(0.3).css()),
            },
        }
    },
    multiValue: (styles, { data }) => {
        const color = chroma(data.color)
        return {
            ...styles,
            backgroundColor: color.alpha(0.1).css(),
        }
    },
    multiValueLabel: (styles, { data }) => ({
        ...styles,
        color: data.color,
    }),
    multiValueRemove: (styles, { data }) => ({
        ...styles,
        color: data.color,
        ':hover': {
            backgroundColor: data.color,
            color: 'white',
        },
    }),
}

export default withRouter((props) => {

    const TAB_LEAD_TIME = "leadTime"
    const TAB_DEPLOYMENT_FREQUENCY = "deploymentFrequency"
    const TAB_CHANGE_FAILURE_RATE = "changeFailureRate"
    const TAB_TIME_TO_RESTORE = "timeToRestore"
    const TAB_DAILY_COVERAGE = "dailyCoverage"
    const paramKeys = {
        SELECTED_ENVIRONMENT_IDS: 'selectedEnvironmentIds',
        FROM_DATE: 'fromDate',
        TO_DATE: 'toDate',
        CHECKING_PERIOD_DAYS: 'checkingPeriodDays',
    }
    const defaultParams = {
        selectedEnvironmentIds: '',
        fromDate: moment().subtract(1, 'jMonth').format(FULL_DATE_J),
        toDate: moment().format(FULL_DATE_J),
        checkingPeriodDays: DEFAULT_CHECKING_PERIOD_DAYS,
    }
    const LIST_ITEM_DELIMITER = ','

    const { defaultEnvironmentId } = props
    const { project_id } = props.match.params

    const [selectedTabKey, setSelectedTabKey] = useState(TAB_LEAD_TIME)
    const [environments, setEnvironments] = useState([])

    const [checkingPeriodDaysParam, setCheckingPeriodDaysParam] = useUrlSearchParameter(paramKeys.CHECKING_PERIOD_DAYS, defaultParams.checkingPeriodDays)
    const [toDateParam, setToDateParam] = useUrlSearchParameter(paramKeys.TO_DATE, defaultParams.toDate)
    const [fromDateParam, setFromDateParam] = useUrlSearchParameter(paramKeys.FROM_DATE, defaultParams.fromDate)
    const [selectedEnvironmentIdsParam, setSelectedEnvironmentIdsParam] = useUrlSearchParameter(paramKeys.SELECTED_ENVIRONMENT_IDS, defaultEnvironmentId)

    const toDateMoment = moment(toDateParam, FULL_DATE_J)
    const fromDateMoment = moment(fromDateParam, FULL_DATE_J)
    const selectedEnvironments = getSelectedEnvironmentsOptions()

    useEffect(() => {
        fillEnvironments()
    }, [project_id])

    async function fillEnvironments() {
        let fetchedEnvironments = await utils.fetchEnvironmentsAsDropdownItems(project_id)
        for (let env of fetchedEnvironments)
            env.color = stc(env.label)

        setEnvironments(fetchedEnvironments)
    }

    function getSelectedEnvironmentsOptions() {
        const selectedEnvironments = []
        for (const env of environments) {
            if (selectedEnvironmentIdsParam.includes(env.value.toString())) {
                selectedEnvironments.push(env)
            }
        }
        return selectedEnvironments
    }

    return (
        <Container fluid>
            <Row>
                <Col md={12}>
                    <div className="card">
                        <div className="card-body">
                            <Row>
                                <Col md={6}>
                                    <Form.Label>Environments </Form.Label>
                                    <Select
                                        isDisabled={selectedTabKey === TAB_DAILY_COVERAGE}
                                        value={selectedEnvironments}
                                        isMulti
                                        name="environments"
                                        options={environments}
                                        placeholder="Select environments..."
                                        onChange={(options) => setSelectedEnvironmentIdsParam(options?.map(option => option.value).join(LIST_ITEM_DELIMITER))}
                                        styles={colourStyles}
                                    />
                                </Col>
                                <Col md={2}>
                                    <Form.Label>From </Form.Label>
                                    <DatetimePickerTrigger
                                        moment={fromDateMoment}
                                        onChange={(value) => setFromDateParam(value.format(FULL_DATE_J))}
                                        isSolar={true}
                                        lang="en"
                                        showTimePicker={false}
                                        closeOnSelectDay={true}
                                    >
                                        <div className="input-group">
                                            <input type="text" value={fromDateMoment.format(FULL_DATE_J)} className="form-control"/>
                                            <div className="input-group-append">
                                            <span className="input-group-text">
                                                <FontAwesomeIcon icon={faCalendarAlt}/>
                                            </span>
                                            </div>
                                        </div>
                                    </DatetimePickerTrigger>
                                </Col>
                                <Col md={2}>
                                    <Form.Label>To </Form.Label>
                                    <DatetimePickerTrigger
                                        moment={toDateMoment}
                                        onChange={(value) => setToDateParam(value.format(FULL_DATE_J))}
                                        isSolar={true}
                                        lang="en"
                                        showTimePicker={false}
                                        isOpen={true}
                                        closeOnSelectDay={true}
                                    >
                                        <div className="input-group">
                                            <input type="text" value={toDateMoment.format(FULL_DATE_J)} className="form-control"/>
                                            <div className="input-group-append">
                                            <span className="input-group-text">
                                                <FontAwesomeIcon icon={faCalendarAlt}/>
                                            </span>
                                            </div>
                                        </div>
                                    </DatetimePickerTrigger>
                                </Col>
                                <Col md={2}>
                                    <Form.Label>Checking Period Days</Form.Label>
                                    <Form.Control
                                        type="number"
                                        placeholder="Checking period days"
                                        onChange={event => setCheckingPeriodDaysParam(event.target.value)}
                                        value={checkingPeriodDaysParam}/>
                                </Col>
                            </Row>
                        </div>
                    </div>
                </Col>
                <Col md={12}>
                    <div className="card">
                        <div className="card-body">
                            <Tabs
                                activeKey={selectedTabKey}
                                onSelect={setSelectedTabKey}>
                                <Tab eventKey={TAB_LEAD_TIME} title="Lead Time">
                                    <LeadTimeChart
                                        projectId={project_id}
                                        environments={selectedEnvironments}
                                        fromDate={fromDateMoment.format(FULL_DATE)}
                                        toDate={toDateMoment.format(FULL_DATE)}
                                        checkingPeriodDays={checkingPeriodDaysParam}
                                        isSelected={selectedTabKey === TAB_LEAD_TIME}
                                    />
                                </Tab>
                                <Tab eventKey={TAB_DEPLOYMENT_FREQUENCY} title="Deployment Frequency">
                                    <DeploymentFrequencyChart
                                        projectId={project_id}
                                        environments={selectedEnvironments}
                                        fromDate={fromDateMoment.format(FULL_DATE)}
                                        toDate={toDateMoment.format(FULL_DATE)}
                                        checkingPeriodDays={checkingPeriodDaysParam}
                                        isSelected={selectedTabKey === TAB_DEPLOYMENT_FREQUENCY} />
                                </Tab>
                                <Tab eventKey={TAB_CHANGE_FAILURE_RATE} title="Change Failure Rate">
                                    <ChangeFailureRateChart
                                        projectId={project_id}
                                        environments={selectedEnvironments}
                                        fromDate={fromDateMoment.format(FULL_DATE)}
                                        toDate={toDateMoment.format(FULL_DATE)}
                                        checkingPeriodDays={checkingPeriodDaysParam}
                                        isSelected={selectedTabKey === TAB_CHANGE_FAILURE_RATE} />
                                </Tab>
                                <Tab eventKey={TAB_TIME_TO_RESTORE} title="Time to Restore">
                                    <TimeToRestoreChart
                                        projectId={project_id}
                                        environments={selectedEnvironments}
                                        fromDate={fromDateMoment.format(FULL_DATE)}
                                        toDate={toDateMoment.format(FULL_DATE)}
                                        checkingPeriodDays={checkingPeriodDaysParam}
                                        isSelected={selectedTabKey === TAB_TIME_TO_RESTORE} />
                                </Tab>
                                <Tab eventKey={TAB_DAILY_COVERAGE} title="Daily Coverage">
                                    <DailyCoverageChart
                                        projectId={project_id}
                                        fromDate={fromDateMoment.format(FULL_DATE)}
                                        toDate={toDateMoment.format(FULL_DATE)}
                                        checkingPeriodDays={checkingPeriodDaysParam}
                                        isSelected={selectedTabKey === TAB_DAILY_COVERAGE} />
                                </Tab>
                            </Tabs>
                        </div>
                    </div>
                </Col>
            </Row>
        </Container>
    )
})
