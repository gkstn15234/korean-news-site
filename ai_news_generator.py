#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 뉴스 기사 생성기
이미지 업로드 → GitHub + Gemini AI 기사 생성 → Hugo 마크다운 저장
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
import base64
import json
import os
from datetime import datetime
import pyperclip
import traceback
import yaml
import random
import re
import google.generativeai as genai
from PIL import Image

class AINewsGenerator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 AI 뉴스 기사 생성기")
        self.root.geometry("800x900")
        
        # 설정 변수들
        self.github_token = tk.StringVar()
        self.github_username = tk.StringVar()
        self.github_repo = tk.StringVar()
        self.gemini_api_key = tk.StringVar()
        self.selected_category = tk.StringVar()
        
        self.config_file = "ai_news_config.json"
        self.categories = []
        
        self.create_widgets()
        self.load_config()
        self.load_categories()
        
    def create_widgets(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = tk.Frame(self.root, padx=15, pady=15)
        main_frame.pack(fill='both', expand=True)
        
        # 제목
        title_label = tk.Label(main_frame, text="🤖 AI 뉴스 기사 생성기", 
                              font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 설정 탭
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # === 설정 탭 ===
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="⚙️ 설정")
        
        # GitHub 설정
        github_frame = tk.LabelFrame(config_frame, text="GitHub 설정", padx=10, pady=10)
        github_frame.pack(fill='x', pady=5)
        
        tk.Label(github_frame, text="GitHub Token:").pack(anchor='w')
        tk.Entry(github_frame, textvariable=self.github_token, show="*", width=70).pack(fill='x', pady=(0, 5))
        
        tk.Label(github_frame, text="사용자명:").pack(anchor='w')
        tk.Entry(github_frame, textvariable=self.github_username, width=30).pack(anchor='w', pady=(0, 5))
        
        tk.Label(github_frame, text="리포지토리:").pack(anchor='w')
        tk.Entry(github_frame, textvariable=self.github_repo, width=30).pack(anchor='w', pady=(0, 10))
        
        # Gemini AI 설정
        gemini_frame = tk.LabelFrame(config_frame, text="Gemini AI 설정", padx=10, pady=10)
        gemini_frame.pack(fill='x', pady=5)
        
        tk.Label(gemini_frame, text="Gemini API Key:").pack(anchor='w')
        tk.Entry(gemini_frame, textvariable=self.gemini_api_key, show="*", width=70).pack(fill='x', pady=(0, 10))
        
        # 설정 저장 버튼
        tk.Button(config_frame, text="설정 저장", command=self.save_config, 
                 bg='#4CAF50', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
        
        # === 기사 생성 탭 ===
        generate_frame = ttk.Frame(notebook)
        notebook.add(generate_frame, text="📰 기사 생성")
        
        # 이미지 업로드 섹션
        upload_frame = tk.LabelFrame(generate_frame, text="1. 이미지 업로드", padx=10, pady=10)
        upload_frame.pack(fill='x', pady=5)
        
        tk.Button(upload_frame, text="📸 이미지 선택 & 업로드", command=self.upload_image,
                 bg='#2196F3', fg='white', font=('Arial', 12, 'bold'), height=2).pack(pady=5)
        
        self.upload_status = tk.StringVar(value="이미지를 선택하세요")
        tk.Label(upload_frame, textvariable=self.upload_status).pack()
        
        # 카테고리 선택
        category_frame = tk.LabelFrame(generate_frame, text="2. 카테고리 선택", padx=10, pady=10)
        category_frame.pack(fill='x', pady=5)
        
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.selected_category, 
                                          state="readonly", width=30)
        self.category_combo.pack(anchor='w', pady=5)
        
        tk.Button(category_frame, text="🔄 카테고리 새로고침", command=self.load_categories).pack(anchor='w')
        
        # 샘플 기사 입력
        sample_frame = tk.LabelFrame(generate_frame, text="3. 샘플 기사 (참고용)", padx=10, pady=10)
        sample_frame.pack(fill='both', expand=True, pady=5)
        
        tk.Label(sample_frame, text="AI가 참고할 기사 스타일을 붙여넣으세요:").pack(anchor='w')
        self.sample_text = scrolledtext.ScrolledText(sample_frame, height=8, wrap='word')
        self.sample_text.pack(fill='both', expand=True, pady=5)
        
        # 기사 생성 버튼
        generate_btn_frame = tk.Frame(generate_frame)
        generate_btn_frame.pack(fill='x', pady=10)
        
        tk.Button(generate_btn_frame, text="🤖 AI 기사 생성", command=self.generate_article,
                 bg='#FF5722', fg='white', font=('Arial', 14, 'bold'), height=2).pack()
        
        # === 결과 탭 ===
        result_frame = ttk.Frame(notebook)
        notebook.add(result_frame, text="📄 결과")
        
        # 결과 표시
        self.result_text = scrolledtext.ScrolledText(result_frame, height=25, wrap='word')
        self.result_text.pack(fill='both', expand=True, pady=5)
        
        # 버튼들
        button_frame = tk.Frame(result_frame)
        button_frame.pack(fill='x', pady=5)
        
        tk.Button(button_frame, text="📋 복사", command=self.copy_result).pack(side='left', padx=5)
        tk.Button(button_frame, text="💾 Hugo 저장", command=self.save_to_hugo).pack(side='left', padx=5)
        
        # 상태바
        self.status_var = tk.StringVar(value="AI 뉴스 기사 생성기 준비완료")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, relief='sunken', anchor='w')
        status_bar.pack(fill='x', side='bottom')
        
    def load_categories(self):
        """categories.yml에서 카테고리 불러오기"""
        try:
            categories_file = "data/categories.yml"
            if os.path.exists(categories_file):
                with open(categories_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.categories = [cat['name'] for cat in data.get('categories', [])]
            else:
                # 기본 카테고리
                self.categories = ['정치', '경제', '사회', '기술', '스포츠']
            
            self.category_combo['values'] = self.categories
            if self.categories:
                self.category_combo.set(self.categories[0])
                
        except Exception as e:
            print(f"카테고리 로딩 실패: {e}")
            self.categories = ['정치', '경제', '사회', '기술', '스포츠']
            self.category_combo['values'] = self.categories
    
    def save_config(self):
        """설정 저장"""
        config = {
            'github_token': self.github_token.get(),
            'github_username': self.github_username.get(),
            'github_repo': self.github_repo.get(),
            'gemini_api_key': self.gemini_api_key.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.status_var.set("✅ 설정이 저장되었습니다")
            messagebox.showinfo("성공", "설정이 저장되었습니다!")
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 실패: {e}")
    
    def load_config(self):
        """설정 불러오기"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.github_token.set(config.get('github_token', ''))
                self.github_username.set(config.get('github_username', ''))
                self.github_repo.set(config.get('github_repo', ''))
                self.gemini_api_key.set(config.get('gemini_api_key', ''))
        except Exception as e:
            print(f"설정 불러오기 실패: {e}")
    
    def upload_image(self):
        """이미지 업로드"""
        if not self.validate_github_config():
            return
        
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[
                ("이미지 파일", "*.jpg *.jpeg *.png *.gif *.webp"),
                ("모든 파일", "*.*")
            ]
        )
        
        if file_path:
            self.upload_status.set("🔄 업로드 중...")
            self.root.update()
            
            try:
                # GitHub에 이미지 업로드
                image_url = self.upload_to_github(file_path)
                
                if image_url:
                    self.uploaded_image_url = image_url
                    self.uploaded_image_path = file_path
                    self.upload_status.set(f"✅ 업로드 완료: {os.path.basename(file_path)}")
                    self.status_var.set("이미지 업로드 완료! 이제 AI 기사를 생성하세요.")
                else:
                    self.upload_status.set("❌ 업로드 실패")
                    
            except Exception as e:
                self.upload_status.set(f"❌ 오류: {str(e)}")
                messagebox.showerror("업로드 오류", str(e))
    
    def upload_to_github(self, file_path):
        """GitHub에 이미지 업로드"""
        try:
            # 파일 읽기
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 파일명 생성
            original_name = os.path.basename(file_path)
            name, ext = os.path.splitext(original_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{name}{ext}"
            
            # 업로드 경로
            upload_path = f"static/images/uploads/{new_filename}"
            
            # GitHub API 호출
            url = f"https://api.github.com/repos/{self.github_username.get()}/{self.github_repo.get()}/contents/{upload_path}"
            
            headers = {
                'Authorization': f'token {self.github_token.get()}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # base64 인코딩
            content_encoded = base64.b64encode(file_content).decode('utf-8')
            
            data = {
                'message': f'AI 뉴스 이미지 업로드: {new_filename}',
                'content': content_encoded
            }
            
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code == 201:
                # 성공 - 이미지 URL 생성
                image_url = f"https://raw.githubusercontent.com/{self.github_username.get()}/{self.github_repo.get()}/main/{upload_path}"
                return image_url
            else:
                error_data = response.json() if response.text else {}
                raise Exception(f"GitHub API 오류 (HTTP {response.status_code}): {error_data.get('message', '알 수 없는 오류')}")
                
        except Exception as e:
            raise Exception(f"이미지 업로드 실패: {str(e)}")
    
    def validate_github_config(self):
        """GitHub 설정 검증"""
        if not self.github_token.get():
            messagebox.showerror("설정 오류", "GitHub Token을 입력해주세요")
            return False
        if not self.github_username.get():
            messagebox.showerror("설정 오류", "GitHub 사용자명을 입력해주세요")
            return False
        if not self.github_repo.get():
            messagebox.showerror("설정 오류", "GitHub 리포지토리명을 입력해주세요")
            return False
        return True
    
    def validate_ai_config(self):
        """AI 설정 검증"""
        if not self.gemini_api_key.get():
            messagebox.showerror("설정 오류", "Gemini API Key를 입력해주세요")
            return False
        return True
    
    def generate_article(self):
        """AI 기사 생성"""
        if not hasattr(self, 'uploaded_image_url'):
            messagebox.showerror("오류", "먼저 이미지를 업로드해주세요!")
            return
        
        if not self.validate_ai_config():
            return
        
        if not self.selected_category.get():
            messagebox.showerror("오류", "카테고리를 선택해주세요!")
            return
        
        try:
            self.status_var.set("🤖 AI가 기사를 생성 중입니다...")
            self.root.update()
            
            # Gemini API 설정
            genai.configure(api_key=self.gemini_api_key.get())
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # 이미지 분석 + 기사 생성
            article_content = self.generate_with_gemini(model)
            
            if article_content:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, article_content)
                self.status_var.set("✅ AI 기사 생성 완료!")
                self.generated_article = article_content
            else:
                self.status_var.set("❌ 기사 생성 실패")
                
        except Exception as e:
            self.status_var.set(f"❌ 오류: {str(e)}")
            messagebox.showerror("AI 오류", f"기사 생성 중 오류 발생:\n{str(e)}")
    
    def generate_with_gemini(self, model):
        """Gemini로 기사 생성"""
        try:
            # 이미지 로드
            image = Image.open(self.uploaded_image_path)
            
            # 샘플 기사 텍스트
            sample_article = self.sample_text.get(1.0, tk.END).strip()
            
            # n8n 워크플로우 스타일의 프롬프트 생성
            prompt = self.create_news_prompt(sample_article)
            
            # Gemini API 호출
            response = model.generate_content([prompt, image])
            
            if response.text:
                # Hugo 마크다운 형식으로 변환
                return self.format_as_hugo_markdown(response.text)
            else:
                raise Exception("Gemini API 응답이 비어있습니다")
                
        except Exception as e:
            raise Exception(f"Gemini API 오류: {str(e)}")
    
    def create_news_prompt(self, sample_article):
        """뉴스 기사 생성 프롬프트 생성"""
        category = self.selected_category.get()
        
        # 카테고리별 감성 키워드
        emotional_keywords = {
            '정치': ['주목', '논란', '격돌', '대립', '합의', '결정', '발표', '변화'],
            '경제': ['충격', '돌파', '폭등', '급등', '대박', '주목', '열풍', '비상', '역대급'],
            '사회': ['화제', '관심', '논란', '변화', '개선', '문제', '해결', '발전'],
            '기술': ['혁신', '획기적', '새로운', '발전', '도약', '변화', '미래', '첨단'],
            '스포츠': ['감동', '역전', '승리', '기록', '돌풍', '화제', '놀라운', '대활약']
        }
        
        keywords = emotional_keywords.get(category, ['주목', '화제', '새로운'])
        
        prompt = f"""
이 이미지를 분석하여 한국 뉴스 기사를 작성해주세요.

**카테고리**: {category}
**감성 키워드**: {', '.join(keywords[:3])}

**기사 작성 규칙**:
1. 제목은 '"{random.choice(keywords)}+핵심사항"…보충설명' 형태로 작성
2. 큰따옴표 안에 짧고 강렬한 문구, 문장 끝 말줄임표(…) 필수
3. 이미지 내용을 정확히 분석하고 관련된 뉴스로 작성
4. 일반 독자도 이해하기 쉽게 전문용어는 풀어서 설명
5. 통계, 수치 등 구체적 정보를 포함하여 신뢰성 확보
6. 첫 문단에 기사의 핵심을 요약
7. 마지막 문단은 향후 전망이나 독자에게 유용한 정보로 마무리

**참고 스타일** (아래 샘플 기사의 톤앤매너를 참고하세요):
{sample_article if sample_article else "전문적이면서도 독자 친화적인 뉴스 스타일로 작성"}

**출력 형식**:
제목: [여기에 제목]

[3-4개 문단, 각 문단 3-4문장으로 작성]

이미지를 정확히 분석하고, 해당 내용과 관련된 현실적이고 구체적인 뉴스 기사를 작성해주세요.
"""
        return prompt
    
    def format_as_hugo_markdown(self, content):
        """Hugo 마크다운 형식으로 변환"""
        try:
            # 제목과 내용 분리
            lines = content.strip().split('\n')
            title = ""
            article_content = ""
            
            for i, line in enumerate(lines):
                if line.startswith('제목:'):
                    title = line.replace('제목:', '').strip()
                    article_content = '\n'.join(lines[i+1:]).strip()
                    break
            
            # 제목이 분리되지 않은 경우 첫 번째 줄을 제목으로
            if not title:
                title = lines[0].strip()
                article_content = '\n'.join(lines[1:]).strip()
            
            # 슬러그 생성
            slug = self.generate_slug(title)
            
            # Hugo front matter 생성
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%dT%H:%M:%S+09:00")
            
            # 이미지 마크다운 추가
            image_markdown = f"\n![{title}]({self.uploaded_image_url})\n"
            
            hugo_content = f"""---
title: "{title}"
date: {date_str}
categories: ["{self.selected_category.get()}"]
tags: ["AI생성", "{self.selected_category.get()}"]
author: "AI 기자"
description: "{title[:100]}..."
image: "{self.uploaded_image_url}"
---

{image_markdown}

{article_content}

---
*이 기사는 AI가 생성한 내용입니다.*
"""
            
            return hugo_content
            
        except Exception as e:
            raise Exception(f"마크다운 변환 오류: {str(e)}")
    
    def generate_slug(self, title):
        """제목에서 슬러그 생성"""
        # 한글 제목을 영어 키워드로 변환 (간단한 버전)
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # 날짜 추가
        date_str = datetime.now().strftime("%Y%m%d")
        category_prefix = self.selected_category.get().lower()
        
        return f"{category_prefix}-{date_str}-ai-news"
    
    def copy_result(self):
        """결과 복사"""
        content = self.result_text.get(1.0, tk.END).strip()
        if content:
            pyperclip.copy(content)
            self.status_var.set("📋 클립보드에 복사되었습니다")
        else:
            messagebox.showinfo("알림", "복사할 내용이 없습니다")
    
    def save_to_hugo(self):
        """Hugo 사이트에 저장"""
        if not hasattr(self, 'generated_article'):
            messagebox.showerror("오류", "먼저 기사를 생성해주세요!")
            return
        
        try:
            # 파일명 생성
            category = self.selected_category.get()
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            filename = f"ai-news-{timestamp}.md"
            
            # 카테고리 폴더 확인/생성
            category_path = f"content/posts/{category}"
            if not os.path.exists(category_path):
                os.makedirs(category_path, exist_ok=True)
            
            # 파일 저장
            filepath = os.path.join(category_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.generated_article)
            
            self.status_var.set(f"✅ Hugo 사이트에 저장완료: {filepath}")
            messagebox.showinfo("저장 완료", f"기사가 저장되었습니다:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("저장 오류", f"Hugo 저장 실패:\n{str(e)}")
    
    def run(self):
        """프로그램 실행"""
        self.root.mainloop()

def main():
    print("🤖 AI 뉴스 기사 생성기 시작...")
    
    try:
        app = AINewsGenerator()
        app.run()
    except Exception as e:
        print(f"💥 오류 발생: {e}")
        input("엔터를 눌러 종료하세요...")

if __name__ == "__main__":
    main() 