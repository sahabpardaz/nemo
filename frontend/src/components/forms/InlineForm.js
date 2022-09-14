import React from "react"
import {faTrashAlt} from "@fortawesome/free-solid-svg-icons"
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome"


export function parseErrors(errorsToParse) {
    let parsedErrors = []
    for (const error in errorsToParse) {
        parsedErrors.push(errorsToParse[error])
    }
    return parsedErrors
}


export default (props) => {
    const { cardTitle, fieldErrors, fieldValue, fieldPlaceholder, setFieldValue, onSubmit, onDelete } = props

    return (
        <div className="card card-outline">
            <div className="card-header">
                <h3 className="card-title">{cardTitle}</h3>
                <div className="card-tools">
                    {onDelete &&
                        <button type="button" className="btn btn-sm btn-danger" onClick={onDelete}>
                            <FontAwesomeIcon icon={faTrashAlt} className="fas nav-icon"/>
                        </button>
                    }
                </div>
            </div>
            <div className="card-body">
                <div className="input-group">
                    <input 
                        type="text" className={`form-control ${fieldErrors && "is-invalid"}`}
                        placeholder={fieldPlaceholder} 
                        value={fieldValue}
                        onChange={e => setFieldValue(e.target.value)}
                    />
                    <span className="input-group-append">
                        <button type="button" className="btn btn-outline-success" onClick={onSubmit}>Submit</button>
                    </span>
                </div>
                {fieldErrors &&
                    <div className="input-group">
                        <span className="text-danger small">{fieldErrors}</span>
                    </div>
                }
            </div>
        </div>
    )
}
