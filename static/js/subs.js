// sub_frontend (This) <-> sub_backend (ws_server.py)

const ws = new WebSocket("ws://127.0.0.1:5001")

// Components
const subs = document.getElementById("subs");

/**
 *
 * @param {string} destination
 * @param {string} intention
 * @param {string} message
 * @return {string}
 */
function formatMessage(destination, intention, message) {
    var messageInJson = JSON.stringify({ destination, intention, message });
    return messageInJson;
};

ws.addEventListener("open", () => {
    var message = formatMessage("subs_backend", "IamAlive", "Hello from subs.");
    ws.send(message);
});

ws.addEventListener("close", () => {
    console.log("WebSocket connection closing.");
});

ws.addEventListener("message", (event) => {
    var wsMessage = JSON.parse(event.data);
    console.log(wsMessage);

    if (wsMessage.destination == "subs_frontend") {
        switch (wsMessage.intention) {
            case "IamAlive":
                break;
            case "askForWhisperResults":
                subs.innerText = wsMessage.message;
                calcualteStrokeTextCSS(16);
                console.log(wsMessage.content);
                break;
            case "changeTextColor":
                subs.style.setProperty("color", wsMessage.message);
                break;
        };
    };
});

// Close WebSocket connection from the browser when the page unloads.
window.addEventListener("beforeunload", () => {
    var message = formatMessage("subs_backend", "goodNight", "Good Sleep.");
    ws.send(message);
    ws.close();
});



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
    subs.style.textShadow = cssToInject;
    return;
};
