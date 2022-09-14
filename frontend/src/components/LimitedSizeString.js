import HelpMark from "./HelpMark"
import React from "react"

export default (props) => {
    let { text, limitedSize } = props
    text = text ?? ""
    if (text.length <= limitedSize)
        return text

    return (
        <HelpMark title={text}>{text.substr(0, limitedSize)}</HelpMark>
    )
}
