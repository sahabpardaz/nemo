import { Modal } from 'react-responsive-modal'


export default (props) => {
    const { children, open, onClose, onAnimationEnd } = props
    return (
        <Modal
            center
            open={open}
            onClose={onClose}
            onAnimationEnd={onAnimationEnd}
            styles={{
                overlay: {
                    position: 'fixed',
                    inset: '0px',
                    zIndex: 1400,
                    overflow: "hidden",
                    perspective: '1300px',
                    backgroundColor: 'rgba(0, 0, 0, 0.6)',
                    opacity: '1',
                },
                modal: {
                    background: "none",
                    boxShadow: "none",
                }
            }}
            showCloseIcon={false}
            classNames={{
                modal: "col-md-6"
            }}
        >
            {children}
        </Modal>
    )
}
