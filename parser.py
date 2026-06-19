"""
Parser สำหรับข้อความราคาเศษเหล็กจาก LINE group
รูปแบบที่รองรับ:

TSB เหล็กกล้า  27/05/69

ปั้ม                           10.80
หนา                         10.16
สปอต 80-100         9.95
สปอต 50-70           9.27
สปอต 0-40             7.58
บาง                          7.05
"""

import re
from dataclasses import dataclass, field
from datetime import datetime

from grade_mapping import normalize_grade, is_known_grade_name


@dataclass
class PriceEntry:
    company: str
    price_date: str          # วันที่ในข้อความ เช่น "27/05/69"
    category: str            # ชื่อเกรดดิบตามที่โรงเรียก เช่น "ปั้ม", "P&S"
    price: float
    raw_text: str
    sender: str
    source_id: str
    source_type: str
    grade: str = field(default="")   # เกรดมาตรฐาน (normalize แล้ว) เช่น "ปั๊ม"

    def __post_init__(self):
        if not self.grade:
            self.grade = normalize_grade(self.company, self.category)


# Regex จับ: ตัวเลขท้ายบรรทัด (ราคา)
PRICE_LINE_RE = re.compile(
    r"^(.+?)\s{2,}([\d]+(?:\.[\d]{1,2})?)\s*$"
)

# Regex จับวันที่ในรูปแบบ dd/mm/yy หรือ dd/mm/yyyy
DATE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b")


def parse_price_message(
    text: str,
    sender: str = "unknown",
    source_id: str = "",
    source_type: str = "group",
) -> list[PriceEntry]:
    """
    แยกข้อความราคาเศษเหล็กออกเป็น PriceEntry ทีละหมวด
    คืนค่า list ว่างถ้าข้อความไม่ใช่ราคา
    """
    lines = text.strip().splitlines()
    if not lines:
        return []

    # ── หาบรรทัดแรกที่เป็น header (มีชื่อบริษัท + วันที่) ─────────────
    company = ""
    price_date = ""
    header_idx = 0

    for i, line in enumerate(lines):
        date_match = DATE_RE.search(line)
        if date_match:
            price_date = date_match.group(1)
            # ชื่อบริษัทคือส่วนหน้าวันที่ ตัด whitespace
            company = line[: date_match.start()].strip()
            header_idx = i
            break

    # ถ้าไม่มีวันที่เลยในข้อความ ลองตีความว่าเป็น quick-price
    # เช่น "ปั้ม 10.80" บรรทัดเดียว
    if not price_date:
        return _parse_quick(text, sender, source_id, source_type)

    # ถ้าบรรทัดวันที่ไม่มีชื่อบริษัทนำหน้า (เช่น "ราคาเริ่มวันที่ 10/6/2026")
    # ให้ใช้บรรทัดก่อนหน้าเป็นชื่อบริษัท (ถ้ามีและไม่มีตัวเลข)
    if "วันที่" in company:
        company = ""
    if not company and header_idx > 0:
        prev_line = lines[header_idx - 1].strip()
        if prev_line and not re.search(r"\d", prev_line):
            company = prev_line

    # ── วนอ่านบรรทัดที่เหลือหาหมวดราคา ────────────────────────────────
    entries: list[PriceEntry] = []
    skip_words = {"เกรด", "ราคา"}
    remaining = [ln.strip() for ln in lines[header_idx + 1:] if ln.strip()]

    i = 0
    while i < len(remaining):
        line = remaining[i]

        # รูปแบบเดิม: "ชื่อเกรด    ราคา" บรรทัดเดียว
        match = PRICE_LINE_RE.match(line)
        if match:
            category = match.group(1).strip()
            price = float(match.group(2))
            entries.append(
                PriceEntry(
                    company=company,
                    price_date=price_date,
                    category=category,
                    price=price,
                    raw_text=text,
                    sender=sender,
                    source_id=source_id,
                    source_type=source_type,
                )
            )
            i += 1
            continue

        # รูปแบบใหม่: บรรทัดชื่อเกรด แล้วบรรทัดถัดไปเป็นราคา
        if line in skip_words:
            i += 1
            continue

        is_number = re.fullmatch(r"[\d]+(?:\.[\d]{1,2})?", line)
        if not is_number and i + 1 < len(remaining):
            next_line = remaining[i + 1]
            num_match = re.fullmatch(r"([\d]+(?:\.[\d]{1,2})?)", next_line)
            if num_match:
                entries.append(
                    PriceEntry(
                        company=company,
                        price_date=price_date,
                        category=line,
                        price=float(num_match.group(1)),
                        raw_text=text,
                        sender=sender,
                        source_id=source_id,
                        source_type=source_type,
                    )
                )
                i += 2
                continue

        i += 1

    # ── เก็บเฉพาะเกรดที่เคยสอน mapping ไว้แล้วเท่านั้น ──────────────
    for e in entries:
        known = is_known_grade_name(e.company, e.category)
        print(f"[PARSER] company={repr(e.company)} category={repr(e.category)} known={known}")
    entries = [e for e in entries if is_known_grade_name(e.company, e.category)]

    return entries


def _parse_quick(
    text: str, sender: str, source_id: str, source_type: str
) -> list[PriceEntry]:
    """
    Fallback: รองรับข้อความสั้น เช่น
      ปั้ม 10.80
      หนา 10.16
    หรือ
      ราคา 10.80
    """
    entries = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # ลองจับ "label price" ก่อน
        m = re.match(r"^(.+?)\s+([\d]+(?:\.[\d]{1,2})?)\s*$", line)
        if m:
            entries.append(
                PriceEntry(
                    company="",
                    price_date="",
                    category=m.group(1).strip(),
                    price=float(m.group(2)),
                    raw_text=text,
                    sender=sender,
                    source_id=source_id,
                    source_type=source_type,
                )
            )
        else:
            # ตัวเลขเดี่ยว
            m2 = re.match(r"^([\d]+(?:\.[\d]{1,2})?)$", line)
            if m2:
                entries.append(
                    PriceEntry(
                        company="",
                        price_date="",
                        category="ราคา",
                        price=float(m2.group(1)),
                        raw_text=text,
                        sender=sender,
                        source_id=source_id,
                        source_type=source_type,
                    )
                )
    return entries


# ── ทดสอบ ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = """TSB เหล็กกล้า  27/05/69

ปั้ม                           10.80
หนา                         10.16
สปอต 80-100         9.95
สปอต 50-70           9.27
สปอต 0-40             7.58
บาง                          7.05"""

    results = parse_price_message(sample, sender="test_user")
    for e in results:
        print(f"[{e.company}] [{e.price_date}] {e.category}: {e.price}")
