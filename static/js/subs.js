// subs_frontend (subs.js) <-> subs_backend (ws_server.py)

const ws = new WebSocket("ws://127.0.0.1:5001")
let websocketUUID;

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

/**
 * 
 * @param {string} message should be wsMessage.message with a "UUID: xxx"
 * @returns {string}
 */
function extractUUID(message) {
    var uuid = message.split(": ")[1];
    return uuid;
};

ws.addEventListener("open", () => {
    var message = formatMessage("subs_backend", "IamAlive", "Hello from subs.");
    ws.send(message);
    // tries to fetch subtitles settings from control panel, and load them when DOM is ready.
    var message = formatMessage("subs_backend", "retrieveSubsSettings", "request");
    ws.send(message);
});

ws.addEventListener("close", () => {
    console.log("WebSocket connection closing.");
});

// Websocket - Message Handling
ws.addEventListener("message", (event) => {
    var wsMessage = JSON.parse(event.data);
    console.log(wsMessage);

    if (wsMessage.destination == "subs_frontend") {
        switch (wsMessage.intention) {
            case "IamAlive":
                websocketUUID = extractUUID(wsMessage.message);
                break;
            case "askForWhisperResults":
                subs.innerText = wsMessage.message;
                calcualteStrokeTextCSS(4);
                console.log(wsMessage.content);
                break;
            case "changeTextColor":
                setTextColor(wsMessage.message);
                break;
            case "changeTextSize":
                setTextSize(wsMessage.message);
                break;
            case "changeTextFontFamily":
                setFontFamily(wsMessage.message);
                break;
            case "changeTextFontWeight":
                setTextFontWeight(wsMessage.message);
                break;
            case "changeStrokeColor":
                setStrokeColor(wsMessage.message);
                break;
            case "changeStrokeWidth":
                setStrokeWidth(wsMessage.message);
                break;
            case "changeStrokeStep":
                setStrokeSteps(wsMessage.message);
                break;
            case "retrievedSubsSettings":
                setStrokeColor(wsMessage.message["strokeColor"]);
                setStrokeSteps(wsMessage.message["strokeSteps"]);
                setTextColor(wsMessage.message["textColor"]);
                setTextSize(wsMessage.message["textSize"]);
                setFontFamily(wsMessage.message["textFontFamily"]);
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

function setTextColor(newColor) {
    subs.style.setProperty("color", newColor);
    return;
};

function setTextSize(newSize) {
    var newValue = newSize + "px";
    subs.style.setProperty("font-size", newValue);
    return;
};

function setFontFamily(newFont) {
    var newValue;
    if (newFont == "") {
        newValue = "Arial, Helvetica, sans-serif";
    } else {
        newValue = newFont + ", sans-serif"; // sans-serif as backup
    }
    subs.style.setProperty("font-family", newValue);
    return;
};

function setTextFontWeight(newWeight) {
    subs.style.setProperty("font-weight", newWeight);
    return;
};

function setStrokeColor(newColor) {
    subs.style.setProperty("--stroke-color", newColor);
    return;
};

function setStrokeWidth(newSize) {
    var newValue = newSize + "px";
    subs.style.setProperty("--stroke-width", newValue);
    return;
};

function setStrokeSteps(newSize) {
    calcualteStrokeTextCSS(newSize);
    return;
};

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
