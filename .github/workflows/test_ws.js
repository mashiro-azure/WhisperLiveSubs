const WebSocket = require('ws');
var ws = new WebSocket("ws://127.0.0.1:5001")

function formatMessage(destination, intention, message) {
    var messageInJson = JSON.stringify({ destination, intention, message });
    return messageInJson;
};

function extractUUID(message) {
    var uuid = message.split(": ")[1];
    return uuid;
};

function checkUUID(websocketUUID) {
    if (!websocketUUID) {
        return 0;
    }
    else { return 1; }
}

ws.addEventListener("open", () => {
    var message = formatMessage("backend", "IamAlive", "Hello from client.");
    ws.send(message);
});

ws.addEventListener("close", () => {
    console.log("WebSocket connection closing.");
});

let websocketUUID;

ws.addEventListener("message", (event) => {
    var wsMessage = JSON.parse(event.data);

    if (wsMessage.destination == "frontend") {
        switch (wsMessage.intention) {
            case "IamAlive":
                websocketUUID = extractUUID(wsMessage.message);
                checkUUID(websocketUUID);
                ws.close()
                break;
        };
    };
});