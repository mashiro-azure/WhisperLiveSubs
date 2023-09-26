import asyncio
import json
import logging

from websockets.exceptions import ConnectionClosed
from websockets.server import serve

from backend.utils import refresh_audio_API_list, refresh_audio_device_list


def ws_server():
    log = logging.getLogger("logger")
    logging.basicConfig(
        format="%(asctime)s - [%(levelname)s]: %(filename)s - %(funcName)s: %(message)s",
        level=logging.DEBUG,
        # datefmt="%Y-%m-%d %H:%M:%S",
    )
    log.info("Backend Initialized.")

    stopServerEvent = asyncio.Event()

    async def processRequest(websocket):
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
                if request["destination"] == "backend":
                    match request["intention"]:  # identify intention if destination is backend.
                        case "IamAlive":
                            message = jsonFormatter("frontend", "IamAlive", "Hello from backend.")
                            await websocket.send(json.dumps(message))
                        case "goodNight":
                            log.info("Good Night: WebSocket closing.")
                            stopServerEvent.set()
                            await websocket.close()
                        case "darkModeSwitch":
                            themeSelect("app_config.json", True)
                        case "lightModeSwitch":
                            themeSelect("app_config.json", False)
                        case "refreshAudioAPI":
                            audioAPIlist = refresh_audio_API_list()
                            message = jsonFormatter("frontend", "refreshAudioAPI", audioAPIlist)
                            await websocket.send(json.dumps(message))
                        case "refreshAudioDeviceList":
                            audioAPIvalue = int(request["message"])
                            audioDeviceList = refresh_audio_device_list(audioAPIvalue)
                            message = jsonFormatter("frontend", "refreshAudioDeviceList", audioDeviceList)
                            await websocket.send(json.dumps(message))
        except ConnectionClosed:
            log.warn("ConnectionClosed: WebSocket closing.")
            await websocket.close()

    async def main():
        async with serve(processRequest, "127.0.0.1", 5001):
            await stopServerEvent.wait()  # run forever

    asyncio.run(main())


def themeSelect(jsonFile: str, setDarkMode: bool):
    with open(jsonFile, mode="r+") as f:
        userConfig: dict = json.load(f)
        userConfig["darkMode"] = setDarkMode
        f.seek(0)
        json.dump(userConfig, f, indent=4)
        f.truncate()


def jsonFormatter(destination: str, intention: str, message: str):
    message = {"destination": destination, "intention": intention, "message": message}
    return message
