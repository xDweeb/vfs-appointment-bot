import logging

import requests


class TelegramLogHandler(logging.Handler):
    """Custom logging handler that sends log messages to Telegram.

    All INFO+ level logs are batched and sent to Telegram so you can
    monitor the bot remotely.
    """

    def __init__(self, bot_token: str, chat_id: str):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def emit(self, record):
        try:
            msg = self.format(record)
            # Truncate very long messages (Telegram limit is 4096)
            if len(msg) > 4000:
                msg = msg[:4000] + "..."
            payload = {
                "chat_id": self.chat_id,
                "text": f"```\n{msg}\n```",
                "parse_mode": "Markdown",
            }
            requests.post(self.api_url, json=payload, timeout=10)
        except Exception:
            # Never let logging errors crash the bot
            pass
