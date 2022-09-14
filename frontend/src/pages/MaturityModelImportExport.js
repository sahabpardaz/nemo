import React, { useEffect, useState } from 'react'
import ContentHeader from "../components/ContentHeader"
import styles from "../css/nemo.module.css"
import Error from "../components/Error"
import { faFileExport } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import download from "downloadjs"
import { toast } from 'react-toastify'
import moment from 'moment-jalaali'
import apiURLs from '../apiURLs'
import utils from '../utils'


export default (props) => {
    const fileInputPlaceHolder = 'Choose file'
    const [maturityModels, setMaturityModels] = useState()
    const [errorMessage, setErrorMessage] = useState()
    const [maturityModelToImport, setMaturityModelToImport] = useState()
    const [fileName, setFileName] = useState(fileInputPlaceHolder)
    const [reload, setReload] = useState(false)
    const [formErrors, setFormErrors] = useState()
    const maturityModelUrl = apiURLs.maturityModelList()

    useEffect(() => {
        utils.requestGET(maturityModelUrl)
            .then(result => {
                setMaturityModels(result.results)
                setErrorMessage()
            })
            .catch(() => {
                setErrorMessage("Failed to get maturity models info from server.")
            })
    }, [reload])

    if (errorMessage) {
        return (
            <div className="content-wrapper">
                <div className="content">
                    <Error error={errorMessage} />
                </div>
            </div>
        )
    }

    if (!maturityModels) {
        return (
            <div className="content-wrapper">
                <div className="content">
                    <p>Loading ...</p>
                </div>
            </div>
        )
    }

    const onMaturityModelFileChosen = (file) => {
        if (file) {
            setFileName(file.name)
            let fileReader = new FileReader()
            fileReader.onloadend = () => {
                setMaturityModelToImport(fileReader.result)
            }
            fileReader.readAsText(file)
        } else {
            setFileName(fileInputPlaceHolder)
            setMaturityModelToImport()
        }
    }

    const onSubmitMaturityModel = (event) => {
        event.preventDefault()
        utils.request(maturityModelUrl, 'POST', maturityModelToImport)
            .then(result => {
                toast.success('Maturity model imported successfully.')
                setFormErrors()
                setFileName(fileInputPlaceHolder)
                setReload(moment.now())
            })
            .catch(errorBundle => {
                switch (errorBundle.response?.status) {
                    case 400:
                        setFormErrors(errorBundle.jsonResult)
                        break
                    case 403:
                        setFormErrors(errorBundle.jsonResult['detail'])
                        break
                }
            })
    }

    const maturityModelsRows = []
    for (const maturityModel of maturityModels) {
        maturityModelsRows.push(
            <tr>
                <td>{maturityModel.id}</td>
                <td>{maturityModel.name}</td>
                <td className="text-right py-0 align-middle">
                    <div className="btn-group btn-group-sm">
                        <a
                            onClick={() => {
                                download(
                                    JSON.stringify(maturityModel),
                                    `${maturityModel.name} ${utils.convertIsoTimestampToJalali(moment().toISOString())}.json`,
                                    "application/json"
                                )
                            }}
                            target="_blank"
                            className="btn btn-secondary">
                            <FontAwesomeIcon icon={faFileExport} style={{ color: "white" }} />
                        </a>
                    </div>
                </td>
            </tr>
        )
    }

    return (
        <div className="content-wrapper">
            <ContentHeader header="Import/Export Maturity Model" />
            <div className="content">
                <div className="card card-primary">
                    <div className="card-header">
                        <h3 className="card-title">Maturity Models</h3>
                    </div>
                    <div className="card-body p-0">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th style={{ width: "8%" }}>Id</th>
                                    <th>Name</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {maturityModels.length !== 0 ? maturityModelsRows :
                                    <tr className={styles.itemTableRow}>
                                        <td colSpan="3">
                                            <h6>There is no maturity model.</h6>
                                        </td>
                                    </tr>
                                }
                            </tbody>
                        </table>
                    </div>

                </div>
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Import</h3>
                    </div>
                    <form role="form">
                        <div class="card-body">
                            <div class="form-group">
                                {formErrors &&
                                    <Error error={
                                        <div>
                                            Errors:
                                            <pre>
                                                {JSON.stringify(formErrors, null, 2)}
                                            </pre>
                                        </div>
                                    } />
                                }
                                <label for="inputFile">File input</label>
                                <div class="input-group">
                                    <div class="custom-file">
                                        <input
                                            type="file"
                                            class="custom-file-input"
                                            accept=".json"
                                            onChange={e => onMaturityModelFileChosen(e.target.files[0])}
                                            id="inputFile"
                                            key={reload}
                                        />
                                        <label class="custom-file-label" for="inputFile">{fileName}</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="card-footer">
                            <button
                                type="submit"
                                class="btn btn-secondary"
                                onClick={onSubmitMaturityModel}
                            >
                                Submit
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    )
}
