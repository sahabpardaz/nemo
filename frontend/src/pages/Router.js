import { BrowserRouter, Route, Switch } from "react-router-dom"
import React from "react"
import Login from './Login'
import AuthenticatedUserRootPage from "./AuthenticatedUserRootPage"

export default (props) => {

    

    return (
        <BrowserRouter>
            <Switch>
                <Route path="/login" component={Login} />
                <AuthenticatedUserRootPage />
            </Switch>
        </BrowserRouter>
    )
}
