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
    var wsMessage = JSON.parse(event.data);
    console.log(wsMessage);
    if (wsMessage.destination == "frontend" && wsMessage.intention == "refreshAudioAPI") {
        console.log(wsMessage.message);
    }
});

// Close WebSocket connection from the browser when the page unloads.
window.addEventListener("beforeunload", () => {
    var message = formatMessage("backend", "goodNight", "Good Sleep.");
    ws.send(message);
    ws.close();
});



// Custom functions to handle web component interaction
const testBtn = document.getElementById("testButton");
testBtn.addEventListener("click", () => {
    var message = formatMessage("backend", "testButton", "Custom button clicked.");
    ws.send(message);
});

const darkModeSwitch = document.getElementById("darkModeSwitch");
darkModeSwitch.addEventListener("click", () => {
    var message = formatMessage("backend", "darkModeSwitch", "Going Dark Mode.");
    ws.send(message);
    document.body.setAttribute("data-bs-theme", "dark")
})

const lightModeSwitch = document.getElementById("lightModeSwitch");
lightModeSwitch.addEventListener("click", () => {
    var message = formatMessage("backend", "lightModeSwitch", "Going Light Mode.");
    ws.send(message);
    document.body.setAttribute("data-bs-theme", "light")
})

const audioRefreshButton = document.getElementById("audioRefreshBtn");
audioRefreshButton.addEventListener("click", () => {
    var message = formatMessage("backend", "refreshAudioAPI", "Want to refresh audio API list.");
    ws.send(message);
})