@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  [ 뉴스 요약 챗봇 ] 서버를 시작합니다.
echo  브라우저에서 http://127.0.0.1:5000/news 를 열어주세요.
echo  종료하려면 이 창을 닫으세요.
echo.

python web_app.py

if errorlevel 1 (
  echo.
  echo  오류: python 이 설치되어 있는지, 이 폴더에서 pip install -r requirements.txt 를 실행했는지 확인하세요.
  pause
)
