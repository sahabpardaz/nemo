import React from 'react'
import { faQuestionCircle } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import theme from '../styles/theme.module.scss'

class HelpMark extends React.Component {
    render() {
        const tooltip = <p style={{display: "inline"}}
                           data-tip={this.props.title}
                           data-place="top"
                           data-effect="solid"
        >
            {this.props.children
                ? this.props.children
                : <FontAwesomeIcon className={theme.forecolor_gray_dark} icon={faQuestionCircle} />
            }
        </p>
        if (!this.props.href)
            return this.__wrap_in_span(tooltip)
        return this.__wrap_in_span(
            <a href={this.props.href} target="_blank" rel="noopener noreferrer" onClick={(event) => event.stopPropagation()}>
                {tooltip}
            </a>
        )
    }

    __wrap_in_span(element) {
        return (
            <span>
                {" "}{element}
            </span>
        )
    }
}

export default HelpMark