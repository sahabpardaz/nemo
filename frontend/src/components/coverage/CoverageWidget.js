import React, {useEffect, useState} from 'react'
import {CircularProgressbarWithChildren} from "react-circular-progressbar"
import utils from "../../utils"
import {getColorFromFailureToSuccessColorsByPercentage} from "../../utils/color_percentage"


export default (props) => {
    const { title, metricUrl, onComponentWillBeRendered } = props
    const [value, setValue] = useState(null)

    useEffect(() => {
        utils.requestGET(metricUrl, true, {value: null}).then(jsonResponse => {
            const coverageValue = jsonResponse.value
            if (coverageValue != null) {
                setValue(
                    Math.floor(coverageValue)
                )
                onComponentWillBeRendered()
            } else {
                setValue(null)
            }
        })
    }, [metricUrl])

    if (value === null)
        return null

    const color = getColorFromFailureToSuccessColorsByPercentage(value)

    return (
        <div className="card">
            <div className="card-body">
                <CircularProgressbarWithChildren
                    value={value}
                    maxValue={100}
                    circleRatio={0.75}
                    styles={{
                        trail: {
                            strokeLinecap: 'butt',
                            transform: 'rotate(-135deg)',
                            transformOrigin: 'center center',
                        },
                        path: {
                            strokeLinecap: 'butt',
                            transform: 'rotate(-135deg)',
                            transformOrigin: 'center center',
                            height: '100%',
                            stroke: color,
                        },
                    }}>
                    <h3 className="text-center p-3" style={{ fontSize: 'larger' }}>
                        <b>{value} %</b>
                        <br/>
                        <small>{title}</small>
                    </h3>
                </CircularProgressbarWithChildren>
            </div>
        </div>
    )
}