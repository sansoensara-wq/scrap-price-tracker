"""
ระบบแจ้งเตือน — ส่งข้อความกลับ LINE เมื่อราคาเกิน/ต่ำกว่า threshold
"""

import os
from linebot import LineBotApi
from linebot.models import TextSendMessage
from database import get_alerts

_fired: set[int] = set()


def check_and_notify(entries: list, line_bot_api: LineBotApi, source_id: str, source_type: str):
    if not line_bot_api.access_token:
        return

    alerts = get_alerts()
    messages = []

    for entry in entries:
        for alert in alerts:
            if not alert["active"]:
                continue
            # ถ้า alert ระบุ category ให้จับคู่กัน
            if alert["category"] and alert["category"] != entry.category:
                continue

            triggered = (
                (alert["direction"] == "above" and entry.price >= alert["threshold"])
                or (alert["direction"] == "below" and entry.price <= alert["threshold"])
            )
            key = (alert["id"], entry.category)
            if triggered and key not in _fired:
                _fired.add(key)
                direction_th = "สูงกว่า ↑" if alert["direction"] == "above" else "ต่ำกว่า ↓"
                messages.append(
                    f"🔔 แจ้งเตือน [{alert['label']}]\n"
                    f"หมวด: {entry.category}\n"
                    f"ราคา {entry.price:,.2f} {direction_th} {alert['threshold']:,.2f}"
                )
            elif not triggered:
                _fired.discard((alert["id"], entry.category))

    if not messages:
        return

    try:
        line_bot_api.push_message(
            source_id, [TextSendMessage(text=m) for m in messages]
        )
    except Exception as e:
        print(f"[notifier] error: {e}")


def send_line_notify(message: str):
    """ส่งผ่าน LINE Notify token"""
    token = os.getenv("LINE_NOTIFY_TOKEN", "")
    if not token:
        print("[notifier] LINE_NOTIFY_TOKEN not set")
        return
    import urllib.request, urllib.parse
    data = urllib.parse.urlencode({"message": f"\n{message}"}).encode()
    req = urllib.request.Request(
        "https://notify-api.line.me/api/notify",
        data=data,
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as res:
            print(f"[notifier] LINE Notify sent: {res.status}")
    except Exception as e:
        print(f"[notifier] error: {e}")
