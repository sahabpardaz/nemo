import React from 'react'

class ContentHeader extends React.Component {
    render() {
        return (
            // Todo : Change static breadcrumb to dynamic
            <div className="content-header">
                <div className="container-fluid">
                    <div className="row mb-2">
                        <div className="col-sm-6">
                            <h1 className="m-0 text-dark">{this.props.header}</h1>
                        </div>
                        {/* Todo: Implement functionality for breadcrumb */}
                        {/* <div className="col-sm-6">
                            <ol className="breadcrumb float-sm-right">
                                <li className="breadcrumb-item"><a href="/">Home</a></li>
                                <li className="breadcrumb-item"><a href="/">Projects</a></li>
                                <li className="breadcrumb-item active">#Name</li>
                            </ol>
                        </div> */}
                    </div>
                </div>
            </div>
        )
    }
}

export default ContentHeader











