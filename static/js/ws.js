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

// empty global variable to store device information
let deviceDetailedInfo;

ws.addEventListener("message", (event) => {
    var wsMessage = JSON.parse(event.data);
    console.log(wsMessage);

    if (wsMessage.destination == "frontend") {
        switch (wsMessage.intention) {
            case "IamAlive":
                refreshAudioAPIList();
                break;
            case "refreshAudioAPI":
                populateAudioAPIList(wsMessage.message);
                break;
            case "refreshAudioDeviceList":
                deviceDetailedInfo = wsMessage.message;
                populateAudioDeviceList(deviceDetailedInfo);
                break;
        };
    };
});

// Close WebSocket connection from the browser when the page unloads.
window.addEventListener("beforeunload", () => {
    var message = formatMessage("backend", "goodNight", "Good Sleep.");
    ws.send(message);
    ws.close();
});

// Custom functions to handle web component interaction
const darkModeSwitch = document.getElementById("darkModeSwitch");
darkModeSwitch.addEventListener("click", () => {
    var message = formatMessage("backend", "darkModeSwitch", "Going Dark Mode.");
    ws.send(message);
    document.body.setAttribute("data-bs-theme", "dark");
});

const lightModeSwitch = document.getElementById("lightModeSwitch");
lightModeSwitch.addEventListener("click", () => {
    var message = formatMessage("backend", "lightModeSwitch", "Going Light Mode.");
    ws.send(message);
    document.body.setAttribute("data-bs-theme", "light");
});


// Audio settings - Components
const AudioSetting_API = document.getElementById("AudioSetting_API");
const AudioSetting_InputDevice = document.getElementById("AudioSetting_InputDevice");
const AudioSetting_SampleRate = document.getElementById("AudioSetting_SampleRate");
const AudioSetting_Channels = document.getElementById("AudioSetting_Channels");

const audioRefreshButton = document.getElementById("audioRefreshBtn");
const startWhisperButton = document.getElementById("startBtn");

const AudioSetting_VolumeThreshold = document.getElementById("slider_volThres");
const AudioSetting_VolumeThresholdInput = document.getElementById("input_volThres");
const AudioSetting_VoiceTimeout = document.getElementById("slider_voiceTimeout");
const AudioSetting_VoiceTimeoutInput = document.getElementById("input_voiceTimeout");

// Audio settings - Audio API
function refreshAudioAPIList() {
    var message = formatMessage("backend", "refreshAudioAPI", "Want to refresh audio API list.");
    ws.send(message);
};

function populateAudioAPIList(APIListInJson) {
    const audioInfo = APIListInJson;
    var apiCount = audioInfo.apiCount;
    var apiType = audioInfo.apiType;
    var apiName = audioInfo.apiName;

    AudioSetting_API.options.length = 0; // clear drop down list
    for (var i = 0; i < apiCount; i++) {
        var item = document.createElement("option");
        item.textContent = apiName[i];
        item.value = apiType[i];
        AudioSetting_API.append(item);
    };
};

// Audio settings - Audio Device
AudioSetting_API.addEventListener("change", () => {
    refreshAudioDeviceList();
});

function refreshAudioDeviceList() {
    var audioAPI = AudioSetting_API.value;
    var message = formatMessage("backend", "refreshAudioDeviceList", audioAPI);
    ws.send(message);
};

function populateAudioDeviceList(DeviceListInJSON) {
    AudioSetting_InputDevice.options.length = 0;

    var deviceList = DeviceListInJSON.deviceList;
    for (var i = 0; i < deviceList.length; i++) {
        var item = document.createElement("option");
        item.textContent = deviceList[i]["name"];
        item.value = deviceList[i]["index"];
        AudioSetting_InputDevice.append(item);
    };
    // Manually invoked for the first time as event listener doesn't trigger
    populateAudioDeviceSampleRate(deviceList[0].index);
    populateAudioDeviceChannels(deviceList[0].index);
};

// Audio Device refresh sample rate and channels drop-down
AudioSetting_InputDevice.addEventListener("change", () => {
    var deviceIndex = parseInt(AudioSetting_InputDevice.value);
    populateAudioDeviceSampleRate(deviceIndex);
    populateAudioDeviceChannels(deviceIndex);
});

// Audio settings - Sample Rate
function populateAudioDeviceSampleRate(deviceIndex) {
    AudioSetting_SampleRate.options.length = 0;

    var sampleRate = deviceDetailedInfo.deviceList.find(x => x.index === deviceIndex).defaultSampleRate;
    var item = document.createElement("option");
    item.textContent = sampleRate + " Hz";
    item.value = sampleRate;
    AudioSetting_SampleRate.append(item);
};

// Audio settings - Channels
function populateAudioDeviceChannels(deviceIndex) {
    AudioSetting_Channels.options.length = 0;

    var channels = deviceDetailedInfo.deviceList.find(x => x.index === deviceIndex).maxInputChannels;
    for (var i = 1; i <= channels; i++) {
        var item = document.createElement("option");
        item.textContent = i;
        item.value = i;
        AudioSetting_Channels.append(item);
    };
};

// Audio Settings - Refresh Button
audioRefreshButton.addEventListener("click", () => {
    refreshAudioDeviceList();
});

// Audio Settings - Volume Threshold
AudioSetting_VolumeThreshold.addEventListener("input", () => {
    AudioSetting_VolumeThresholdInput.value = AudioSetting_VolumeThreshold.value;
});

AudioSetting_VolumeThresholdInput.addEventListener("beforeinput", (e) => {
    var inputChar = e.data;
    if (!(inputChar >= '0' && inputChar <= '9')) {
        e.preventDefault();
    };
});

AudioSetting_VolumeThresholdInput.addEventListener("input", () => {
    AudioSetting_VolumeThreshold.value = AudioSetting_VolumeThresholdInput.value;
});

// Audio Settings - Voice Timeout
AudioSetting_VoiceTimeout.addEventListener("input", () => {
    AudioSetting_VoiceTimeoutInput.value = AudioSetting_VoiceTimeout.value;
});

AudioSetting_VoiceTimeoutInput.addEventListener("beforeinput", (e) => {
    var inputChar = e.data;
    if (!(inputChar >= '0' && inputChar <= '9')) {
        e.preventDefault();
    };
});

AudioSetting_VoiceTimeoutInput.addEventListener("input", () => {
    AudioSetting_VoiceTimeout.value = AudioSetting_VoiceTimeoutInput.value;
});

// Audio Settings - Start Whisper Button
startWhisperButton.addEventListener("click", () => {
    // return device, sample rate, channels, volume threshold, voice timeout, whisper model size, language, task to backend
    var userAudioSettings; // TODO: work on this
    var message = formatMessage("backend", "startWhisper", userAudioSettings);
});