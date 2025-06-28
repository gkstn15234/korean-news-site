@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo 🤖 AI 뉴스 기사 생성기
echo ==================================================
echo 📸 이미지 업로드 → GitHub
echo 🤖 Gemini AI → 이미지 분석 → 기사 생성  
echo 📰 Hugo 마크다운 → 자동 저장
echo ==================================================
echo.

echo 📦 필요한 패키지 설치 확인...
pip install google-generativeai pyyaml

echo.
echo 🚀 AI 뉴스 생성기 실행...
python ai_news_generator.py

echo.
echo 프로그램이 종료되었습니다.
pause 