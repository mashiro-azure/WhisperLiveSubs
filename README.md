# WhisperLiveSubs
An attempt to add near real-time capability to OpenAI's Whisper, coupled with a web UI that is tailored for streaming. This project uses Whisper locally, no API keys needed.

![whisperlivesubs](https://github.com/mashiro-azure/WhisperLiveSubs/assets/23091058/8da0d7e3-69f3-4fbc-9823-aaf5255ed7a3)

## Requirements
- Python: Version 3.10 - 3.11
- GPU (optional): AMD Radeon RX 6600+ / Nvidia GeForce GTX 900+
- Operating System: Tested for Windows 10 / Ubuntu Linux
- Web Browser: Modern versions of Firefox / Chrome, with JavaScript enabled
- Available ports: 5000, 5001

## Setup
1. Install [Python](https://www.python.org/downloads/) 3.10.X or 3.11.X.
  > [!IMPORTANT]
  > During installation on Windows, check "Add Python 3.X to PATH". Re-login to apply the changes.
2. Download and unpack the latest release, through the sidebar on Github or `git clone`
3. Open a command prompt / terminal in the unpacked folder, and create a virtual environment using `python -m venv pick_a_name_for_your_venv`
4. Activate the virtual environment, by doing
    - Debian-based systems: `source ./pick_a_name_for_your_venv/bin/activate`
    - Windows systems: `pick_a_name_for_your_venv\Scripts\activate`
5. Installing libraries,
    <details>
      <summary>CPU only</summary>

      1. Visit [PyTorch](https://pytorch.org/get-started/locally/), and complete the helper form. Pick "CPU" in the "Compute Platform" row.
      1. Copy and execute the command shown by the form.
      1. Install PyAudio by doing
          - Debian-based systems: `sudo apt install python3-pyaudio`
          - Windows systems: `pip install pyaudio`
      1. Run `pip install -r requirements.txt`
      1. All Done! :heavy_check_mark:
    </details>

    <details>
      <summary>AMD GPU (Linux only)</summary>

      1. Visit [PyTorch](https://pytorch.org/get-started/locally/), and complete the helper form. Pick "ROCm" in the "Compute Platform" row.
      1. Copy and execute the command shown by the form.
      1. Install PyAudio by running `sudo apt install python3-pyaudio`
      1. Run `pip install -r requirements.txt`
      1. All Done! :heavy_check_mark:
    </details>

    <details>
      <summary>Nvidia GPU</summary>

      1. Visit [PyTorch](https://pytorch.org/get-started/locally/), and complete the helper form. Pick "CUDA" in the "Compute Platform" row. _The newer CUDA version is recommended by the PyTorch Team._
      1. Copy and execute the command shown by the form.
      1. Install PyAudio by doing
          - Debian-based systems: `sudo apt install python3-pyaudio`
          - Windows systems: `pip install pyaudio`
      1. Run `pip install -r requirements.txt`
      1. All Done! :heavy_check_mark:
    </details>
  > [!NOTE]
  > If `python3-pyaudio` is not available, you'll have to compile PyAudio from source. Check the wiki for more information.
6. Execute `python app.py` and navigate to 127.0.0.1:5000.
7. Fullscreen subtitles are available on 127.0.0.1:5000/subs. Use window capture / browser source to capture the fullscreen subtitles page.
  > [!IMPORTANT]
  > For optimal inference quality, please setup your audio according to the [OBS's audio mixer guide](https://obsproject.com/kb/audio-mixer-guide#zones).

For more information, please consult the wiki.

## Contributing
This project uses `Flake8` and `Black` to lint and format python files. It also uses the default linters and formatters in Visual Studio Code for HTML, JavaScript and CSS.

## Disclaimer
This is my first proper project, don't expect high quality code. I'm just a guy who copies and pastes. However, I hope that you'll find this project somewhat useful. Thanks for checking this out.
