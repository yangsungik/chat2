@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo  서버를 시작하고 브라우저를 엽니다...
start "뉴스 챗봇 서버" cmd /k "cd /d ""%~dp0"" && python web_app.py"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:5000/news"
exit
