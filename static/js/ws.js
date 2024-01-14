// This file is responsible for the JavaScript of control panel.
// frontend (ws.js) <-> backend (ws_server.py)

// WebSocket
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

/**
 * 
 * @param {string} message should be wsMessage.message with a "UUID: xxx"
 * @returns {string}
 */
function extractUUID(message) {
    var uuid = message.split(": ")[1];
    return uuid;
};

// Tells frontend websocket is alive
ws.addEventListener("open", () => {
    var message = formatMessage("backend", "IamAlive", "Hello from client.");
    ws.send(message);
});

ws.addEventListener("close", () => {
    console.log("WebSocket connection closing.");
});

// empty global variable to store device information
let deviceDetailedInfo;
let askForWhisperResultsID;
let websocketUUID;

// Websocket - Message Handling
ws.addEventListener("message", (event) => {
    var wsMessage = JSON.parse(event.data);
    console.log(wsMessage);

    // messages coming from ws_server.py
    if (wsMessage.destination == "frontend") {
        switch (wsMessage.intention) {
            case "IamAlive":
                websocketUUID = extractUUID(wsMessage.message);
                refreshAudioAPIList();
                loadSettings();
                break;
            case "applySettings":
                applySettings(wsMessage);
                break;
            case "refreshAudioAPI":
                populateAudioAPIList(wsMessage.message);
                break;
            case "refreshAudioDeviceList":
                deviceDetailedInfo = wsMessage.message;
                populateAudioDeviceList(deviceDetailedInfo);
                break;
            case "checkWhisperStarted":
                startWhisperButton.classList.remove("btn-primary", "btn-loading");
                startWhisperButton.classList.add("btn-outline-danger");
                startWhisperButton.textContent = "Stop Whisper";
                clearInterval(checkWhisperStartedTimeoutID);
                whisperIsActive = true;
                askForWhisperResultsID = setInterval(askForWhisperResults, 500);
                break;
            case "stopWhisper":
                startWhisperButton.classList.remove("btn-outline-danger", "btn-loading");
                startWhisperButton.classList.add("btn-primary");
                startWhisperButton.textContent = "Start Whisper";
                whisperIsActive = false;
                clearInterval(askForWhisperResultsID);
                break;
            case "subsFrontend_alive":
                SubtitleWebsocketStatus_Disconnected.style.display = "none";
                SubtitleWebsocketStatus_Connected.style.display = "block";
                break;
            case "subsFrontend_dead":
                SubtitleWebsocketStatus_Disconnected.style.display = "block";
                SubtitleWebsocketStatus_Connected.style.display = "none";
                break;
            case "retrieveSubsSettings":
                var subsSettings = {
                    "textColor": SubtitleSettings_TextColor.value,
                    "textSize": parseInt(SubtitleSettings_TextSize.value),
                    "textFontFamily": SubtitleSettings_TextFontFamily.value,
                    "textFontWeight": parseInt(SubtitleSettings_TextFontWeight.value),
                    "strokeColor": SubtitleSettings_StrokeColor.value,
                    "strokeWidth": parseInt(SubtitleSettings_StrokeWidth.value),
                    "strokeSteps": parseInt(SubtitleSettings_StrokeSteps.value),
                };
                var message = formatMessage("subs_backend", "retrievedSubsSettings", subsSettings)
                ws.send(message);
                break;
            case "savedAudioSettings":
                var toast = convertToBSToast("toast_audioSettingSaved");
                toast.show();
                break;
            case "savedWhisperSettings":
                var toast = convertToBSToast("toast_whisperSettingSaved");
                toast.show();
                break;
            case "savedSubtitleSettings":
                var toast = convertToBSToast("toast_subtitleSettingSaved");
                toast.show();
                break;
        };
    };
});

