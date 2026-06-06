"""
LINE Bot Webhook — รับข้อความราคาเศษเหล็กจากกลุ่ม LINE
"""

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from dotenv import load_dotenv

from parser import parse_price_message
from database import save_prices
from notifier import check_and_notify

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    sender = getattr(event.source, "user_id", "unknown")
    source_type = event.source.type
    source_id = (
        getattr(event.source, "group_id", None)
        or getattr(event.source, "room_id", None)
        or sender
    )

    entries = parse_price_message(
        text,
        sender=sender,
        source_id=source_id,
        source_type=source_type,
    )

    if not entries:
        return

    save_prices(entries)
    check_and_notify(entries, line_bot_api, source_id, source_type)
    print(f"[webhook] saved {len(entries)} entries from {sender}")


if __name__ == "__main__":
    print("LINE Price Tracker Webhook running on :5000")
    app.run(port=5000, debug=True)
