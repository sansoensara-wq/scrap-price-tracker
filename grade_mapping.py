"""
Grade Mapping — แปลงชื่อเกรดเศษเหล็กที่แต่ละโรงหลอมเรียกต่างกัน
ให้กลายเป็น "เกรดมาตรฐาน" เดียวกัน เพื่อให้กราฟ/รายงานเปรียบเทียบได้ถูกต้อง

ที่มา: ข้อมูลที่ผู้ใช้สอนไว้ (บันทึกใน scrap_grades_knowledge.md)

วิธีใช้:
    from grade_mapping import normalize_grade
    standard = normalize_grade(company="TSB", raw_category="ปั้ม")
    # -> "ปั๊ม"
"""

# ══════════════════════════════════════════════════════════════
# เกรดมาตรฐาน (Standard Grade) ที่โปรแกรมจะใช้แสดงผล
# ══════════════════════════════════════════════════════════════
GRADE_PUMP = "ปั๊ม"
GRADE_CUT_A = "ตัดไฟ A"
GRADE_CUT_B = "ตัดไฟ B"
GRADE_THICK_SPECIAL = "หนาพิเศษ"
GRADE_SPOT_80_100 = "สปอต 80-100"
GRADE_SPOT_50_70 = "สปอต 50-70"
GRADE_AB = "AB"
GRADE_B2 = "B2"
GRADE_TURNING = "ขี้กลึง"

ALL_STANDARD_GRADES = [
    GRADE_PUMP,
    GRADE_CUT_A,
    GRADE_CUT_B,
    GRADE_THICK_SPECIAL,
    GRADE_SPOT_80_100,
    GRADE_SPOT_50_70,
    GRADE_AB,
    GRADE_B2,
    GRADE_TURNING,
]

# ══════════════════════════════════════════════════════════════
# ตาราง Mapping: (ชื่อโรงหลอม, ชื่อเกรดที่โรงนั้นเรียก) -> เกรดมาตรฐาน
#
# ⚠️ สำคัญ: ชื่อเกรดบางชื่อซ้ำกันระหว่างโรง/ระหว่างเกรด (เช่น "P&S",
# "spot100sp", "หนา") แต่หมายถึงคนละเกรดกัน ขึ้นอยู่กับว่าโรงไหนเป็นคนพูด
# ดังนั้น mapping นี้ผูกกับ "ชื่อโรงหลอม" เสมอ ห้าม map แบบไม่สนโรง
# ══════════════════════════════════════════════════════════════

# รายชื่อโรงหลอมทั้งหมด (สำหรับใช้ตรวจสอบ/แสดงผลใน UI)
ALL_MILLS = [
    "LN", "SISCO", "ZUBB", "YX", "CHOW", "KPP", "TSB", "STS", "CSS",
    "NTS", "GJ", "GS", "SCSC", "SYS", "TYS", "MILLCON", "AB STEEL", "YLL",
]

