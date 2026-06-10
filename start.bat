@echo off
chcp 65001 > nul
echo ============================================
echo   LINE Price Tracker - Startup
echo ============================================

cd /d "%~dp0"

if not exist .env (
    echo [ERROR] ไม่พบไฟล์ .env
    pause
    exit /b 1
)

echo [1/2] Starting LINE Bot Webhook on port 5000...
start "LINE Webhook" cmd /k "cd /d "%~dp0" && python webhook.py"

timeout /t 2 > nul

echo [2/2] Starting Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "%USERPROFILE%\cloudflared.exe tunnel --url http://localhost:5000"

echo.
echo ============================================
echo  เปิดหน้าต่างแล้ว 2 หน้าต่าง:
echo   - LINE Webhook  (port 5000)
echo   - Cloudflare Tunnel (ดู URL ในหน้าต่าง Cloudflare)
echo ============================================
echo.
echo รอ Cloudflare สักครู่ จะเห็น URL แบบ:
echo   https://xxxx.trycloudflare.com
echo.
echo คัดลอก URL นั้นแล้วใส่ใน LINE Console:
echo   Messaging API - Webhook URL:
echo   https://xxxx.trycloudflare.com/webhook
echo ============================================
pause
