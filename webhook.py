"""
LINE Bot Webhook — รับข้อความราคาเศษเหล็กจากกลุ่ม LINE (SDK v3)
ตอบ LINE กลับทันที แล้วประมวลผลใน background thread
"""

import os
import sys
import threading
import logging
from flask import Flask, request, abort

# ตั้ง logging ที่ thread-safe
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(message)s",
    handlers=[
        logging.FileHandler("webhook_debug.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, MessagingApiBlob
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
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
    return "OK"  # ตอบ LINE กลับทันที


def _process_text(text, sender, source_id, source_type):
    """ประมวลผลข้อความราคาใน background"""
    try:
        entries = parse_price_message(text, sender=sender, source_id=source_id, source_type=source_type)
        if not entries:
            print(f"[webhook] ไม่ใช่ข้อความราคา: {text[:50]}")
            return
        save_prices(entries)
        print(f"[webhook] บันทึก {len(entries)} รายการจาก {sender}")
        with ApiClient(configuration) as api_client:
            check_and_notify(entries, MessagingApi(api_client), source_id, source_type)
    except Exception as e:
        print(f"[webhook] _process_text error: {e}")


def _process_image(message_id, sender, source_id, source_type):
    """ดาวน์โหลดรูป + OCR + บันทึก ใน background"""
    try:
        log.info(f"_process_image start: message_id={message_id}")
        with ApiClient(configuration) as api_client:
            image_bytes = MessagingApiBlob(api_client).get_message_content(message_id)
        log.info(f"ดาวน์โหลดรูปสำเร็จ: {len(image_bytes)} bytes")

        text = extract_text_from_image_bytes(image_bytes)
        if not text:
            log.warning("OCR อ่านข้อความจากรูปไม่ได้")
            return
        log.info(f"OCR text: {text[:200]}")

        entries = parse_price_message(text, sender=sender, source_id=source_id, source_type=source_type)
        if not entries:
            log.warning("OCR ไม่พบข้อมูลราคาในรูป")
            return
        save_prices(entries)
        log.info(f"บันทึก {len(entries)} รายการจากรูปภาพ")
        with ApiClient(configuration) as api_client:
            check_and_notify(entries, MessagingApi(api_client), source_id, source_type)
    except Exception as e:
        log.error(f"_process_image error: {e}", exc_info=True)


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    sender = getattr(event.source, "user_id", "unknown")
    source_type = event.source.type
    source_id = getattr(event.source, "group_id", None) or getattr(event.source, "room_id", None) or sender
    threading.Thread(
        target=_process_text,
        args=(event.message.text, sender, source_id, source_type),
        daemon=True
    ).start()


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    sender = getattr(event.source, "user_id", "unknown")
    source_type = event.source.type
    source_id = getattr(event.source, "group_id", None) or getattr(event.source, "room_id", None) or sender
    threading.Thread(
        target=_process_image,
        args=(event.message.id, sender, source_id, source_type),
        daemon=True
    ).start()


if __name__ == "__main__":
    init_db()
    print("LINE Price Tracker Webhook running on :5000")
    app.run(port=5000, debug=False, threaded=True)
