import React from "react"
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome"
import theme from "../styles/theme.module.scss"
import HelpMark from "./HelpMark"


export default((props) => {
    const { title, title_help_text, content, loading, icon } = props
    return (
        <div className="info-box">
            <span className="info-box-icon"><FontAwesomeIcon icon={icon} /></span>
            {loading && <div className="overlay dark" />}
            <div className="info-box-content">
                    <span className={`info-box-text ${theme.forecolor}`}>{title}
                        <HelpMark title={title_help_text} />
                    </span>
                <span className={`info-box-number ${theme.forecolor_dark}`}>{content}</span>
            </div>
        </div>
    )
})
