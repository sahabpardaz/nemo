import React from "react"

export default (props) => {
    let className = props.className
    if (props.error) {
        className += " is-invalid"
    }

    return (
        <>
            <input {...props} className={className} />
            {props.error && <span className="error invalid-feedback">{props.error}</span>}
        </>
    )
}