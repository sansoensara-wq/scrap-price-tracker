"""
ทดสอบ dashboard โดยไม่ต้องเชื่อม LINE Bot
รัน: python run_demo.py  แล้วเปิด http://localhost:8501
"""

from database import add_demo_data, init_db

if __name__ == "__main__":
    init_db()
    add_demo_data()
    print("Demo data loaded: 200 records")
    print("Run dashboard: streamlit run dashboard.py")
