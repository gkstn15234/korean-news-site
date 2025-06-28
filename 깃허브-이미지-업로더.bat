@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================
echo 📸 깃허브 이미지 업로더 시작
echo ==============================================
echo.

echo 📦 필요한 패키지 설치 확인...
pip install -r requirements.txt

echo.
echo 🚀 이미지 업로더 실행...
python github_image_uploader.py

echo.
echo 프로그램이 종료되었습니다.
pause 