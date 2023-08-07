// WebSocket stuff
const ws = new WebSocket("ws://127.0.0.1:5001")
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
    var message = formatMessage("backend", "IamAlive", "Hello from client.");
    ws.send(message);
});

ws.addEventListener("close", () => {
    console.log("WebSocket connection closing.");
});

ws.addEventListener("message", (event) => {
    console.log(event.data);
});

// Close WebSocket connection from the browser when the page unloads.
window.addEventListener("pagehide", () => {
    ws.close();
});



// Custom functions to handle web component interaction
const testBtn = document.getElementById("testButton");
testBtn.addEventListener("click", () => {
    var message = formatMessage("backend", "testButton", "Custom button clicked.");
    ws.send(message);
});