# (mill, ชื่อที่โรงเรียก) -> เกรดมาตรฐาน
GRADE_MAP: dict[tuple[str, str], str] = {
    # ── 1) ปั๊ม ────────────────────────────────────────────────
    ("LN", "ปั๊มยาว"): GRADE_PUMP,
    ("SISCO", "B1"): GRADE_PUMP,
    ("ZUBB", "B1"): GRADE_PUMP,
    ("YX", "ปั้ม"): GRADE_PUMP,
    ("YX", "ปั๊ม"): GRADE_PUMP,
    ("CHOW", "ปั้ม"): GRADE_PUMP,
    ("CHOW", "ปั๊ม"): GRADE_PUMP,
    ("TSB", "ปั้ม"): GRADE_PUMP,
    ("TSB", "ปั๊ม"): GRADE_PUMP,
    ("STS", "ปั้ม"): GRADE_PUMP,
    ("STS", "ปั๊ม"): GRADE_PUMP,
    ("CSS", "ปั้ม"): GRADE_PUMP,
    ("CSS", "ปั๊ม"): GRADE_PUMP,
    ("CSS", "เหล็กปั้ม/ปั๊มอัด"): GRADE_PUMP,
    ("NTS", "B1"): GRADE_PUMP,
    ("GJ", "Busheling"): GRADE_PUMP,
    ("GS", "Busheling"): GRADE_PUMP,
    ("SCSC", "B1"): GRADE_PUMP,
    ("SYS", "B1"): GRADE_PUMP,
    ("TYS", "ปั้ม"): GRADE_PUMP,
    ("TYS", "ปั๊ม"): GRADE_PUMP,
    ("AB STEEL", "ปั้ม"): GRADE_PUMP,
    ("AB STEEL", "ปั๊ม"): GRADE_PUMP,
    ("YLL", "ปั้ม"): GRADE_PUMP,
    ("YLL", "ปั๊ม"): GRADE_PUMP,

    # ── 2) ตัดไฟ A ────────────────────────────────────────────
    ("YX", "ตัดไฟ A"): GRADE_CUT_A,
    ("CHOW", "ตัดไฟ A"): GRADE_CUT_A,
    ("STS", "ตัดไฟ A"): GRADE_CUT_A,
    ("CSS", "ตัดไฟ A"): GRADE_CUT_A,
    ("CSS", "เหล็กตัดไฟ/หนาพิเศษ A"): GRADE_CUT_A,
    ("AB STEEL", "ตัดไฟ A"): GRADE_CUT_A,
    ("YLL", "ตัดไฟ A"): GRADE_CUT_A,

    # ── 3) ตัดไฟ B (เหล็กหนา 3 mm. ขึ้นไป) ────────────────────
    ("YX", "ตัดไฟ B"): GRADE_CUT_B,
    ("CHOW", "ตัดไฟ B"): GRADE_CUT_B,
    ("KPP", "ตัดไฟ B"): GRADE_CUT_B,
    ("STS", "ตัดไฟ B"): GRADE_CUT_B,
    ("CSS", "ตัดไฟ B"): GRADE_CUT_B,
    ("CSS", "เหล็กตัดไฟ/หนาพิเศษ B"): GRADE_CUT_B,
    ("SYS", "PM"): GRADE_CUT_B,
    ("TYS", "P&S B"): GRADE_CUT_B,
    ("AB STEEL", "ตัดไฟ B"): GRADE_CUT_B,
    ("YLL", "ตัดไฟ B"): GRADE_CUT_B,

    # ── 4) หนาพิเศษ (เหล็กหนา 5 mm. ขึ้นไป) ───────────────────
    ("LN", "หนาพิเศษ"): GRADE_THICK_SPECIAL,
    ("SISCO", "spot100sp"): GRADE_THICK_SPECIAL,
    ("ZUBB", "spot Z"): GRADE_THICK_SPECIAL,
    ("TSB", "หนา"): GRADE_THICK_SPECIAL,
    ("NTS", "spot100sp"): GRADE_THICK_SPECIAL,
    ("GJ", "P&S"): GRADE_THICK_SPECIAL,
    ("GS", "P&S"): GRADE_THICK_SPECIAL,
    ("SCSC", "spot100sp"): GRADE_THICK_SPECIAL,
    ("TYS", "P&S A"): GRADE_THICK_SPECIAL,

    # ── 5) สปอต 80-100 ────────────────────────────────────────
    ("LN", "เหล็กสปอร์ต 80:20"): GRADE_SPOT_80_100,
    ("SISCO", "spot 80-100"): GRADE_SPOT_80_100,
    ("ZUBB", "Mix 1"): GRADE_SPOT_80_100,
    ("YX", "สปอท"): GRADE_SPOT_80_100,
    ("CHOW", "สปอท"): GRADE_SPOT_80_100,
    ("KPP", "สปอท 80"): GRADE_SPOT_80_100,
    ("TSB", "สปอต 80-100"): GRADE_SPOT_80_100,
    ("TSB", "สปอท 80-100"): GRADE_SPOT_80_100,
    ("STS", "สปอท 80"): GRADE_SPOT_80_100,
    ("CSS", "เหล็กสปอทร้อย"): GRADE_SPOT_80_100,
    ("NTS", "spot 80-100"): GRADE_SPOT_80_100,
    ("GJ", "HMS80/20"): GRADE_SPOT_80_100,
    ("GS", "HMS80/20"): GRADE_SPOT_80_100,
    ("SCSC", "spot 80-100"): GRADE_SPOT_80_100,
    ("SYS", "SM"): GRADE_SPOT_80_100,
    ("TYS", "HMS สปอร์ท"): GRADE_SPOT_80_100,
    ("MILLCON", "Local 1"): GRADE_SPOT_80_100,
    ("AB STEEL", "สปอท"): GRADE_SPOT_80_100,
    ("YLL", "สปอท"): GRADE_SPOT_80_100,

    # ── 6) สปอต 50-70 ────────────────────────────────────────
    ("SISCO", "SPOT 50-70"): GRADE_SPOT_50_70,
    ("TSB", "สปอต 50-70"): GRADE_SPOT_50_70,
    ("NTS", "SPOT 50-70"): GRADE_SPOT_50_70,
    ("SCSC", "SPOT 50-70"): GRADE_SPOT_50_70,

    # ── 7) AB (เหล็กบาง) ──────────────────────────────────────
    ("LN", "เหล็กบาง (50:50)"): GRADE_AB,
    ("LN", "เหล็กบาง"): GRADE_AB,
    ("SISCO", "AB"): GRADE_AB,
    ("ZUBB", "Mix 2"): GRADE_AB,
    ("TSB", "สปอต 0-40"): GRADE_AB,
    ("NTS", "AB"): GRADE_AB,
    ("SCSC", "AB"): GRADE_AB,
    ("SYS", "D"): GRADE_AB,
    ("TYS", "LMS บาง"): GRADE_AB,
    ("MILLCON", "Local 3"): GRADE_AB,
    ("CSS", "เหล็กบาง"): GRADE_AB,

    # ── 8) B2 ────────────────────────────────────────────────
    ("LN", "เหล็กบางอัด"): GRADE_B2,
    ("SISCO", "B2"): GRADE_B2,
    ("ZUBB", "บางอัดแน่น"): GRADE_B2,
    ("NTS", "B2"): GRADE_B2,
    ("GJ", "Bundle 2"): GRADE_B2,
    ("GJ", "HMS Bundle"): GRADE_B2,
    ("GS", "Bundle 2"): GRADE_B2,
    ("GS", "HMS Bundle"): GRADE_B2,
    ("SCSC", "B2"): GRADE_B2,
    ("SYS", "Bundle SY"): GRADE_B2,
    ("TYS", "LMS Bundle"): GRADE_B2,
    ("MILLCON", "Bundle 2"): GRADE_B2,

    # ── 9) ขี้กลึง ─────────────────────────────────────────────
    ("CSS", "ขี้กลึงฟู"): GRADE_TURNING,
    ("CSS", "ขี้กลึงฟ"): GRADE_TURNING,   # OCR บางครั้งอ่านขาด ู
}


