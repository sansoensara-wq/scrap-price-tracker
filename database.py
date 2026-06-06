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
                price       REAL    NOT NULL,
                sender      TEXT,
                source_type TEXT,
                source_id   TEXT,
                raw_text    TEXT,
                recorded_at TEXT    NOT NULL
            )
        """)
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
            con.execute(
                """INSERT INTO prices
                   (company, price_date, category, price, sender, source_type, source_id, raw_text, recorded_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (e.company, e.price_date, e.category, e.price,
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
    """รายชื่อหมวดราคาทั้งหมด"""
    init_db()
    with _conn() as con:
        rows = con.execute(
            "SELECT DISTINCT category FROM prices ORDER BY category"
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
    """เพิ่มข้อมูลตัวอย่าง 90 วัน × ทุกหมวด"""
    from parser import PriceEntry
    init_db()
    base = datetime.now() - timedelta(days=90)
    entries = []
    prices = {k: v[1] for k, v in DEMO_CATEGORIES.items()}

    for day in range(90):
        ts = base + timedelta(days=day)
        company = random.choice(DEMO_COMPANIES)
        price_date = ts.strftime("%d/%m/%y")
        for key, (cat_name, _) in DEMO_CATEGORIES.items():
            prices[key] += random.uniform(-0.3, 0.3)
            prices[key] = round(max(5.0, min(15.0, prices[key])), 2)
            entries.append(PriceEntry(
                company=company,
                price_date=price_date,
                category=cat_name,
                price=prices[key],
                raw_text=f"{company} {price_date}\n{cat_name} {prices[key]}",
                sender="demo_user",
                source_id="demo_group",
                source_type="group",
            ))

    # บันทึกโดยตั้ง recorded_at ตามวัน
    init_db()
    with _conn() as con:
        base2 = datetime.now() - timedelta(days=90)
        idx = 0
        for day in range(90):
            ts = (base2 + timedelta(days=day)).strftime("%Y-%m-%d %H:%M:%S")
            for _ in DEMO_CATEGORIES:
                e = entries[idx]
                con.execute(
                    """INSERT INTO prices
                       (company, price_date, category, price, sender, source_type, source_id, raw_text, recorded_at)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (e.company, e.price_date, e.category, e.price,
                     e.sender, e.source_type, e.source_id, e.raw_text, ts),
                )
                idx += 1