// Close WebSocket connection from the browser when the page unloads.
window.addEventListener("beforeunload", (e) => {
    if (whisperIsActive === true) {
        var toast = convertToBSToast("toast_whisperStillRunning");
        toast.show();
        e.preventDefault();
    } else {
        var message = formatMessage("backend", "goodNight", "Good Sleep.");
        ws.send(message);
        ws.close();
    };
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

function loadSettings() {
    var message = formatMessage("backend", "loadSettings", "request");
    ws.send(message);
};

function applySettings(wsMessage) { // I could refactor this into not relying wsMessage.
    AudioSetting_VolumeThreshold.value = AudioSetting_VolumeThresholdInput.value = parseInt(wsMessage.message["audio_volumethreshold"]);
    AudioSetting_VoiceTimeout.value = AudioSetting_VoiceTimeoutInput.value = parseInt(wsMessage.message["audio_voicetimeoutms"]);
    WhisperSettings_ModelSize.value = wsMessage.message["whisper_modelsize"];
    WhisperSettings_InputLanguage.value = wsMessage.message["whisper_language"];
    if (wsMessage.message["whisper_task"] == "transcribe") {
        WhisperSettings_TaskTranscribe.checked = true;
        WhisperSettings_TaskTranslate.checked = false;
    } else {
        WhisperSettings_TaskTranscribe.checked = false;
        WhisperSettings_TaskTranslate.checked = true;
    };
    if (wsMessage.message["whisper_usegpu"] == "true") {
        WhisperSettings_GPUon.checked = true;
        WhisperSettings_GPUoff.checked = false;
    } else {
        WhisperSettings_GPUon.checked = false;
        WhisperSettings_GPUoff.checked = true;
    };
    SubtitleSettings_TextColor.value = wsMessage.message["subtitle_textcolor"];
    SubtitleSettings_TextSize.value = parseInt(wsMessage.message["subtitle_textsize"]);
    if (wsMessage.message["subtitle_textfontfamily"] == "sans-serif") {
        SubtitleSettings_TextFontFamily.value = ''
    } else {
        SubtitleSettings_TextFontFamily.value = wsMessage.message["subtitle_textfontfamily"];
    };
    SubtitleSettings_TextFontWeight.value = parseInt(wsMessage.message["subtitle_textfontweight"]);
    SubtitleSettings_StrokeColor.value = wsMessage.message["subtitle_strokecolor"];
    SubtitleSettings_StrokeWidth.value = parseInt(wsMessage.message["subtitle_strokewidth"]);
    SubtitleSettings_StrokeSteps.value = parseInt(wsMessage.message["subtitle_strokesteps"]);

    // update coloris color pickers thumbnail
    SubtitleSettings_StrokeSteps.dispatchEvent(new Event("change"));
    SubtitleSettings_TextColor.dispatchEvent(new Event("input", { bubbles: true }));
    SubtitleSettings_StrokeColor.dispatchEvent(new Event("input", { bubbles: true }));
};

// Audio settings - Components
const audioRefreshButton = document.getElementById("audioRefreshBtn");
const AudioSetting_Save = document.getElementById("AudioSetting_Save");
// const AudioSetting_Reset = document.getElementById("AudioSetting_Reset");

const AudioSetting_API = document.getElementById("AudioSetting_API");
const AudioSetting_InputDevice = document.getElementById("AudioSetting_InputDevice");
const AudioSetting_SampleRate = document.getElementById("AudioSetting_SampleRate");
const AudioSetting_Channels = document.getElementById("AudioSetting_Channels");

const AudioSetting_VolumeThreshold = document.getElementById("slider_volThres");
const AudioSetting_VolumeThresholdInput = document.getElementById("input_volThres");
const AudioSetting_VoiceTimeout = document.getElementById("slider_voiceTimeout");
const AudioSetting_VoiceTimeoutInput = document.getElementById("input_voiceTimeout");

// Audio Settings - Save and Reset
function saveAudioSettings() {
    var audioSettings = {
        "VolumeThreshold": parseInt(AudioSetting_VolumeThresholdInput.value),
        "VoiceTimeout": parseInt(AudioSetting_VoiceTimeoutInput.value)
    };
    return audioSettings;
};

AudioSetting_Save.addEventListener("click", () => {
    var audioSettings = saveAudioSettings();
    var message = formatMessage("backend", "saveAudioSettings", audioSettings);
    ws.send(message);
});


// Audio Settings - Audio API
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
    // If the deviceList is empty, don't call the populate...() functions.
    if (deviceList.length == 0) {
        var toast = convertToBSToast("toast_errorDeviceListEmpty");
        toast.show();
        return -1;
    } else {
        // Manually invoked for the first time as event listener doesn't trigger
        populateAudioDeviceSampleRate(deviceList[0].index);
        populateAudioDeviceChannels(deviceList[0].index);
    };
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


// Whisper Settings - Components
const startWhisperButton = document.getElementById("startBtn");
const WhisperSettings_Save = document.getElementById("WhisperSettings_Save");
// const WhisperSettings_Reset = document.getElementById("WhisperSettings_Reset");
const WhisperSettings_ModelSize = document.getElementById("WhisperModelSize");
const WhisperSettings_InputLanguage = document.getElementById("WhisperInputLanguage");
const WhisperSettings_TaskTranscribe = document.getElementById("WhisperTask_Transcribe");
const WhisperSettings_TaskTranslate = document.getElementById("WhisperTask_Translate");
const WhisperSettings_GPUon = document.getElementById("WhisperGPU_on");
const WhisperSettings_GPUoff = document.getElementById("WhisperGPU_off");

// Whisper Settings - Save and Reset
function saveWhisperSettings() {
    var whisperSettings = {
        "ModelSize": WhisperSettings_ModelSize.value,
        "InputLanguage": WhisperSettings_InputLanguage.value,
        "Task": checkWhisperTask(),
        "useGPU": checkWhisperGPU()
    };
    return whisperSettings;
};

WhisperSettings_Save.addEventListener("click", () => {
    var whisperSettings = saveWhisperSettings();
    var message = formatMessage("backend", "saveWhisperSettings", whisperSettings);
    ws.send(message);
});

// Whisper Settings - Start Whisper Button
let checkWhisperStartedTimeoutID;
let whisperIsActive = false;
startWhisperButton.addEventListener("click", () => {
    if (whisperIsActive === true) { // stop whisper
        var message = formatMessage("backend", "stopWhisper", "request");
        ws.send(message);
        startWhisperButton.classList.add("btn-loading");
    }
    else { // start whisper
        // return device, sample rate, channels, volume threshold, voice timeout, whisper model size, language, task to backend
        var userAudioSettings = collectUserSettings();
        switch (userAudioSettings) {
            case -1:
                break;
            default:
                var message = formatMessage("backend", "startWhisper", userAudioSettings);
                ws.send(message);
                startWhisperButton.classList.add("btn-loading"); // disable start whisper button to prevent spam clicking
                checkWhisperStartedTimeoutID = setInterval(checkWhisperStarted, 2000); // check if whisper has started from backend
        };
    };
});

function checkWhisperStarted() {
    var message = formatMessage("backend", "checkWhisperReady", "request");
    ws.send(message);
}

// Whisper Settings - Check Whisper Task
function checkWhisperTask() {
    return WhisperTask = document.querySelector('input[name="WhisperTask"]:checked').value;
};

// Whisper Settings - Check Whisper running on GPU
function checkWhisperGPU() {
    return WhisperGPU = document.querySelector('input[name="WhisperGPU"]:checked').value;
};

// Whisper Settings - Collect User Settings
function collectUserSettings() {
    if (AudioSetting_InputDevice.value == "") {
        var toast = convertToBSToast("toast_audioDeviceMissing");
        toast.show();
        return -1;
    };

    return userSettings = {
        "InputDevice": parseInt(AudioSetting_InputDevice.value),
        "AudioSampleRate": parseInt(AudioSetting_SampleRate.value),
        "AudioChannel": parseInt(AudioSetting_Channels.value),
        "VolumeThreshold": parseInt(AudioSetting_VolumeThresholdInput.value),
        "VoiceTimeout": parseInt(AudioSetting_VoiceTimeoutInput.value),
        "WhisperModelSize": WhisperSettings_ModelSize.value,
        "WhisperLanguage": WhisperSettings_InputLanguage.value,
        "WhisperTask": checkWhisperTask(), // "transcribe" / "translate"
        "WhisperGPU": checkWhisperGPU(), // "true" / "false"
    };
};

function askForWhisperResults() {
    var message = formatMessage("subs_backend", "askForWhisperResults", "request");
    ws.send(message);
};

// Toast - Converter
function convertToBSToast(toast_id) {
    var toast = document.getElementById(toast_id);
    var bsToast = new bootstrap.Toast(toast);
    return bsToast;
};

// Subs Settings - Color pickers
document.addEventListener("DOMContentLoaded", function () {
    window.Coloris && (Coloris({
        el: "#SubtitleSettings_TextColor",
        selectInput: false,
        alpha: false,
        format: "hex",
        swatches: [
            "#0054a6",
            "#45aaf2",
            "#6574cd",
            "#a55eea",
            "#f66d9b",
            "#fa4654",
            "#fd9644",
            "#f1c40f",
            "#7bd235",
            "#5eba00",
            "#2bcbba",
            "#17a2b8",
        ],
    }))
});

document.addEventListener("DOMContentLoaded", function () {
    window.Coloris && (Coloris({
        el: "#SubtitleSettings_StrokeColor",
        selectInput: false,
        alpha: false,
        format: "hex",
        swatches: [
            "#0054a6",
            "#45aaf2",
            "#6574cd",
            "#a55eea",
            "#f66d9b",
            "#fa4654",
            "#fd9644",
            "#f1c40f",
            "#7bd235",
            "#5eba00",
            "#2bcbba",
            "#17a2b8",
        ],
    }))
});

// Subtitle Settings - Components
const SubtitleWebsocketStatus_Disconnected = document.getElementById("SubtitleWebsocketStatus_Disconnected");
const SubtitleWebsocketStatus_Connected = document.getElementById("SubtitleWebsocketStatus_Connected");
const SubtitleSettings_Save = document.getElementById("SubtitleSettings_Save");
// const SubtitleSettings_Reset = document.getElementById("SubtitleSettings_Reset");
const SubtitleSettings_TextColor = document.getElementById("SubtitleSettings_TextColor");
const SubtitleSettings_TextSize = document.getElementById("SubtitleSettings_TextSize");
const SubtitleSettings_TextFontFamily = document.getElementById("SubtitleSettings_TextFontFamily");
const SubtitleSettings_TextFontWeight = document.getElementById("SubtitleSettings_TextFontWeight");
const SubtitleSettings_StrokeColor = document.getElementById("SubtitleSettings_StrokeColor");
const SubtitleSettings_StrokeWidth = document.getElementById("SubtitleSettings_StrokeWidth");
const SubtitleSettings_StrokeSteps = document.getElementById("SubtitleSettings_strokeSteps");
const SubtitleSettings_StrokeStepsWarningIcon = document.getElementById("SubtitleSettings_StrokeStepsWarningIcon");
const SubtitleSettings_StrokeStepsWarningText = document.getElementById("SubtitleSettings_StrokeStepsWarningText");

// Subtitle Settings - Save and Reset
function saveSubtitleSettings() {
    var subtitleSettings = {
        "TextColor": SubtitleSettings_TextColor.value,
        "TextSize": parseInt(SubtitleSettings_TextSize.value),
        "TextFontFamily": SubtitleSettings_TextFontFamily.value,
        "TextFontWeight": parseInt(SubtitleSettings_TextFontWeight.value),
        "StrokeColor": SubtitleSettings_StrokeColor.value,
        "StrokeWidth": parseInt(SubtitleSettings_StrokeWidth.value),
        "StrokeSteps": parseInt(SubtitleSettings_StrokeSteps.value)
    };
    return subtitleSettings;
};

SubtitleSettings_Save.addEventListener("click", () => {
    var subtitleSettings = saveSubtitleSettings();
    var message = formatMessage("backend", "saveSubtitleSettings", subtitleSettings);
    ws.send(message);
});

// Subtitle Settings - Detect change and send through WS
SubtitleSettings_TextColor.addEventListener('input', (e) => {
    var newColor = e.target.value;
    var message = formatMessage("subs_backend", "changeTextColor", newColor);
    ws.send(message);
});

SubtitleSettings_TextSize.addEventListener('change', (e) => {
    var newValue = e.target.value;
    var message = formatMessage("subs_backend", "changeTextSize", parseInt(newValue));
    ws.send(message);
});

SubtitleSettings_TextFontFamily.addEventListener("change", (e) => {
    var newFontFamily = e.target.value;
    var message = formatMessage("subs_backend", "changeTextFontFamily", newFontFamily);
    ws.send(message);
});

SubtitleSettings_TextFontWeight.addEventListener("change", (e) => {
    var newFontWeight = e.target.value;
    var message = formatMessage("subs_backend", "changeTextFontWeight", newFontWeight);
    ws.send(message);
});

SubtitleSettings_StrokeColor.addEventListener('input', (e) => {
    var newColor = e.target.value;
    var message = formatMessage("subs_backend", "changeStrokeColor", newColor);
    ws.send(message);
});

SubtitleSettings_StrokeWidth.addEventListener("change", (e) => {
    var newValue = e.target.value;
    var message = formatMessage("subs_backend", "changeStrokeWidth", parseInt(newValue));
    ws.send(message);
});

SubtitleSettings_StrokeSteps.addEventListener('change', (e) => {
    var newValue = e.target.value;
    var message = formatMessage("subs_backend", "changeStrokeStep", parseInt(newValue));
    ws.send(message);
    if (newValue > 16) {
        SubtitleSettings_StrokeStepsWarningIcon.setAttribute("visibility", "");
        SubtitleSettings_StrokeStepsWarningText.hidden = false;
    } else {
        SubtitleSettings_StrokeStepsWarningIcon.setAttribute("visibility", "hidden");
        SubtitleSettings_StrokeStepsWarningText.hidden = true;
    }
});
