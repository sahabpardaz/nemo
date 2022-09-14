import HelpMark from "./HelpMark"
import React from "react"
import {Badge} from "react-bootstrap"

export default (props) => {
    const {children, variant, helpText} = props
    return (
        <HelpMark title={helpText} >
            <Badge className="p-1 d-inline" variant={variant}>
                {children}
            </Badge>
        </HelpMark>
    )
}
