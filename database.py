"""
Database layer — รองรับทั้ง PostgreSQL (Render) และ SQLite (local)
ถ้ามี environment variable DATABASE_URL จะใช้ PostgreSQL อัตโนมัติ
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
import random

DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_PG = bool(DATABASE_URL)

# ── SQLite (local) ────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent / "prices.db"


def _conn():
    if USE_PG:
        import psycopg2
        import psycopg2.extras
        con = psycopg2.connect(DATABASE_URL)
        return con
    else:
        import sqlite3
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        return con


def _placeholder():
    """เครื่องหมาย placeholder ใน SQL"""
    return "%s" if USE_PG else "?"


def _rows_to_dicts(rows, cursor=None):
    """แปลง rows เป็น list[dict]"""
    if USE_PG:
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in rows]
    else:
        return [dict(r) for r in rows]


def init_db():
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    id          SERIAL PRIMARY KEY,
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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id          SERIAL PRIMARY KEY,
                    label       TEXT    NOT NULL,
                    category    TEXT    NOT NULL DEFAULT '',
                    threshold   REAL    NOT NULL,
                    direction   TEXT    NOT NULL CHECK(direction IN ('above','below')),
                    active      INTEGER NOT NULL DEFAULT 1
                )
            """)
            con.commit()
        else:
            import sqlite3
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
            con.commit()
    finally:
        con.close()


def save_prices(entries: list):
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ph = _placeholder()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            for e in entries:
                grade = getattr(e, "grade", "") or e.category
                cur.execute(
                    f"""INSERT INTO prices
                       (company, price_date, category, grade, price, sender, source_type, source_id, raw_text, recorded_at)
                       VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
                    (e.company, e.price_date, e.category, grade, e.price,
                     e.sender, e.source_type, e.source_id, e.raw_text, now),
                )
            con.commit()
        else:
            for e in entries:
                grade = getattr(e, "grade", "") or e.category
                con.execute(
                    f"""INSERT INTO prices
                       (company, price_date, category, grade, price, sender, source_type, source_id, raw_text, recorded_at)
                       VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
                    (e.company, e.price_date, e.category, grade, e.price,
                     e.sender, e.source_type, e.source_id, e.raw_text, now),
                )
            con.commit()
    finally:
        con.close()


def get_latest_prices() -> list[dict]:
    init_db()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            cur.execute("""
                SELECT p.*
                FROM prices p
                INNER JOIN (
                    SELECT category, MAX(recorded_at) AS max_ts
                    FROM prices GROUP BY category
                ) latest ON p.category = latest.category AND p.recorded_at = latest.max_ts
                ORDER BY p.category
            """)
            return _rows_to_dicts(cur.fetchall(), cur)
        else:
            rows = con.execute("""
                SELECT p.*
                FROM prices p
                INNER JOIN (
                    SELECT category, MAX(recorded_at) AS max_ts
                    FROM prices GROUP BY category
                ) latest ON p.category = latest.category AND p.recorded_at = latest.max_ts
                ORDER BY p.category
            """).fetchall()
            return _rows_to_dicts(rows)
    finally:
        con.close()


def get_price_history(category: str | None = None, limit: int = 1000) -> list[dict]:
    init_db()
    ph = _placeholder()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            if category:
                cur.execute(
                    f"SELECT * FROM prices WHERE category={ph} ORDER BY recorded_at DESC LIMIT {ph}",
                    (category, limit),
                )
            else:
                cur.execute(
                    f"SELECT * FROM prices ORDER BY recorded_at DESC LIMIT {ph}",
                    (limit,),
                )
            rows = cur.fetchall()
            return list(reversed(_rows_to_dicts(rows, cur)))
        else:
            if category:
                rows = con.execute(
                    f"SELECT * FROM prices WHERE category={ph} ORDER BY recorded_at DESC LIMIT {ph}",
                    (category, limit),
                ).fetchall()
            else:
                rows = con.execute(
                    f"SELECT * FROM prices ORDER BY recorded_at DESC LIMIT {ph}",
                    (limit,),
                ).fetchall()
            return list(reversed(_rows_to_dicts(rows)))
    finally:
        con.close()


def get_categories() -> list[str]:
    init_db()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            cur.execute("SELECT DISTINCT category FROM prices ORDER BY category")
            return [r[0] for r in cur.fetchall()]
        else:
            rows = con.execute(
                "SELECT DISTINCT category FROM prices ORDER BY category"
            ).fetchall()
            return [r[0] for r in rows]
    finally:
        con.close()


def get_grades() -> list[str]:
    init_db()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            cur.execute("SELECT DISTINCT grade FROM prices WHERE grade != '' ORDER BY grade")
            return [r[0] for r in cur.fetchall()]
        else:
            rows = con.execute(
                "SELECT DISTINCT grade FROM prices WHERE grade != '' ORDER BY grade"
            ).fetchall()
            return [r[0] for r in rows]
    finally:
        con.close()


