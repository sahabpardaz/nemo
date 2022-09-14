import React from 'react'
import { withRouter, NavLink } from "react-router-dom"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { faBars, faSignOutAlt } from "@fortawesome/free-solid-svg-icons"
import apiURLs from '../apiURLs'
import utils from '../utils'


class Navbar extends React.Component {
  constructor(props) {
    super(props)
    this.logOut = this.logOut.bind(this)
  }

  logOut = () => {
    const url = new URL(apiURLs.logout())
    url.searchParams.set("next", "/")
    utils.redirectToExternalUrl(url.href)
  };

  render() {
    return (
      <nav className="main-header navbar navbar-expand navbar-white navbar-light">
        <ul className="navbar-nav">
          <li className="nav-item">
            <a className="nav-link" data-widget="pushmenu" href="/"><FontAwesomeIcon icon={faBars} /></a>
          </li>
          <li className="nav-item d-none d-sm-inline-block">
            <NavLink to="/project" className="nav-link">Home</NavLink>
          </li>
          <li className="nav-item d-none d-sm-inline-block">
            <a href={apiURLs.swagger()} className="nav-link">API Documentation</a>
          </li>
          <li className="nav-item d-none d-sm-inline-block">
            <a href="/user-manual" className="nav-link">User Manual</a>
          </li>
        </ul>
        <ul className="navbar-nav ml-auto">
          <li className="nav-item d-none d-sm-inline-block">
            <a className="nav-link" onClick={this.logOut}>
              <FontAwesomeIcon icon={faSignOutAlt} />
              Logout
            </a>
          </li>
        </ul>
      </nav>
    )
  }
}

export default withRouter(Navbar)
