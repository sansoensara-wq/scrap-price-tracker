"""
SQLite database layer — บันทึกและดึงข้อมูลราคาเศษเหล็ก
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import random

DB_PATH = Path(__file__).parent / "prices.db"


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                company     TEXT,
                price_date  TEXT,
                category    TEXT    NOT NULL,
                grade       TEXT    NOT NULL DEFAULT '',
                price       REAL    NOT NULL,
                sender      TEXT,
                source_type TEXT,
                source_id   TEXT,
                raw_text    TEXT,
                recorded_at TEXT    NOT NULL
            )
        """)
        # migration: เพิ่มคอลัมน์ grade ถ้าฐานข้อมูลเก่ายังไม่มี
        cols = [r[1] for r in con.execute("PRAGMA table_info(prices)").fetchall()]
        if "grade" not in cols:
            con.execute("ALTER TABLE prices ADD COLUMN grade TEXT NOT NULL DEFAULT ''")
        con.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                label       TEXT    NOT NULL,
                category    TEXT    NOT NULL DEFAULT '',
                threshold   REAL    NOT NULL,
                direction   TEXT    NOT NULL CHECK(direction IN ('above','below')),
                active      INTEGER NOT NULL DEFAULT 1
            )
        """)


def save_prices(entries: list):
    """บันทึก list[PriceEntry] ลง DB"""
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as con:
        for e in entries:
            grade = getattr(e, "grade", "") or e.category
            con.execute(
                """INSERT INTO prices
                   (company, price_date, category, grade, price, sender, source_type, source_id, raw_text, recorded_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (e.company, e.price_date, e.category, grade, e.price,
                 e.sender, e.source_type, e.source_id, e.raw_text, now),
            )


def get_latest_prices() -> list[dict]:
    """ดึงราคาล่าสุดแยกตามหมวด (1 แถวต่อหมวด)"""
    init_db()
    with _conn() as con:
        rows = con.execute("""
            SELECT p.*
            FROM prices p
            INNER JOIN (
                SELECT category, MAX(recorded_at) AS max_ts
                FROM prices GROUP BY category
            ) latest ON p.category = latest.category AND p.recorded_at = latest.max_ts
            ORDER BY p.category
        """).fetchall()
    return [dict(r) for r in rows]


