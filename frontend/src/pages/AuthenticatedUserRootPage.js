import React, { useState } from 'react'
import { withRouter, Route, Redirect } from "react-router-dom"
import agent from "../agent"
import { useEffect } from "react"
import Menus from "../components/Menus"
import Navbar from "../components/Navbar"
import Projects from "./Projects"
import ProjectRouter from "./project/ProjectRouter"
import Footer from "../components/Footer"
import { ToastContainer, toast } from 'react-toastify'
import MaturityModelImportExport from './MaturityModelImportExport'
import ReactTooltip from "react-tooltip"
import styles from "../css/nemo.module.css"
import UserManual from "./UserManual"
import UserSettings from './UserSettings'


function AuthenticatedUserRootPage(props) {
    const [appLoaded, setAppLoaded] = useState(false)

    useEffect(() => {
        (async () => {
            let urlToVisit = props.history.location.pathname
            if (! await agent.isLoggedIn() && urlToVisit !== "/login") {
                props.history.push(`/login${urlToVisit && `?next=${encodeURI(urlToVisit)}`}`)
            }
            setAppLoaded(true)
        })()
    }, [props.history.location])

    useEffect(() => {
        ReactTooltip.rebuild()
    })

    if (!appLoaded)
        return (
            <div className="login-logo">
                <img src="/dist/img/loading-fish.gif" alt="loading..." />
            </div>
        )
    else
        return (
            <div className="wrapper">

                <Menus />
                <ReactTooltip className={styles.generalTooltip} />
                <Navbar />
                <Route exact path="/">
                    <Redirect to='/project' />
                </Route>
                <Route exact path="/project" component={Projects} />
                <Route path="/project/:id" component={ProjectRouter} />
                <Route path="/maturity-model-import-export" component={MaturityModelImportExport} />
                <Route path="/user-manual" component={UserManual} />
                <Route path="/user/settings" component={UserSettings} />
                <ToastContainer
                    position={toast.POSITION.BOTTOM_RIGHT}
                    closeButton={false}
                    limit={3}
                />
                <Footer />

            </div>
        )
}


export default withRouter(AuthenticatedUserRootPage)