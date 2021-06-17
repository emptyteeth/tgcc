# tgcc

a simple(rough) chromecast telegram bot

## Credits

- [PyChromecast](https://github.com/home-assistant-libs/pychromecast)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

## Usage

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
