import React, { useEffect } from 'react'
import { withRouter } from "react-router-dom"
import agent from '../agent'
import 'icheck-bootstrap'
import apiURLs from '../apiURLs'
import utils from "../utils"

function Login(props) {
    utils.useEffectAsync(async () => {
        const searchParams = new URLSearchParams(props.location.search)
        const next = searchParams.get('next') ?? "/"

        if (await agent.isLoggedIn()) {
            props.history.push(next)
        } else {
            let loginUrl = new URL(apiURLs.login())
            loginUrl.searchParams.set("next", next)
            utils.redirectToExternalUrl(loginUrl.href)
        }
    }, [])

    return (
        <div className="hold-transition login-page">
            <div className="login-box">
                <div className="login-logo">
                    <img src="/dist/img/logo.png" alt="Nemo Logo" width="150"
                        className="brand-image img-circle " />
                    <div>
                        Redirecting to <b>SSO</b>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default withRouter(Login)
