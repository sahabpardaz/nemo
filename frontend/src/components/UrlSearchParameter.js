import React, { useEffect } from 'react'
import { useHistory, useLocation } from "react-router-dom"


export default function useUrlSearchParameter(key, defaultValue=null) {
    let history = useHistory()
    let location = useLocation()
    const emptyValues = ['null', 'undefined', '']

    useEffect(() => {
        setValue(defaultValue, true)
    }, [defaultValue, location])

    function setSearchParameter(key, newValue, onlyIfCurrentValueIsNull) {
        let params = new URLSearchParams(location.search)
        if (onlyIfCurrentValueIsNull === true)
            if (params.has(key) && !emptyValues.includes(params.get(key)))
                return
        params.set(key, newValue)
        history.push({
            search: `?${params.toString()}`
        })
    }

    function getSearchParameter(key) {
        let params = new URLSearchParams(location.search)
        return params.get(key)
    }

    const setValue = (value, onlyIfCurrentValueIsNull=false) => {
        setSearchParameter(key, value, onlyIfCurrentValueIsNull)
    }

    const value = getSearchParameter(key)

    return [
        value,
        setValue,
    ]
}