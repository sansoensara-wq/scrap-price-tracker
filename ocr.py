"""
OCR Module — อ่านข้อความราคาเศษเหล็กจากรูปภาพด้วย Tesseract (ฟรี ไม่ต้องบัตร)
"""

import io


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """
    รับ bytes ของรูปภาพ คืนข้อความที่อ่านได้จากรูป
    คืน string ว่างถ้าอ่านไม่ได้หรือเกิด error
    """
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(image_bytes))
        # ภาษาไทย+อังกฤษ, PSM 6 = อ่านเป็น block ของข้อความ
        text = pytesseract.image_to_string(image, lang="tha+eng", config="--psm 6")
        print(f"[OCR] Tesseract อ่านได้: {len(text)} ตัวอักษร")
        return text.strip()

    except ImportError as e:
        print(f"[OCR] ขาด library: {e}")
        return ""
    except Exception as e:
        print(f"[OCR] Error: {e}")
        return ""


def extract_text_from_image_url(url: str) -> str:
    """ดาวน์โหลดรูปจาก URL แล้วส่งให้ OCR"""
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
        with open(sys.argv[1], "rb") as f:
            data = f.read()
        text = extract_text_from_image_bytes(data)
        print("=== OCR Result ===")
        print(text)
    else:
        print("วิธีใช้: python ocr.py <path_to_image>")
