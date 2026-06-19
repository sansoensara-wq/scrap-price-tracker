"""
OCR Module — อ่านข้อความราคาเศษเหล็กจากรูปภาพด้วย Tesseract (ฟรี ไม่ต้องบัตร)
"""

import io


def _preprocess(image):
    """ขยายรูปและแปลงเป็น grayscale เพื่อให้ Tesseract อ่านตารางได้ดีขึ้น"""
    from PIL import ImageOps, ImageFilter
    # ขยาย 2x ให้ตัวอักษรใหญ่ขึ้น
    w, h = image.size
    image = image.resize((w * 2, h * 2))
    # แปลงเป็น grayscale
    image = ImageOps.grayscale(image)
    # เพิ่มความคมชัด
    image = image.filter(ImageFilter.SHARPEN)
    return image


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(image_bytes))
        image = _preprocess(image)

        # PSM 6 = uniform block, เหมาะกับตารางราคา
        text = pytesseract.image_to_string(
            image, lang="tha+eng", config="--psm 6"
        )
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