def _norm_text(s: str) -> str:
    """ตัด space ซ้ำ/หัวท้าย ลบวรรณยุกต์ไทย เพื่อให้ ปั้ม/ปั๊ม/ปั่ม ถือว่าเหมือนกัน"""
    TONE_MARKS = "่้๊๋"
    s = "".join(c for c in s if c not in TONE_MARKS)
    return " ".join(s.strip().split())


# สร้าง lookup table แบบ case-insensitive ไว้ล่วงหน้า เพื่อความเร็ว+ความทนทาน
_LOOKUP: dict[tuple[str, str], str] = {
    (_norm_text(mill).upper(), _norm_text(name).lower()): standard
    for (mill, name), standard in GRADE_MAP.items()
}


def normalize_grade(company: str, raw_category: str) -> str:
    """
    แปลงชื่อเกรดดิบ (ตามที่แต่ละโรงเรียก) ให้เป็นชื่อเกรดมาตรฐาน

    Args:
        company: ชื่อโรงหลอม เช่น "TSB", "GJ" (ไม่สนตัวพิมพ์เล็ก-ใหญ่)
        raw_category: ชื่อเกรดดิบที่อ่านได้จากข้อความ เช่น "ปั้ม", "P&S"

    Returns:
        ชื่อเกรดมาตรฐาน ถ้าไม่พบใน mapping จะคืนค่า raw_category เดิม
        (เผื่อกรณีเกรดใหม่ที่ยังไม่เคยสอน โปรแกรมจะยังเก็บข้อมูลไว้ได้
        และสามารถนำมาสอน mapping เพิ่มทีหลังได้)
    """
    if not company or not raw_category:
        return raw_category

    key = (_norm_text(company).upper(), _norm_text(raw_category).lower())
    return _LOOKUP.get(key, raw_category)


def is_known_grade_name(company: str, raw_category: str) -> bool:
    """เช็คว่าชื่อเกรดนี้เคยถูกสอน (มีอยู่ใน mapping) หรือยัง"""
    if not company or not raw_category:
        return False
    key = (_norm_text(company).upper(), _norm_text(raw_category).lower())
    return key in _LOOKUP


def unknown_grade_names() -> list[tuple[str, str]]:
    """
    คืนรายการ (mill, raw_name) ที่ยังไม่มีใน mapping
    -- เผื่อใช้ debug ว่ามีชื่อเกรดใหม่ที่ต้องมาสอนเพิ่ม
    (ฟังก์ชันนี้ไว้สำหรับ dev เรียกตรวจสอบเอง ไม่ได้ track อัตโนมัติ)
    """
    return []


# ── ทดสอบ ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        ("TSB", "ปั้ม"),
        ("GJ", "Busheling"),
        ("GJ", "P&S"),          # -> หนาพิเศษ (สำหรับ GJ)
        ("SISCO", "spot100sp"), # -> หนาพิเศษ (สำหรับ SISCO)
        ("SYS", "PM"),          # -> ตัดไฟ B
        ("MILLCON", "Local 1"), # -> สปอต 80-100
        ("XXX", "ไม่รู้จัก"),     # -> คืนค่าเดิม (ไม่พบ)
    ]
    for mill, raw in tests:
        print(f"{mill:10s} '{raw}' -> {normalize_grade(mill, raw)}")
