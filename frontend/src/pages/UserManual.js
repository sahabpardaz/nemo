import React, {useEffect, useState} from 'react'
import ReactMarkdownWithHtml from "react-markdown/with-html"
import {Container, Row, Col} from "react-bootstrap"
import ContentHeader from "../components/ContentHeader"
import toc from 'remark-toc'
import GithubSlugger from 'github-slugger'


export default (props) => {
    const [markdownFormatText, setMarkdownFormatText] = useState("")

    useEffect(() => {
        const userManualFileModule = require("../user-manual/main.md")
        const userManualFileURL = userManualFileModule.default
        fetch(userManualFileURL)
            .then(response => response.text())
            .then(text => {
                setMarkdownFormatText(text)
            })
    })

    function flatten(text, child) {
        return typeof child === 'string'
            ? text + child
            : React.Children.toArray(child.props.children).reduce(flatten, text)
    }

    function HeadingRenderer(props) {
        let slugger = new GithubSlugger()
        let slugId = slugger.slug(React.Children.toArray(props.children).reduce(flatten, ''), false)
        return React.createElement('h' + props.level, {id: slugId}, props.children)
    }

    return (
        <div className="content-wrapper">
            <ContentHeader header="User Manual" />
            <div className="content">
                <Container fluid>
                    <Row>
                        <Col>
                            <div className="card">
                                <div className="card-body">
                                    <ReactMarkdownWithHtml
                                        plugins={[
                                            [toc, {maxDepth : 3, heading : "فهرست", tight: true}],
                                        ]}
                                        children={markdownFormatText}
                                        renderers={{heading: HeadingRenderer}}
                                        // I wish I could use remark-slug plugin instead. But I tried and id's didn't rendered.
                                        // https://github.com/remarkjs/react-markdown/issues/69
                                        allowDangerousHtml
                                    />
                                </div>
                            </div>
                        </Col>
                    </Row>
                </Container>
            </div>
        </div>
    )
}
