import asyncio
import json
import logging
import queue
import threading
from configparser import ConfigParser

from websockets import broadcast
from websockets.exceptions import ConnectionClosed
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
                    match request["intention"]:  # identify intention if destination is backend.
                        case "IamAlive":
                            message = jsonFormatter("frontend", "IamAlive", "Hello from backend.")
                            await websocket.send(json.dumps(message))
                        case "goodNight":
                            log.info("Good Night: WebSocket closing.")
                            stopServerEvent.set()
                            await websocket.close()
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
                    match request["intention"]:
                        case "IamAlive":
                            log.info("Subs_frontend connecting to Websocket.")
                            message = jsonFormatter("subs_frontend", "IamAlive", "Good morning, from backend to subs.")
                            await websocket.send(json.dumps(message))
                        case "goodNight":
                            log.info("Subs_frontend disconnecting from Websocket.")
                        case "askForWhisperResults":
                            if request["message"] == "request":
                                try:
                                    whisperResult = whisperOutputQueue.get(block=False)
                                    message = jsonFormatter("subs_frontend", "askForWhisperResults", whisperResult)
                                    broadcast(websocketConnections, json.dumps(message))
                                except queue.Empty:
                                    continue
        except ConnectionClosed:
            log.warn("ConnectionClosed: WebSocket closing.")
            await websocket.close()

    async def main():
        async with serve(processRequest, "127.0.0.1", 5001):
            await stopServerEvent.wait()  # run forever

    asyncio.run(main())


def themeSelect(configFileName: str, config: ConfigParser, setDarkMode: str):
    with open(configFileName, mode="w") as f:
        config["user.config"]["darkMode"] = setDarkMode
        config.write(f)
