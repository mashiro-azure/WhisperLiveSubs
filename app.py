import json
import logging
import threading

from flask import Flask, render_template

from ws_server import ws_server

# Read configurations
with open("app_config.json") as f:
    userConfig: dict = json.load(f)
app = Flask(__name__)

# Reduce built-in logging for "Flask" and "Websockets"
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("asyncio.coroutines").setLevel(logging.WARNING)
logging.getLogger("websockets.server").setLevel(logging.WARNING)
logging.getLogger("websockets.protocol").setLevel(logging.WARNING)


@app.route("/")
def hello_world():
    ws_thread = threading.Thread(target=ws_server, daemon=True)
    ws_thread.start()
    return render_template(
        "empty.html", userConfig=userConfig
    )  # modify body class and show specific button icon (moon / full moon), save and write config using websockets? # noqa: E501


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="5000", debug=True)
