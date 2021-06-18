# tgcc

a simple(rough) chromecast telegram bot

## Credits

- [PyChromecast](https://github.com/home-assistant-libs/pychromecast)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

## Usage

- Send audio url
- Share radio station from [radio garden APP](https://play.google.com/store/apps/details?id=com.jonathanpuckey.radiogarden)
- `/status` check device status

## Run

- local

  ```shell
  pip install -r requirements.txt
  tgtoken="TG-BOT-TOKEN" tgchatid="TG-CHAT-ID" python3 tgcc.py
  ```

- container

  ```shell
  docker run -d --network host --restart=unless-stopped \
  -e tgtoken="TG-BOT-TOKEN" -e tgchatid="TG-CHAT-ID" \
  ghcr.io/emptyteeth/tgcc:latest
  ```
