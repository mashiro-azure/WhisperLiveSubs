import asyncio
import json
import logging
import os
import queue
import threading
import uuid
from configparser import ConfigParser
from shutil import copy2

from websockets.exceptions import ConnectionClosed
from websockets.legacy.server import WebSocketServerProtocol
from websockets.server import serve

from backend.utils import jsonFormatter, refresh_audio_API_list, refresh_audio_device_list
from backend.whisperProcessing import whisperProcessing


def ws_server(config: ConfigParser, configFileName: str):
    log = logging.getLogger("logger")
    logging.basicConfig(
        format="%(asctime)s - [%(levelname)s]: %(filename)s - %(funcName)s: %(message)s",
        level=logging.DEBUG,
        # datefmt="%Y-%m-%d %H:%M:%S",
    )
    log.info("Backend Initialized.")

    stopServerEvent = asyncio.Event()
    whisperReadyEvent = threading.Event()
    whisperOutputQueue = queue.Queue()
    websocketConnections = []
    websocketConnectionsUUID = {"control_panel": "", "subs_frontend": ""}

    async def processRequest(websocket):
        websocketConnections.append(websocket)
        try:
            async for message in websocket:
                log.debug(f"Incoming message: {message}")
                request = json.loads(message)
                """
                request:
                    Contains a three-argument JSON object, including:
                    "destination": string, usually "backend" / "frontend"
                    "intention": string
                    "message": string
                """

                if request["destination"] == "backend":  # ws.js
                    if websocketConnectionsUUID["control_panel"] == "":
                        match request["intention"]:  # identify intention if destination is backend.
                            case "IamAlive":
                                wsUUID = str(websocket.id)
                                websocketConnectionsUUID["control_panel"] = wsUUID
                                message = jsonFormatter("frontend", "IamAlive", f"Hello from backend. UUID: {wsUUID}")
                                await websocket.send(json.dumps(message))
                    else:
                        websocket = findTargetWebsocket("control_panel")
                        # changing something in the control panel will use the control panel's websocket,
                        # so we need to find the correct websocket to use, that is, the subs_frontend,
                        # to send the message to the right client.
                        match request["intention"]:
                            case "goodNight":
                                log.info("Good Night: WebSocket closing.")
                                stopServerEvent.set()
                                await websocket.close()
                                websocketConnections.remove(websocket)
                                websocketConnectionsUUID["control_panel"] = ""
                                backupConfig(configFileName)
                                log.info("Backing up config file.")
                            case "pruneModels":
                                pruneModels()
                                log.debug("Pruning all models.")
                                message = jsonFormatter("frontend", "prunedModels", "response")
                                await websocket.send(json.dumps(message))
                            case "darkModeSwitch":
                                log.debug("Switching to Dark Mode.")
                                themeSelect(configFileName, config, "true")
                            case "lightModeSwitch":
                                log.debug("Switching to Light Mode.")
                                themeSelect(configFileName, config, "false")
                            case "loadSettings":
                                savedSettings = gatherSettings(configFileName, config)
                                message = jsonFormatter("frontend", "applySettings", savedSettings)
                                await websocket.send(json.dumps(message))
                            case "refreshAudioAPI":
                                log.debug("Audio API List refresh requested.")
                                audioAPIlist = refresh_audio_API_list()
                                message = jsonFormatter("frontend", "refreshAudioAPI", audioAPIlist)
                                await websocket.send(json.dumps(message))
                            case "refreshAudioDeviceList":
                                log.debug("Audio Device List refresh requested.")
                                audioAPIvalue = int(request["message"])
                                audioDeviceList = refresh_audio_device_list(audioAPIvalue)
                                message = jsonFormatter("frontend", "refreshAudioDeviceList", audioDeviceList)
                                await websocket.send(json.dumps(message))
                            case "startWhisper":
                                log.debug("Whisper Start requested.")
                                userSettings = request["message"]
                                whisperThread = whisperProcessing(userSettings, whisperReadyEvent, whisperOutputQueue)
                                whisperThread.start()
                            case "checkWhisperReady":
                                log.debug("Is Whisper ready yet?")
                                if whisperReadyEvent.is_set() is True:
                                    log.debug("Whisper is ready!")
                                    message = jsonFormatter("frontend", "checkWhisperStarted", "true")
                                    await websocket.send(json.dumps(message))
                            case "stopWhisper":
                                log.debug("Whisper stopping!")
                                whisperThread.stop()
                                whisperReadyEvent.clear()
                                message = jsonFormatter("frontend", "stopWhisper", "Stopping Whisper")
                                await websocket.send(json.dumps(message))
                            case "saveAudioSettings":
                                log.info("Saving Audio Settings.")
                                audioSettings = request["message"]
                                saveAudioSettings(configFileName, config, audioSettings)
                                message = jsonFormatter("frontend", "savedAudioSettings", "true")
                                await websocket.send(json.dumps(message))
                            case "saveWhisperSettings":
                                log.info("Saving Whisper Settings.")
                                whisperSettings = request["message"]
                                saveWhisperSettings(configFileName, config, whisperSettings)
                                message = jsonFormatter("frontend", "savedWhisperSettings", "true")
                                await websocket.send(json.dumps(message))
                            case "saveSubtitleSettings":
                                log.info("Saving Subtitle Settings.")
                                subtitleSettings = request["message"]
                                saveSubtitleSettings(configFileName, config, subtitleSettings)
                                message = jsonFormatter("frontend", "savedSubtitleSettings", "true")
                                await websocket.send(json.dumps(message))

                if request["destination"] == "subs_backend":  # subs.js
                    if websocketConnectionsUUID["subs_frontend"] == "":
                        match request["intention"]:
                            case "IamAlive":
                                log.info("Subs_frontend connecting to Websocket.")
                                wsUUID = str(websocket.id)
                                websocketConnectionsUUID["subs_frontend"] = wsUUID
                                message = jsonFormatter(
                                    "subs_frontend",
                                    "IamAlive",
                                    f"Good morning, from backend to subs. UUID: {wsUUID}",
                                )
                                await websocket.send(json.dumps(message))
                                # Notify control panel, subs_frontend is connecting.
                                websocket = findTargetWebsocket("control_panel")
                                message = jsonFormatter("frontend", "subsFrontend_alive", "notify")
                                await websocket.send(json.dumps(message))
                    else:
                        websocket = findTargetWebsocket("subs_frontend")
                        match request["intention"]:
                            case "goodNight":
                                log.info("Subs_frontend disconnecting from Websocket.")
                                await websocket.close()
                                websocketConnections.remove(websocket)
                                websocketConnectionsUUID["subs_frontend"] = ""
                                # Notify control panel, subs_frontend is disconnecting.
                                websocket = findTargetWebsocket("control_panel")
                                message = jsonFormatter("frontend", "subsFrontend_dead", "notify")
                                await websocket.send(json.dumps(message))
                            case "askForWhisperResults":
                                if request["message"] == "request":
                                    try:
                                        whisperResult = whisperOutputQueue.get(block=False)
                                        message = jsonFormatter("subs_frontend", "askForWhisperResults", whisperResult)
                                        await websocket.send(json.dumps(message))
                                    except queue.Empty:
                                        continue
                            case "changeTextColor":
                                message = jsonFormatter("subs_frontend", "changeTextColor", request["message"])
                                await websocket.send(json.dumps(message))
                            case "changeTextSize":
                                message = jsonFormatter("subs_frontend", "changeTextSize", request["message"])
                                await websocket.send(json.dumps(message))
                            case "changeTextFontFamily":
                                message = jsonFormatter("subs_frontend", "changeTextFontFamily", request["message"])
                                await websocket.send(json.dumps(message))
                            case "changeTextFontWeight":
                                message = jsonFormatter("subs_frontend", "changeTextFontWeight", request["message"])
                                await websocket.send(json.dumps(message))
                            case "changeStrokeColor":
                                message = jsonFormatter("subs_frontend", "changeStrokeColor", request["message"])
                                await websocket.send(json.dumps(message))
                            case "changeStrokeWidth":
                                message = jsonFormatter("subs_frontend", "changeStrokeWidth", request["message"])
                                await websocket.send(json.dumps(message))
                            case "changeStrokeStep":
                                message = jsonFormatter("subs_frontend", "changeStrokeStep", request["message"])
                                await websocket.send(json.dumps(message))
                            case "enableLogAnimation":
                                message = jsonFormatter("subs_frontend", "enableLogAnimation", "request")
                                await websocket.send(json.dumps(message))
                            case "disableLogAnimation":
                                message = jsonFormatter("subs_frontend", "disableLogAnimation", "request")
                                await websocket.send(json.dumps(message))
                            case "changeLogLength":
                                message = jsonFormatter("subs_frontend", "changeLogLength", request["message"])
                                await websocket.send(json.dumps(message))
                            case "retrieveSubsSettings":
                                log.debug("Retrieving subtitle settings.")
                                websocket = findTargetWebsocket("control_panel")
                                message = jsonFormatter("frontend", "retrieveSubsSettings", "request")
                                await websocket.send(json.dumps(message))
                            case "retrievedSubsSettings":
                                log.debug("Retrieved subtitle settings.")
                                message = jsonFormatter("subs_frontend", "retrievedSubsSettings", request["message"])
                                await websocket.send(json.dumps(message))
                            case "DEBUG_subtitles":
                                message = jsonFormatter("subs_frontend", "DEBUG_subtitles", request["message"])
                                await websocket.send(json.dumps(message))
        except ConnectionClosed:
            log.warn("ConnectionClosed: WebSocket closing.")
            await websocket.close()

    def findTargetWebsocket(
        websocketConnectionString: str,
    ) -> WebSocketServerProtocol:  # should be either "control_panel" / "subs_frontend"
        wsUUIDstr = websocketConnectionsUUID[websocketConnectionString]
        for i in websocketConnections:
            if i.id == uuid.UUID(wsUUIDstr):
                return i

    async def main():
        async with serve(processRequest, "127.0.0.1", 5001):
            await stopServerEvent.wait()  # run forever

    asyncio.run(main())


