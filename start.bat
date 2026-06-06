@echo off
chcp 65001 > nul
echo ============================================
echo   LINE Price Tracker - Startup
echo ============================================

cd /d "%~dp0"

REM ตรวจว่ามีไฟล์ .env
if not exist .env (
    echo [ERROR] ไม่พบไฟล์ .env
    echo กรุณาสร้างไฟล์ .env จาก .env.example แล้วใส่ Token
    pause
    exit /b 1
)

echo [1/3] Starting LINE Bot Webhook on port 5000...
start "LINE Webhook" cmd /k "cd /d "%~dp0" && python webhook.py"

timeout /t 2 > nul

echo [2/3] Starting ngrok tunnel...
start "ngrok" cmd /k "C:\Users\sanso\AppData\Local\ngrok\ngrok.exe http 5000"

timeout /t 3 > nul

echo [3/3] Starting Dashboard...
start "Dashboard" cmd /k "cd /d "%~dp0" && python -m streamlit run dashboard.py"

echo.
echo ============================================
echo  เปิดหน้าต่างแล้ว 3 หน้าต่าง:
echo   - LINE Webhook  (port 5000)
echo   - ngrok         (ดู URL ที่ต้องใส่ใน LINE Console)
echo   - Dashboard     (http://localhost:8501)
echo ============================================
echo.
echo คัดลอก URL จาก ngrok (https://xxxx.ngrok-free.app)
echo แล้วใส่ใน LINE Console:
echo   Messaging API → Webhook URL → https://xxxx.ngrok-free.app/webhook
echo ============================================
pause
