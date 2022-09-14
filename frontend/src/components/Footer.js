import React from 'react'
import theme from '../styles/theme.module.scss'

class Footer extends React.Component {
    render() {
        return (
            <footer className={`main-footer ${theme.bg_gray_light}`}>
                <strong>Copyright &copy; {window.AppConfig.COPYRIGHT_YEAR} <a href="/">Vertical Team</a>.</strong> All rights reserved.
                <span className="float-right">Version: {window.AppConfig.NEMO_VERSION}</span>
            </footer>
        )
    }
}

export default Footer 
