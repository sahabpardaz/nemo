import React from 'react'

class Error extends React.Component {
    render() {
        const error = this.props.error
        if (error) {
            return (
                <div className="callout callout-danger">
                    <p>{error}</p>
                </div>
            )
        } else {
            return null
        }
    }
}

export default Error
