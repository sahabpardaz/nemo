import React from 'react'
import ReactDOM from 'react-dom'
import * as serviceWorker from './serviceWorker'
import Router from './pages/Router'
import './App.scss'
import ReactTooltip from "react-tooltip"
import * as Sentry from '@sentry/browser'

const { SENTRY_ENVIRONMENT, SENTRY_DSN } = window.AppConfig

if (SENTRY_DSN !== null && SENTRY_DSN !== '')
    Sentry.init({
        dsn: SENTRY_DSN,
        environment: SENTRY_ENVIRONMENT,
    })

ReactDOM.render(
    <Router/>,
    document.getElementById('root'),
    ReactTooltip.rebuild)

serviceWorker.unregister()
