"""
OCR Module — อ่านข้อความราคาเศษเหล็กจากรูปภาพด้วย Google Cloud Vision API
"""

import os
import json
import tempfile
from pathlib import Path


def _setup_credentials():
    """
    ตั้งค่า Google credentials จาก:
    1. Streamlit secrets (GOOGLE_CREDENTIALS_JSON) — ใช้บน Streamlit Cloud
    2. ไฟล์ JSON ในโฟลเดอร์โปรเจค — ใช้บนเครื่อง local
    """
    # ลอง Streamlit secrets ก่อน
    try:
        import streamlit as st
        creds_json = st.secrets.get("GOOGLE_CREDENTIALS_JSON", None)
        if creds_json:
            # เขียนลง temp file เพราะ google SDK ต้องการ path
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            )
            tmp.write(creds_json)
            tmp.close()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
            return True
    except Exception:
        pass

    # fallback: ใช้ไฟล์ key ในโฟลเดอร์โปรเจค
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "scrap-ocr-key.json")
    if not os.path.isabs(key_path):
        key_path = str(Path(__file__).parent / key_path)
    if os.path.exists(key_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
        return True

    print("[OCR] ไม่พบ Google credentials — ตรวจสอบ scrap-ocr-key.json หรือ Streamlit secrets")
    return False


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """
    รับ bytes ของรูปภาพ คืนข้อความที่อ่านได้จากรูป
    คืน string ว่างถ้าอ่านไม่ได้หรือเกิด error
    """
    try:
        from google.cloud import vision

        _setup_credentials()

        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = client.text_detection(image=image)

        if response.error.message:
            print(f"[OCR] Google Vision error: {response.error.message}")
            return ""

        texts = response.text_annotations
        if texts:
            return texts[0].description  # full text block
        return ""

    except ImportError:
        print("[OCR] google-cloud-vision ยังไม่ได้ติดตั้ง — รัน: pip install google-cloud-vision")
        return ""
    except Exception as e:
        print(f"[OCR] Error: {e}")
        return ""


def extract_text_from_image_url(url: str) -> str:
    """
    ดาวน์โหลดรูปจาก URL แล้วส่งให้ OCR
    """
    import urllib.request
    try:
        with urllib.request.urlopen(url) as resp:
            image_bytes = resp.read()
        return extract_text_from_image_bytes(image_bytes)
    except Exception as e:
        print(f"[OCR] ดาวน์โหลดรูปไม่ได้: {e}")
        return ""


# ── ทดสอบ ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
        with open(img_path, "rb") as f:
            data = f.read()
        text = extract_text_from_image_bytes(data)
        print("=== OCR Result ===")
        print(text)
    else:
        print("วิธีใช้: python ocr.py <path_to_image>")
