// https://stackoverflow.com/a/61396704
export function colorGradient(fadeFraction, rgbColor1, rgbColor2, rgbColor3) {
    var color1 = rgbColor1
    var color2 = rgbColor2
    var fade = fadeFraction

    // Do we have 3 colors for the gradient? Need to adjust the params.
    if (rgbColor3) {
        fade = fade * 2

        // Find which interval to use and adjust the fade percentage
        if (fade >= 1) {
            fade -= 1
            color1 = rgbColor2
            color2 = rgbColor3
        }
    }

    var diffRed = color2.red - color1.red
    var diffGreen = color2.green - color1.green
    var diffBlue = color2.blue - color1.blue

    var gradient = {
        red: parseInt(Math.floor(color1.red + (diffRed * fade)), 10),
        green: parseInt(Math.floor(color1.green + (diffGreen * fade)), 10),
        blue: parseInt(Math.floor(color1.blue + (diffBlue * fade)), 10),
    }

    return 'rgb(' + gradient.red + ',' + gradient.green + ',' + gradient.blue + ')'
}

export function getColorFromFailureToSuccessColorsByPercentage(percentage) {
    const red = {red: 220, green: 53, blue: 69} // danger color
    const orange = {red: 253, green: 193, blue: 7} // warning color
    const green = {red: 40, green: 167, blue: 69} // success color
    return colorGradient((percentage / 100).toString(), red, orange, green)
}
