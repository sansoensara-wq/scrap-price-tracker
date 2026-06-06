# LINE Price Tracker 📈

รับราคาจาก LINE group → เก็บข้อมูล → แสดง Dashboard + แจ้งเตือน

## โครงสร้างไฟล์

```
line-price-tracker/
├── webhook.py      ← LINE Bot รับข้อความ
├── database.py     ← SQLite บันทึก/ดึงข้อมูล
├── notifier.py     ← ส่งแจ้งเตือนกลับ LINE
├── dashboard.py    ← Streamlit Dashboard
├── run_demo.py     ← ทดสอบโดยไม่ต้องเชื่อม LINE
└── requirements.txt
```

## วิธีติดตั้ง

```bash
cd line-price-tracker
pip install -r requirements.txt
```

## วิธีทดสอบ (ไม่ต้องมี LINE Bot)

```bash
python run_demo.py
streamlit run dashboard.py
```

เปิด http://localhost:8501

## วิธีเชื่อม LINE Bot จริง

### 1. สร้าง LINE Bot
1. ไปที่ https://developers.line.biz/
2. สร้าง Provider → สร้าง Messaging API channel
3. คัดลอก **Channel Access Token** และ **Channel Secret**

### 2. ตั้งค่า .env
```bash
cp .env.example .env
# แก้ไขค่าใน .env
```

### 3. รัน Webhook Server
```bash
# ใส่ environment variables
set LINE_CHANNEL_ACCESS_TOKEN=xxx
set LINE_CHANNEL_SECRET=xxx

python webhook.py
```

### 4. Expose localhost ด้วย ngrok (สำหรับทดสอบ)
```bash
ngrok http 5000
# คัดลอก URL เช่น https://xxxx.ngrok.io/webhook
# ใส่ใน LINE Developers Console → Webhook URL
```

### 5. รัน Dashboard
```bash
streamlit run dashboard.py
```

## รูปแบบข้อความที่รองรับ

| ข้อความ | ราคาที่จับได้ |
|---------|-------------|
| `ราคา 1500` | 1500 |
| `1500 บาท` | 1500 |
| `gold 1523.50` | 1523.50 |
| `ทอง 1480` | 1480 |
| `1600` | 1600 |

## ฟีเจอร์ Dashboard

- **ราคาปัจจุบัน** พร้อม % เปลี่ยนแปลง
- **กราฟ Line Chart** ราคาย้อนหลัง + เส้น alert threshold
- **กราฟ Candlestick** (OHLC รายชั่วโมง)
- **Histogram** การกระจายตัวของราคา
- **จัดการ Alert** ตั้ง threshold แจ้งเตือนสูง/ต่ำ
