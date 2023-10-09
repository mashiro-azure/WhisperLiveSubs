import configparser
import logging
import threading

from flask import Flask, render_template

from ws_server import ws_server

# Read configurations
configFileName = "app_config.ini"
config = configparser.ConfigParser()
config.read(configFileName)
userConfig = config["user.config"]

app = Flask(__name__)

# Reduce built-in logging for "Flask" and "Websockets"
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("asyncio.coroutines").setLevel(logging.WARNING)
logging.getLogger("websockets.server").setLevel(logging.WARNING)
logging.getLogger("websockets.protocol").setLevel(logging.WARNING)


@app.route("/")
def hello_world():
    ws_thread = threading.Thread(
        target=ws_server,
        args=(
            config,
            configFileName,
        ),
        daemon=True,
    )
    ws_thread.start()
    return render_template(
        "empty.html", userConfig=userConfig
    )  # modify body class and show specific button icon (moon / full moon), save and write config using websockets? # noqa: E501


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="5000", debug=True, use_reloader=False)
