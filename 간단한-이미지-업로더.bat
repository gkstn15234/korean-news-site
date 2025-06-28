@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================
echo GitHub 이미지 업로더 (간단 버전)
echo ==============================================
echo.

echo 패키지 설치 확인...
pip install requests pyperclip

echo.
echo 프로그램 실행...
python simple_github_uploader.py

echo.
echo 프로그램이 종료되었습니다.
pause 