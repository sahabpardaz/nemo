import { toast } from "react-toastify"
import apiURLs from "../../../apiURLs"
import utils, { RequestError } from "../../../utils"

export default {
    getBackToReportListFunc(props, targetTab) {
        return () => {
            const { project_id } = props.match.params
            props.history.push(`/project/${project_id}/reports${targetTab}`)
        }
    },
    isEditMode(props) {
        return !!props.match.params.report_id
    },
    async saveReport(props, body, setErrorsFunc, targetTab, itemListUrl, itemId = undefined) {
        let url
        let method
        if (this.isEditMode(props)) {
            if (itemId === undefined)
                throw Error("itemId is not passed for saving report. It's mandatory in the edit mode!")
            url = apiURLs.getEditUrlFromListUrl(itemListUrl, itemId)
            method = 'PUT'
        } else {
            url = itemListUrl
            method = 'POST'
        }

        if (!body.time?.isValid()){
            setErrorsFunc({ time: "Selected time is not valid." })
            return
        }

        try {
            const jsonResult = await utils.request(url, method, body, false)
            toast.success(`Report ${jsonResult.id} saved.`)
            this.getBackToReportListFunc(props, targetTab)()
        } catch (e) {
            if (e instanceof RequestError) {
                if (e.response.status === 400)
                    setErrorsFunc(e.jsonResult)
            } else
                throw e
        }
    }
}