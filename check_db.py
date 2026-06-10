from database import init_db, get_price_history
init_db()
rows = get_price_history(limit=10)
if rows:
    for r in rows[-5:]:
        print(r['recorded_at'], "|", r['company'], "|", r['category'], "|", r['grade'], "|", r['price'])
else:
    print("ไม่มีข้อมูลในฐานข้อมูล")
