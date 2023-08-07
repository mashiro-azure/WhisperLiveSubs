import asyncio
import json
import logging

from websockets.exceptions import ConnectionClosed
from websockets.server import serve


def ws_server():
    log = logging.getLogger("logger")
    logging.basicConfig(
        format="%(asctime)s - [%(levelname)s]: %(filename)s - %(funcName)s: %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log.info("Backend Initialized.")

    async def processRequest(websocket):
        try:
            async for message in websocket:
                log.info(f"Incoming message: {message}")
                request = json.loads(message)
                """
                request:
                    Contains a three-argument JSON object, including:
                    "destination": string, usually "backend" / "frontend"
                    "intention": string
                    "message": string
                """
                if request["destination"] == "backend":
                    if request["intention"] == "IamAlive":
                        await websocket.send("Hello from backend.")
        except ConnectionClosed:
            await websocket.close()
            log.info("WebSocket closing.")

    async def main():
        async with serve(processRequest, "127.0.0.1", 5001):
            await asyncio.Future()  # run forever

    asyncio.run(main())
