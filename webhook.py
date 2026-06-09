"""
LINE Bot Webhook — รับข้อความราคาเศษเหล็กจากกลุ่ม LINE (SDK v3)
"""

import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi, MessagingApiBlob,
)
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, ImageMessageContent,
)
from dotenv import load_dotenv

from parser import parse_price_message
from database import save_prices, init_db
from notifier import check_and_notify
from ocr import extract_text_from_image_bytes

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

handler = WebhookHandler(LINE_CHANNEL_SECRET)

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
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
        print(f"[webhook] ข้อความไม่ใช่ราคา: {text[:50]}")
        return

    save_prices(entries)
    print(f"[webhook] saved {len(entries)} entries from {sender}")

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        check_and_notify(entries, line_bot_api, source_id, source_type)


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    """รับรูปภาพจาก LINE แล้วใช้ OCR อ่านราคา"""
    sender = getattr(event.source, "user_id", "unknown")
    source_type = event.source.type
    source_id = (
        getattr(event.source, "group_id", None)
        or getattr(event.source, "room_id", None)
        or sender
    )

    # ดาวน์โหลดรูปจาก LINE
    try:
        with ApiClient(configuration) as api_client:
            blob_api = MessagingApiBlob(api_client)
            image_bytes = blob_api.get_message_content(event.message.id)
    except Exception as e:
        print(f"[webhook] ดาวน์โหลดรูปไม่ได้: {e}")
        return

    # OCR อ่านข้อความจากรูป
    text = extract_text_from_image_bytes(image_bytes)
    if not text:
        print("[webhook] OCR อ่านข้อความจากรูปไม่ได้")
        return

    print(f"[webhook] OCR text:\n{text}")

    entries = parse_price_message(
        text,
        sender=sender,
        source_id=source_id,
        source_type=source_type,
    )

    if not entries:
        print("[webhook] OCR ไม่พบข้อมูลราคาในรูป")
        return

    save_prices(entries)
    print(f"[webhook] saved {len(entries)} entries from image (sender={sender})")

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        check_and_notify(entries, line_bot_api, source_id, source_type)


if __name__ == "__main__":
    init_db()
    print("LINE Price Tracker Webhook running on :5000")
    app.run(port=5000, debug=False)
