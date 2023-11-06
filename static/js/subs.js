function calcualteStrokeTextCSS(steps) { // steps = 16 looks good
    var cssToInject = "";
    for (var i = 0; i < steps; i++) {
        var angle = (i * 2 * Math.PI) / steps;
        var sin = Math.round(10000 * Math.sin(angle)) / 10000;
        var cos = Math.round(10000 * Math.cos(angle)) / 10000;
        cssToInject += "calc(var(--stroke-width) * " +
            sin + ") calc(var(--stroke-width) * " +
            cos + ") 0 var(--stroke-color),";
    };
    cssToInject = cssToInject.slice(0, -1); // to remove the trailing comma
    document.getElementById("subs").style.textShadow = cssToInject;
};