def get_price_history(category: str | None = None, limit: int = 1000) -> list[dict]:
    """ดึงประวัติราคา ถ้าระบุ category จะกรองเฉพาะหมวดนั้น"""
    init_db()
    with _conn() as con:
        if category:
            rows = con.execute(
                "SELECT * FROM prices WHERE category=? ORDER BY recorded_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM prices ORDER BY recorded_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in reversed(rows)]


def get_categories() -> list[str]:
    """รายชื่อหมวดราคาทั้งหมด (ชื่อดิบตามที่แต่ละโรงเรียก)"""
    init_db()
    with _conn() as con:
        rows = con.execute(
            "SELECT DISTINCT category FROM prices ORDER BY category"
        ).fetchall()
    return [r[0] for r in rows]


def get_grades() -> list[str]:
    """รายชื่อเกรดมาตรฐาน (normalize แล้ว) ทั้งหมด — ใช้สำหรับกราฟ/ตัวกรอง"""
    init_db()
    with _conn() as con:
        rows = con.execute(
            "SELECT DISTINCT grade FROM prices WHERE grade != '' ORDER BY grade"
        ).fetchall()
    return [r[0] for r in rows]


def get_companies() -> list[str]:
    """รายชื่อบริษัท/แหล่งที่มาทั้งหมด"""
    init_db()
    with _conn() as con:
        rows = con.execute(
            "SELECT DISTINCT company FROM prices WHERE company != '' ORDER BY company"
        ).fetchall()
    return [r[0] for r in rows]


# ── Alerts ───────────────────────────────────────────────────────────

def get_alerts() -> list[dict]:
    init_db()
    with _conn() as con:
        rows = con.execute("SELECT * FROM alerts").fetchall()
    return [dict(r) for r in rows]


def add_alert(label: str, category: str, threshold: float, direction: str):
    init_db()
    with _conn() as con:
        con.execute(
            "INSERT INTO alerts (label, category, threshold, direction) VALUES (?,?,?,?)",
            (label, category, threshold, direction),
        )


def delete_alert(alert_id: int):
    with _conn() as con:
        con.execute("DELETE FROM alerts WHERE id=?", (alert_id,))


def toggle_alert(alert_id: int, active: bool):
    with _conn() as con:
        con.execute("UPDATE alerts SET active=? WHERE id=?", (int(active), alert_id))


# ── Demo data ────────────────────────────────────────────────────────

DEMO_CATEGORIES = {
    "pump":        ("ปั้ม",          11.0),
    "thick":       ("หนา",          10.5),
    "spot_80_100": ("สปอต 80-100",  10.0),
    "spot_50_70":  ("สปอต 50-70",    9.3),
    "spot_0_40":   ("สปอต 0-40",     7.6),
    "thin":        ("บาง",           7.1),
}

DEMO_COMPANIES = ["TSB เหล็กกล้า", "SS Steel", "มิตรเหล็ก"]


def add_demo_data():
    """
    เพิ่มข้อมูลตัวอย่าง 90 วัน — จำลองว่าหลายโรงหลอม (บริษัท) ส่งราคามา
    โดยแต่ละโรงเรียกชื่อเกรดต่างกัน แล้วใช้ grade_mapping แปลงให้เป็นเกรดมาตรฐาน
    เพื่อโชว์ว่าระบบ Grade Mapping ทำงานถูกต้อง
    """
    from parser import PriceEntry
    from grade_mapping import GRADE_MAP

    init_db()
    base = datetime.now() - timedelta(days=90)

    # ใช้ข้อมูลจริงจาก GRADE_MAP: เลือกบางโรง x ชื่อเกรดดิบที่โรงนั้นใช้
    sample_pairs = [
        ("TSB", "ปั้ม"), ("TSB", "หนา"), ("TSB", "สปอต 80-100"),
        ("GJ", "Busheling"), ("GJ", "P&S"), ("GJ", "HMS80/20"),
        ("SISCO", "B1"), ("SISCO", "spot100sp"), ("SISCO", "AB"),
        ("YX", "ปั้ม"), ("YX", "ตัดไฟ A"), ("YX", "ตัดไฟ B"),
    ]
    # กรองเอาเฉพาะคู่ที่มีอยู่จริงใน mapping
    sample_pairs = [(m, c) for m, c in sample_pairs if (m, c) in GRADE_MAP]

    base_prices = {pair: random.uniform(7.0, 12.0) for pair in sample_pairs}

    rows = []
    for day in range(90):
        ts = (base + timedelta(days=day))
        price_date = ts.strftime("%d/%m/%y")
        recorded_at = ts.strftime("%Y-%m-%d %H:%M:%S")
        for pair in sample_pairs:
            company, raw_cat = pair
            base_prices[pair] += random.uniform(-0.25, 0.25)
            base_prices[pair] = round(max(5.0, min(15.0, base_prices[pair])), 2)
            price = base_prices[pair]
            entry = PriceEntry(
                company=company,
                price_date=price_date,
                category=raw_cat,
                price=price,
                raw_text=f"{company}  {price_date}\n\n{raw_cat}   {price}",
                sender="demo_user",
                source_id="demo_group",
                source_type="group",
            )
            rows.append((entry, recorded_at))

    with _conn() as con:
        for e, ts in rows:
            con.execute(
                """INSERT INTO prices
                   (company, price_date, category, grade, price, sender, source_type, source_id, raw_text, recorded_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (e.company, e.price_date, e.category, e.grade, e.price,
                 e.sender, e.source_type, e.source_id, e.raw_text, ts),
            )
