import React from "react"

class DropDown extends React.Component {

    lastValue = null

    constructor(props) {
        super(props)
        this.state = { lastValue: null }
        this._onSelectionChanged = this._onSelectionChanged.bind(this)
        this._notifySelectionChangedIfNeeded = this._notifySelectionChangedIfNeeded.bind(this)
    }

    render() {
        this._notifySelectionChangedIfNeeded(this.props.items.find(i => i.value === this.props.value))

        const options = []
        if (this.props.placeholder)
            options.push(<option key="placeholder" value="" disabled>{this.props.placeholder}</option>)

        for (let i = 0; i < this.props.items.length; i++) {
            const item = this.props.items[i]
            options.push(
                <option key={i} value={item.value}>{item.label}</option>
            )
        }
        return (
            <select className="form-control" disabled={this.props.disabled} onChange={this._onSelectionChanged.bind(this)} value={this.props.value || ""}>
                {options}
            </select>
        )
    }

    _onSelectionChanged(event) {
        const selectedIndex = event.currentTarget.selectedIndex - (this.props.placeholder ? 1 : 0)
        const item = this.props.items[selectedIndex]
        this._notifySelectionChangedIfNeeded(item)
    }

    _notifySelectionChangedIfNeeded(item) {
        if (this.props.onSelectionChanged && item)
            if (this.lastValue !== item.value) {
                this.lastValue = item.value
                setTimeout(() => {
                    this.props.onSelectionChanged(this.props.items.filter(i => i.value === item.value)[0])
                }, 0)
            }
    }
}

export default DropDown