def backupConfig(configFileName: str):
    """Backups the app_config.ini file on websocket shutdown with filename, app_config.bk"""
    newFileName = configFileName.split(".")
    newFileName[1] = "bk"
    newFileName = ".".join(newFileName)
    copy2(configFileName, newFileName)


def pruneModels():
    cwd = os.getcwd()
    if os.path.basename(cwd).lower() != "whisperlivesubs":
        pass
    else:
        models_dir = os.path.join(cwd, "backend", "models")
        for models in os.listdir(models_dir):
            if models.endswith(".pt"):
                os.remove(os.path.join(models_dir, models))


def themeSelect(configFileName: str, config: ConfigParser, setDarkMode: str):
    with open(configFileName, mode="w") as f:
        config["user.config"]["darkMode"] = setDarkMode
        config.write(f)


def gatherSettings(configFileName: str, config: ConfigParser):
    with open(configFileName, mode="r") as _:
        savedSettings = {}
        for k, v in config["user.config"].items():
            savedSettings[k] = v
        return savedSettings  # The values will all be in strings, remember to parse them in JS.


def saveAudioSettings(configFileName: str, config: ConfigParser, audioSettings: str):
    with open(configFileName, mode="w") as f:
        config["user.config"]["audio_volumethreshold"] = str(audioSettings["VolumeThreshold"])
        config["user.config"]["audio_voicetimeoutms"] = str(audioSettings["VoiceTimeout"])
        config.write(f)


