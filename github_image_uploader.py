#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국뉴스 깃허브 이미지 업로더
GitHub API를 사용하여 이미지를 업로드하고 마크다운 링크를 생성합니다.
"""

import sys
import locale
import os

# Windows 인코딩 설정
if sys.platform == "win32":
    try:
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Korean_Korea.949')
        except:
            pass

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tk_font
import tkinterdnd2 as tkdnd
import requests
import base64
import json
import os
import threading
import time
from datetime import datetime
import pyperclip
from PIL import Image, ImageTk
import io
import hashlib

class GitHubImageUploader:
    def __init__(self):
        self.root = tkdnd.Tk()
        self.root.title("📸 한국뉴스 깃허브 이미지 업로더")
        self.root.geometry("600x700")
        self.root.configure(bg='#f8f9fa')
        
        # 한글 폰트 설정
        self.korean_font = self.get_korean_font()
        
        # 설정 파일 경로
        self.config_file = "github_uploader_config.json"
        
        # 설정 변수들
        self.github_token = tk.StringVar()
        self.github_username = tk.StringVar()
        self.github_repo = tk.StringVar()
        self.upload_path = tk.StringVar(value="static/images/uploads/")
        
        # UI 구성
        self.create_widgets()
        
        # 설정 불러오기
        self.load_config()
        
        # 드래그앤드롭 설정
        self.setup_drag_drop()
    
    def get_korean_font(self):
        """한글을 지원하는 폰트를 찾습니다."""
        korean_fonts = [
            ('Malgun Gothic', 12),
            ('맑은 고딕', 12),
            ('Gulim', 12),
            ('굴림', 12),
            ('Dotum', 12),
            ('돋움', 12),
            ('Arial Unicode MS', 12),
            ('Arial', 12)
        ]
        
        for font_name, size in korean_fonts:
            try:
                test_font = tk_font.Font(family=font_name, size=size)
                return (font_name, size)
            except:
                continue
        
        return ('Arial', 12)  # 최후의 대안
        
    def create_widgets(self):
        """UI 구성 요소들을 생성합니다."""
        
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_font = (self.korean_font[0], 16, 'bold')
        title_label = ttk.Label(main_frame, text="📸 깃허브 이미지 업로더", 
                               font=title_font)
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 설정 섹션
        config_frame = ttk.LabelFrame(main_frame, text="깃허브 설정", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # GitHub Token
        ttk.Label(config_frame, text="GitHub Token:").grid(row=0, column=0, sticky=tk.W, pady=5)
        token_entry = ttk.Entry(config_frame, textvariable=self.github_token, show="*", width=50)
        token_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # GitHub 사용자명
        ttk.Label(config_frame, text="사용자명:").grid(row=1, column=0, sticky=tk.W, pady=5)
        username_entry = ttk.Entry(config_frame, textvariable=self.github_username, width=30)
        username_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # GitHub 리포지토리
        ttk.Label(config_frame, text="리포지토리:").grid(row=2, column=0, sticky=tk.W, pady=5)
        repo_entry = ttk.Entry(config_frame, textvariable=self.github_repo, width=30)
        repo_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 업로드 경로
        ttk.Label(config_frame, text="업로드 경로:").grid(row=3, column=0, sticky=tk.W, pady=5)
        path_entry = ttk.Entry(config_frame, textvariable=self.upload_path, width=40)
        path_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 설정 저장 버튼
        save_btn = ttk.Button(config_frame, text="설정 저장", command=self.save_config)
        save_btn.grid(row=4, column=1, sticky=tk.E, pady=10, padx=(10, 0))
        
        # 드래그앤드롭 영역
        self.drop_frame = tk.Frame(main_frame, bg='#e9ecef', relief='dashed', bd=2, height=200)
        self.drop_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        self.drop_frame.grid_propagate(False)
        
        drop_label = tk.Label(self.drop_frame, 
                             text="📁 이미지를 여기에 드래그하거나\n클릭해서 파일을 선택하세요",
                             bg='#e9ecef', fg='#6c757d', font=self.korean_font)
        drop_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # 파일 선택 바인딩
        self.drop_frame.bind("<Button-1>", self.select_file)
        drop_label.bind("<Button-1>", self.select_file)
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 상태 텍스트
        self.status_var = tk.StringVar(value="업로드할 이미지를 선택하세요")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=4, column=0, columnspan=2, pady=(0, 20))
        
        # 결과 텍스트 영역
        result_frame = ttk.LabelFrame(main_frame, text="생성된 마크다운 링크", padding="10")
        result_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        self.result_text = tk.Text(result_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 복사 버튼
        copy_btn = ttk.Button(result_frame, text="📋 클립보드에 복사", command=self.copy_to_clipboard)
        copy_btn.grid(row=1, column=0, columnspan=2, pady=10)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        config_frame.columnconfigure(1, weight=1)
        
    def setup_drag_drop(self):
        """드래그앤드롭 기능을 설정합니다."""
        self.drop_frame.drop_target_register(tkdnd.DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
    def on_drop(self, event):
        """파일이 드롭되었을 때 실행됩니다."""
        files = self.root.tk.splitlist(event.data)
        for file_path in files:
            if self.is_image_file(file_path):
                self.upload_image(file_path)
                break
        else:
            messagebox.showwarning("경고", "지원되는 이미지 파일을 선택해주세요.\n(JPG, PNG, GIF, WebP)")
    
    def select_file(self, event=None):
        """파일 선택 다이얼로그를 엽니다."""
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[
                ("이미지 파일", "*.jpg *.jpeg *.png *.gif *.webp"),
                ("모든 파일", "*.*")
            ]
        )
        if file_path:
            self.upload_image(file_path)
    
    def is_image_file(self, file_path):
        """이미지 파일인지 확인합니다."""
        return file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
    
    def save_config(self):
        """설정을 파일에 저장합니다."""
        config = {
            'github_token': self.github_token.get(),
            'github_username': self.github_username.get(),
            'github_repo': self.github_repo.get(),
            'upload_path': self.upload_path.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.status_var.set("✅ 설정이 저장되었습니다")
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 실패: {e}")
    
    def load_config(self):
        """설정을 파일에서 불러옵니다."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.github_token.set(config.get('github_token', ''))
                self.github_username.set(config.get('github_username', ''))
                self.github_repo.set(config.get('github_repo', ''))
                self.upload_path.set(config.get('upload_path', 'static/images/uploads/'))
        except Exception as e:
            print(f"설정 불러오기 실패: {e}")
    
    def upload_image(self, file_path):
        """이미지를 깃허브에 업로드합니다."""
        if not self.validate_config():
            return
        
        # 별도 스레드에서 업로드 실행
        thread = threading.Thread(target=self._upload_image_thread, args=(file_path,))
        thread.daemon = True
        thread.start()
    
    def validate_config(self):
        """설정값들을 검증합니다."""
        if not self.github_token.get():
            messagebox.showerror("오류", "GitHub Token을 입력해주세요")
            return False
        if not self.github_username.get():
            messagebox.showerror("오류", "GitHub 사용자명을 입력해주세요")
            return False
        if not self.github_repo.get():
            messagebox.showerror("오류", "GitHub 리포지토리명을 입력해주세요")
            return False
        return True
    
    def _upload_image_thread(self, file_path):
        """실제 업로드를 수행하는 스레드 함수입니다."""
        try:
            self.progress_var.set(10)
            self.status_var.set("🔄 이미지 준비 중...")
            
            # 파일 읽기
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            self.progress_var.set(30)
            
            # 파일명 생성 (타임스탬프 + 원본명)
            original_name = os.path.basename(file_path)
            name, ext = os.path.splitext(original_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{name}{ext}"
            
            # 업로드 경로 구성
            upload_path = self.upload_path.get().rstrip('/') + '/' + new_filename
            
            self.progress_var.set(50)
            self.status_var.set("📤 깃허브에 업로드 중...")
            
            # GitHub API 호출
            url = f"https://api.github.com/repos/{self.github_username.get()}/{self.github_repo.get()}/contents/{upload_path}"
            
            headers = {
                'Authorization': f'token {self.github_token.get()}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # base64 인코딩
            content_encoded = base64.b64encode(file_content).decode('utf-8')
            
            data = {
                'message': f'이미지 업로드: {new_filename}',
                'content': content_encoded
            }
            
            self.progress_var.set(70)
            
            response = requests.put(url, headers=headers, json=data)
            
            self.progress_var.set(90)
            
            if response.status_code == 201:
                # 성공
                self.progress_var.set(100)
                self.status_var.set("✅ 업로드 완료!")
                
                # 이미지 URL 생성
                image_url = f"https://raw.githubusercontent.com/{self.github_username.get()}/{self.github_repo.get()}/main/{upload_path}"
                
                # 마크다운 링크 생성
                markdown_link = f"![{name}]({image_url})"
                
                # 결과 표시
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, f"📸 업로드 완료!\n\n")
                self.result_text.insert(tk.END, f"파일명: {new_filename}\n")
                self.result_text.insert(tk.END, f"이미지 URL:\n{image_url}\n\n")
                self.result_text.insert(tk.END, f"마크다운 링크:\n{markdown_link}")
                
                # 클립보드에 자동 복사
                pyperclip.copy(markdown_link)
                
                # 3초 후 진행률 초기화
                self.root.after(3000, lambda: self.progress_var.set(0))
                
            else:
                # 실패
                self.progress_var.set(0)
                error_msg = f"업로드 실패 (HTTP {response.status_code})"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f": {error_data.get('message', '알 수 없는 오류')}"
                    except:
                        error_msg += f": {response.text[:100]}"
                
                self.status_var.set(f"❌ {error_msg}")
                messagebox.showerror("업로드 실패", error_msg)
                
        except Exception as e:
            self.progress_var.set(0)
            error_msg = f"오류 발생: {str(e)}"
            self.status_var.set(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)
    
    def copy_to_clipboard(self):
        """결과 텍스트를 클립보드에 복사합니다."""
        content = self.result_text.get(1.0, tk.END).strip()
        if content:
            # 마크다운 링크만 추출
            lines = content.split('\n')
            for line in lines:
                if line.startswith('!['):
                    pyperclip.copy(line)
                    self.status_var.set("📋 마크다운 링크가 클립보드에 복사되었습니다")
                    return
            
            # 마크다운 링크가 없으면 전체 내용 복사
            pyperclip.copy(content)
            self.status_var.set("📋 내용이 클립보드에 복사되었습니다")
        else:
            messagebox.showinfo("알림", "복사할 내용이 없습니다")
    
    def run(self):
        """프로그램을 실행합니다."""
        self.root.mainloop()

def main():
    """메인 함수"""
    print("=" * 50)
    print("📸 한국뉴스 깃허브 이미지 업로더")
    print("=" * 50)
    
    try:
        app = GitHubImageUploader()
        app.run()
    except Exception as e:
        print(f"❌ 프로그램 실행 중 오류가 발생했습니다: {e}")
        input("엔터를 눌러 종료하세요...")

if __name__ == "__main__":
    main() 