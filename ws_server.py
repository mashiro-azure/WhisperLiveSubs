import asyncio
import json
import logging
import queue
import threading
import uuid
from configparser import ConfigParser

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
                            case "darkModeSwitch":
                                themeSelect(configFileName, config, "true")
                            case "lightModeSwitch":
                                themeSelect(configFileName, config, "false")
                            case "refreshAudioAPI":
                                audioAPIlist = refresh_audio_API_list()
                                message = jsonFormatter("frontend", "refreshAudioAPI", audioAPIlist)
                                await websocket.send(json.dumps(message))
                            case "refreshAudioDeviceList":
                                audioAPIvalue = int(request["message"])
                                audioDeviceList = refresh_audio_device_list(audioAPIvalue)
                                message = jsonFormatter("frontend", "refreshAudioDeviceList", audioDeviceList)
                                await websocket.send(json.dumps(message))
                            case "startWhisper":
                                userSettings = request["message"]
                                whisperThread = whisperProcessing(userSettings, whisperReadyEvent, whisperOutputQueue)
                                whisperThread.start()
                            case "checkWhisperReady":
                                if whisperReadyEvent.is_set() is True:
                                    message = jsonFormatter("frontend", "checkWhisperStarted", "true")
                                    await websocket.send(json.dumps(message))
                            case "stopWhisper":
                                whisperThread.stop()
                                whisperReadyEvent.clear()
                                message = jsonFormatter("frontend", "stopWhisper", "Stopping Whisper")
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
                    else:
                        websocket = findTargetWebsocket("subs_frontend")
                        match request["intention"]:
                            case "goodNight":
                                log.info("Subs_frontend disconnecting from Websocket.")
                                await websocket.close()
                                websocketConnections.remove(websocket)
                                websocketConnectionsUUID["subs_frontend"] = ""
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
                            case "changeStrokeColor":
                                message = jsonFormatter("subs_frontend", "changeStrokeColor", request["message"])
                                await websocket.send(json.dumps(message))
                            case "changeTextSize":
                                message = jsonFormatter("subs_frontend", "changeTextSize", request["message"])
                                await websocket.send(json.dumps(message))
                            case "changeStrokeWidth":
                                message = jsonFormatter("subs_frontend", "changeStrokeWidth", request["message"])
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


def themeSelect(configFileName: str, config: ConfigParser, setDarkMode: str):
    with open(configFileName, mode="w") as f:
        config["user.config"]["darkMode"] = setDarkMode
        config.write(f)