def saveWhisperSettings(configFileName: str, config: ConfigParser, whisperSettings: str):
    with open(configFileName, mode="w") as f:
        config["user.config"]["whisper_modelsize"] = str(whisperSettings["ModelSize"])
        config["user.config"]["whisper_language"] = str(whisperSettings["InputLanguage"])
        config["user.config"]["whisper_task"] = str(whisperSettings["Task"])
        config["user.config"]["whisper_usegpu"] = str(whisperSettings["useGPU"])
        config.write(f)


def saveSubtitleSettings(configFileName: str, config: ConfigParser, subtitleSettings: str):
    with open(configFileName, mode="w") as f:
        config["user.config"]["subtitle_textcolor"] = str(subtitleSettings["TextColor"])
        config["user.config"]["subtitle_textsize"] = str(subtitleSettings["TextSize"])
        # Text Font Family could be empty, this should fallback to 'sans-serif'
        if subtitleSettings["TextFontFamily"] == "":
            TextFontFamily = "sans-serif"
        else:
            TextFontFamily = str(subtitleSettings["TextFontFamily"])
        config["user.config"]["subtitle_textfontfamily"] = str(TextFontFamily)
        config["user.config"]["subtitle_textfontweight"] = str(subtitleSettings["TextFontWeight"])
        config["user.config"]["subtitle_strokecolor"] = str(subtitleSettings["StrokeColor"])
        config["user.config"]["subtitle_strokewidth"] = str(subtitleSettings["StrokeWidth"])
        config["user.config"]["subtitle_strokesteps"] = str(subtitleSettings["StrokeSteps"])
        config["user.config"]["subtitle_animation_enabled"] = str(subtitleSettings["AnimationEnabled"]).lower()
        config["user.config"]["subtitle_loglength"] = str(subtitleSettings["LogLength"])
        config.write(f)
