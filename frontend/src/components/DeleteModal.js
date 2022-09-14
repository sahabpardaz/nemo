import React from 'react'
import { Modal, ModalManager, Effect } from 'react-dynamic-modal'
import { token } from '../agent'
import { toast } from 'react-toastify'
import utils from '../utils'


class DeleteModal extends React.Component {
    requestDelete() {

        utils.request(this.props.deleteURL, 'DELETE')
            .then(jsonResult => {
                toast.success(`${this.props.modelTypeName} ${this.props.modelTitle} was deleted.`)
                ModalManager.close()
                if (this.props.onSuccessful)
                    this.props.onSuccessful()
            })
    }

    render() {
        const { modelTypeName, modelTitle } = this.props

        return (
            <Modal
                effect={Effect.ScaleUp}>
                <div className="modal-content">
                    <div className="modal-header">
                        <h4 className="modal-title">Delete {modelTypeName}</h4>
                        <button type="button" className="close" onClick={ModalManager.close}>
                            <span aria-hidden="true">×</span>
                        </button>
                    </div>
                    <div className="modal-body">
                        Are You sure you want to delete {modelTypeName} {modelTitle}?
                    </div>
                    <div className="modal-footer justify-content-between">
                        <button type="button" className="btn btn-default" onClick={ModalManager.close}>Cancel</button>
                        <button type="button" className="btn btn-danger" onClick={event => this.requestDelete(event)}>
                            Delete
                        </button>
                    </div>
                </div>
            </Modal>
        )
    }
}

export default DeleteModal
