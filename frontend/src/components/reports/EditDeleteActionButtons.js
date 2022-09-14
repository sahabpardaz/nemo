import React from "react"
import { Link } from "react-router-dom"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faEdit, faTrash } from "@fortawesome/free-solid-svg-icons"


export default (props) => {
    const { editUrl, onDeleteClicked } = props
    return (
        <div className="btn-group btn-group-sm">
            <Link to={editUrl} className="btn btn-primary" ><FontAwesomeIcon icon={faEdit}/></Link>
            <button className="btn btn-danger" onClick={onDeleteClicked}><FontAwesomeIcon icon={faTrash}/></button>
        </div>
    )
}
