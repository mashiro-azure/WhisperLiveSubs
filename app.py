import configparser
import logging
import os
import sys
import threading

from flask import Flask, render_template

from ws_server import ws_server

app = Flask(__name__)

# Reduce built-in logging for "Flask" and "Websockets"
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("asyncio.coroutines").setLevel(logging.WARNING)
logging.getLogger("websockets.server").setLevel(logging.WARNING)
logging.getLogger("websockets.protocol").setLevel(logging.WARNING)
log = logging.getLogger("logger")


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


@app.route("/subs")
def renderSubsPage():
    return render_template("subs.html")


def readConfigFile():
    configFileName = "app_config.ini"
    if os.path.isfile(configFileName) is False:
        log.error("app_config.ini does not exist, aborting.")
        sys.exit(-1)
    else:
        config = configparser.ConfigParser()
        config.read(configFileName)
        try:
            userConfig = config["user.config"]
            return config, configFileName, userConfig
        except KeyError:
            log.error("Cannot read config. File might be empty.")
            sys.exit(-1)


if __name__ == "__main__":
    config, configFileName, userConfig = readConfigFile()
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