def get_companies() -> list[str]:
    init_db()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            cur.execute("SELECT DISTINCT company FROM prices WHERE company != '' ORDER BY company")
            return [r[0] for r in cur.fetchall()]
        else:
            rows = con.execute(
                "SELECT DISTINCT company FROM prices WHERE company != '' ORDER BY company"
            ).fetchall()
            return [r[0] for r in rows]
    finally:
        con.close()


# ── Alerts ───────────────────────────────────────────────────────────

def get_alerts() -> list[dict]:
    init_db()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            cur.execute("SELECT * FROM alerts")
            return _rows_to_dicts(cur.fetchall(), cur)
        else:
            rows = con.execute("SELECT * FROM alerts").fetchall()
            return _rows_to_dicts(rows)
    finally:
        con.close()


def add_alert(label: str, category: str, threshold: float, direction: str):
    init_db()
    ph = _placeholder()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            cur.execute(
                f"INSERT INTO alerts (label, category, threshold, direction) VALUES ({ph},{ph},{ph},{ph})",
                (label, category, threshold, direction),
            )
            con.commit()
        else:
            con.execute(
                f"INSERT INTO alerts (label, category, threshold, direction) VALUES ({ph},{ph},{ph},{ph})",
                (label, category, threshold, direction),
            )
            con.commit()
    finally:
        con.close()


def delete_alert(alert_id: int):
    ph = _placeholder()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            cur.execute(f"DELETE FROM alerts WHERE id={ph}", (alert_id,))
            con.commit()
        else:
            con.execute(f"DELETE FROM alerts WHERE id={ph}", (alert_id,))
            con.commit()
    finally:
        con.close()


def toggle_alert(alert_id: int, active: bool):
    ph = _placeholder()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            cur.execute(f"UPDATE alerts SET active={ph} WHERE id={ph}", (int(active), alert_id))
            con.commit()
        else:
            con.execute(f"UPDATE alerts SET active={ph} WHERE id={ph}", (int(active), alert_id))
            con.commit()
    finally:
        con.close()


# ── Demo data ────────────────────────────────────────────────────────

def add_demo_data():
    from parser import PriceEntry
    from grade_mapping import GRADE_MAP

    init_db()
    base = datetime.now() - timedelta(days=90)

    sample_pairs = [
        ("TSB", "ปั้ม"), ("TSB", "หนา"), ("TSB", "สปอต 80-100"),
        ("GJ", "Busheling"), ("GJ", "P&S"), ("GJ", "HMS80/20"),
        ("SISCO", "B1"), ("SISCO", "spot100sp"), ("SISCO", "AB"),
        ("YX", "ปั้ม"), ("YX", "ตัดไฟ A"), ("YX", "ตัดไฟ B"),
    ]
    sample_pairs = [(m, c) for m, c in sample_pairs if (m, c) in GRADE_MAP]
    base_prices = {pair: random.uniform(7.0, 12.0) for pair in sample_pairs}

    entries_with_ts = []
    for day in range(90):
        ts = (base + timedelta(days=day))
        price_date = ts.strftime("%d/%m/%y")
        recorded_at = ts.strftime("%Y-%m-%d %H:%M:%S")
        for pair in sample_pairs:
            company, raw_cat = pair
            base_prices[pair] += random.uniform(-0.25, 0.25)
            base_prices[pair] = round(max(5.0, min(15.0, base_prices[pair])), 2)
            entry = PriceEntry(
                company=company, price_date=price_date, category=raw_cat,
                price=base_prices[pair],
                raw_text=f"{company}  {price_date}\n\n{raw_cat}   {base_prices[pair]}",
                sender="demo_user", source_id="demo_group", source_type="group",
            )
            entries_with_ts.append((entry, recorded_at))

    ph = _placeholder()
    con = _conn()
    try:
        if USE_PG:
            cur = con.cursor()
            for e, ts in entries_with_ts:
                cur.execute(
                    f"""INSERT INTO prices
                       (company, price_date, category, grade, price, sender, source_type, source_id, raw_text, recorded_at)
                       VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
                    (e.company, e.price_date, e.category, e.grade, e.price,
                     e.sender, e.source_type, e.source_id, e.raw_text, ts),
                )
            con.commit()
        else:
            for e, ts in entries_with_ts:
                con.execute(
                    f"""INSERT INTO prices
                       (company, price_date, category, grade, price, sender, source_type, source_id, raw_text, recorded_at)
                       VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
                    (e.company, e.price_date, e.category, e.grade, e.price,
                     e.sender, e.source_type, e.source_id, e.raw_text, ts),
                )
            con.commit()
    finally:
        con.close()
