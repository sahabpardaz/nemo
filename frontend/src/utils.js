import humanizeDuration from 'humanize-duration'
import apiURLs from "./apiURLs"
import { toast } from "react-toastify"
import moment from 'moment-jalaali'
import { useEffect } from 'react'
import Cookies from 'js-cookie'


export class RequestError extends Error {
    constructor(error, response, jsonResult){
        super(error?.message)
        this.error = error
        this.response = response
        this.jsonResult = jsonResult
    }
}

export default {
    /**
     * Same as request but uses GET method.
     *
     * @param {String} url
     * @param {Boolean} toastError Whether or not toasting the encountered error message.
     * @param {Object} defaultResult Optinal. An object to be returned in case of request failure.
     */
    async requestGET(url, toastError = true, defaultResult = undefined) {
        return await this.request(url, 'GET', null, toastError, defaultResult)
    },
    /**
     * Makes a request and automatically shows errors by toasting appropriate messages.
     *
     * @param {String} url
     * @param {String} method GET | POST | PUT | DELETE | HEAD ...
     * @param {Object} body Optional. Post / Put data payload.
     * @param {Boolean} toastError Whether or not toasting the encountered error message.
     * @param {Object} defaultResult An object to be returned in case of request failure.
     * If not passed the async method will reject in case of error.
     *
     * @throws {{error, response, jsonBody}}
     * @returns {Object} json body of response
     */
    async request(url, method, body = null, toastError = true, defaultResult) {
        let response
        let jsonResult
        try {
            response = await this.rawRequest(url, method, body)
            switch (response.status) {
                case 200:
                case 201:
                    jsonResult = await response.json()
                case 204:
                    return jsonResult ?? defaultResult
                case 400:
                    jsonResult = await response.json()
                    throw new Error(
                        `Bad Request. ${this._getErrorDescription(jsonResult)}`)
                case 401:
                    jsonResult = await response.json()
                    throw new Error('You need to sign in before continuing')
                case 403:
                    throw new Error('Access to this action is forbidden.')
                case 404:
                    throw new Error('Resource not found')
                default:
                    const responseBodyTxt = await response.text()
                    let errorDetail = ""
                    try {
                        const responseBody = JSON.parse(responseBodyTxt)
                        errorDetail = responseBody.detail
                    } catch (SyntaxError) { }
                    let errorTxt = null
                    if (errorDetail)
                        errorTxt = `${errorDetail} (Status ${response.status})`
                    else
                        errorTxt = `Unexpected server error (${response.status})`
                    console.error(`${errorTxt}\n\nrequest:\n\nurl:\n${url}\n\nResponse body:\n${responseBodyTxt}`)
                    throw new Error(errorTxt)
            }
        } catch (error) {
            console.log(`utils.request error: ${error}`)
            if (toastError) {
                if (error.message === 'Failed to fetch')
                    toast.error('Could not connect to server.', { toastId: -1 })
                else
                    toast.error(error.message, { toastId: error.message })
            }
            if (defaultResult !== undefined)
                return defaultResult
            throw new RequestError(error, response, jsonResult)
        }
    },
    _getErrorDescription(jsonResult) {
        return Object.keys(jsonResult)
            .map(k => `${k}: ${jsonResult[k]}`)
            .join(' | ')
    },
    /**
     * Authorized request. Returns the raw response of the request.
     *
     * @param {String} url
     * @param {String} method Http method
     * @param {Object} body Optional. Put/Post body.
     *
     * @returns {Response}
     */
    async rawRequest(url, method, body = null) {
        return await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            body: body ? JSON.stringify(body) : null
        })
    },
    async fetchEnvironmentsAsDropdownItems(projectId) {
        const url = apiURLs.devopsMetricsEnvironmentsList(projectId)
        const jsonResult = await this.requestGET(url, { results: [] })
        const environments = jsonResult.results.map(
            env => ({ label: env.name, value: env.id }))
        return environments
    },
    getFormatedTimeDuration(seconds) {
        if (!isNaN(seconds)) {
            return humanizeDuration(parseInt(seconds * 1000), { largest: 2 })
        } else {
            return seconds
        }
    },
    getFormatedPercentage(percentage) {
        if (!isNaN(percentage)) {
            return parseFloat(percentage).toFixed(2)
        } else {
            return percentage
        }
    },
    /**
     *
     * @param value: Unformatted value
     * @param type: value type could be Percentage(PRC), Seconds(SEC)
     * @returns {*} Formatted value
     */
    getReadableValueByType(value, type) {
        switch (type) {
            case "PRC":
                return this.getFormatedPercentage(value)
            case "SEC":
                return this.getFormatedTimeDuration(value)
            case null:
                return value
            default:
                throw new Error(`Type ${type} not supported.`)
        }
    },
    throwAbstractMethodNotImplemented() {
        throw new Error("Abstract method not implemented")
    },
    /**
     * Prevents throtlling a function call; that is, if the function is called more frequently than the given interval, only the last non-frequent one is applied.
     * @param {Function} func The function to be debounced
     * @param {Number} interval The time (in ms) to wait to ensure no other multiple calls happened
     * @param {Object} thisArg Scope replacement
     * @returns {Function} A wrapper function that ignores previous multiple calls during the 'interval' period
     */
    debounce(func, interval, thisArg = this) {
        let timeoutId
        return function (...args) {
            clearTimeout(timeoutId)
            timeoutId = setTimeout(() => func.apply(thisArg, args), interval)
        }
    },
    /**
     * Accepts an async function for useEffect. Since the regular useEffect function doesn't accept such functions.
     * For more details, see: https://js.plainenglish.io/how-to-use-async-function-in-react-hook-useeffect-typescript-js-6204a788a435
     * @param {Function} asyncFunc The function to get called.
     * @param {Object} thisArg Optional. The 'this' context.
     */
    useEffectAsync(asyncFunc, deps = undefined, thisArg = this) {
        useEffect(() => {
            asyncFunc.apply(thisArg)
        }, deps)
    },
    /**
     * history.push method wouldn't work with external url.
     * @param {String} url
     */
    redirectToExternalUrl(url) {
        window.location.href = url
    },
    /**
     *
     * @param {String} timestampStr
     * @param {Boolean} includeTime Optional.
     * @returns {String} Jalali timestamp string
     */
    convertIsoTimestampToJalali(timestampStr, includeTime = true){
        let format = 'jYYYY-jMM-jDD'
        if (includeTime)
            format += ' HH:mm:ss'
        return moment(timestampStr).format(format)
    },
}
