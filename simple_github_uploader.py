#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 깃허브 이미지 업로더
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import base64
import json
import os
from datetime import datetime
import pyperclip
import traceback

class SimpleGitHubUploader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GitHub 이미지 업로더")
        self.root.geometry("500x600")
        
        # 설정 변수들
        self.github_token = tk.StringVar()
        self.github_username = tk.StringVar()
        self.github_repo = tk.StringVar()
        
        self.config_file = "uploader_config.json"
        
        self.create_widgets()
        self.load_config()
        
    def create_widgets(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 제목
        title_label = tk.Label(main_frame, text="GitHub 이미지 업로더", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 설정 프레임
        config_frame = tk.LabelFrame(main_frame, text="GitHub 설정", padx=10, pady=10)
        config_frame.pack(fill='x', pady=(0, 20))
        
        # Token
        tk.Label(config_frame, text="GitHub Token:").pack(anchor='w')
        tk.Entry(config_frame, textvariable=self.github_token, show="*", width=60).pack(fill='x', pady=(0, 10))
        
        # 사용자명
        tk.Label(config_frame, text="사용자명:").pack(anchor='w')
        tk.Entry(config_frame, textvariable=self.github_username, width=30).pack(anchor='w', pady=(0, 10))
        
        # 리포지토리
        tk.Label(config_frame, text="리포지토리:").pack(anchor='w')
        tk.Entry(config_frame, textvariable=self.github_repo, width=30).pack(anchor='w', pady=(0, 10))
        
        # 설정 저장 버튼
        tk.Button(config_frame, text="설정 저장", command=self.save_config).pack(anchor='e')
        
        # 파일 선택 버튼
        tk.Button(main_frame, text="이미지 파일 선택", command=self.select_file, 
                 width=20, height=2).pack(pady=20)
        
        # 상태 레이블
        self.status_var = tk.StringVar(value="이미지를 선택하세요")
        status_label = tk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=10)
        
        # 결과 텍스트
        result_frame = tk.LabelFrame(main_frame, text="결과", padx=10, pady=10)
        result_frame.pack(fill='both', expand=True, pady=20)
        
        self.result_text = tk.Text(result_frame, height=10, wrap='word')
        scrollbar = tk.Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 복사 버튼
        tk.Button(result_frame, text="클립보드에 복사", command=self.copy_result).pack(pady=10)
        
    def save_config(self):
        """설정 저장"""
        config = {
            'github_token': self.github_token.get(),
            'github_username': self.github_username.get(),
            'github_repo': self.github_repo.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.status_var.set("설정이 저장되었습니다")
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
        except Exception as e:
            print(f"설정 불러오기 실패: {e}")
    
    def select_file(self):
        """파일 선택"""
        file_path = filedialog.askopenfilename(
            title="이미지 파일 선택",
            filetypes=[
                ("이미지 파일", "*.jpg *.jpeg *.png *.gif *.webp"),
                ("모든 파일", "*.*")
            ]
        )
        if file_path:
            self.upload_image(file_path)
    
    def upload_image(self, file_path):
        """이미지 업로드"""
        print(f"\n=== 업로드 시작 ===")
        print(f"파일 경로: {file_path}")
        
        if not self.validate_config():
            print("❌ 설정 검증 실패")
            return
        
        print(f"GitHub 사용자명: {self.github_username.get()}")
        print(f"GitHub 리포지토리: {self.github_repo.get()}")
        print(f"GitHub 토큰: {self.github_token.get()[:10]}...{self.github_token.get()[-4:] if len(self.github_token.get()) > 10 else 'too_short'}")
        
        try:
            self.status_var.set("업로드 중...")
            self.root.update()
            
            # 파일 읽기
            print("📂 파일 읽는 중...")
            with open(file_path, 'rb') as f:
                file_content = f.read()
            print(f"파일 크기: {len(file_content)} bytes")
            
            # 파일명 생성
            original_name = os.path.basename(file_path)
            name, ext = os.path.splitext(original_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{name}{ext}"
            print(f"새 파일명: {new_filename}")
            
            # 업로드 경로
            upload_path = f"static/images/uploads/{new_filename}"
            print(f"업로드 경로: {upload_path}")
            
            # GitHub API 호출
            url = f"https://api.github.com/repos/{self.github_username.get()}/{self.github_repo.get()}/contents/{upload_path}"
            print(f"API URL: {url}")
            
            headers = {
                'Authorization': f'token {self.github_token.get()}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # base64 인코딩
            print("🔄 base64 인코딩 중...")
            content_encoded = base64.b64encode(file_content).decode('utf-8')
            print(f"인코딩된 크기: {len(content_encoded)} chars")
            
            data = {
                'message': f'이미지 업로드: {new_filename}',
                'content': content_encoded
            }
            
            print("📤 GitHub API 호출 중...")
            response = requests.put(url, headers=headers, json=data)
            print(f"HTTP 상태 코드: {response.status_code}")
            print(f"응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 201:
                # 성공
                print("✅ 업로드 성공!")
                response_data = response.json()
                print(f"GitHub 응답: {response_data.get('content', {}).get('download_url', 'URL 없음')}")
                
                self.status_var.set("업로드 완료!")
                
                # 이미지 URL 생성
                image_url = f"https://raw.githubusercontent.com/{self.github_username.get()}/{self.github_repo.get()}/main/{upload_path}"
                print(f"생성된 이미지 URL: {image_url}")
                
                # 마크다운 링크 생성
                markdown_link = f"![{name}]({image_url})"
                print(f"마크다운 링크: {markdown_link}")
                
                # 결과 표시
                result = f"업로드 완료!\n\n파일명: {new_filename}\n\n이미지 URL:\n{image_url}\n\n마크다운 링크:\n{markdown_link}"
                
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, result)
                
                # 클립보드에 자동 복사
                pyperclip.copy(markdown_link)
                print("📋 클립보드에 복사 완료!")
                
            else:
                # 실패
                print("❌ 업로드 실패!")
                print(f"응답 본문: {response.text}")
                
                error_msg = f"업로드 실패 (HTTP {response.status_code})"
                if response.text:
                    try:
                        error_data = response.json()
                        print(f"JSON 응답: {error_data}")
                        error_msg += f": {error_data.get('message', '알 수 없는 오류')}"
                    except Exception as json_err:
                        print(f"JSON 파싱 실패: {json_err}")
                        error_msg += f": {response.text[:100]}"
                
                print(f"최종 오류 메시지: {error_msg}")
                self.status_var.set(error_msg)
                messagebox.showerror("업로드 실패", error_msg)
                
        except Exception as e:
            print("💥 예외 발생!")
            print(f"예외 유형: {type(e).__name__}")
            print(f"예외 메시지: {str(e)}")
            print("전체 스택 트레이스:")
            traceback.print_exc()
            
            error_msg = f"오류 발생: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("오류", error_msg)
    
    def validate_config(self):
        """설정 검증"""
        print("\n🔍 설정 검증 중...")
        
        token = self.github_token.get().strip()
        username = self.github_username.get().strip()
        repo = self.github_repo.get().strip()
        
        print(f"토큰 길이: {len(token)} chars")
        print(f"사용자명: '{username}'")
        print(f"리포지토리: '{repo}'")
        
        if not token:
            print("❌ GitHub Token이 비어있음")
            messagebox.showerror("오류", "GitHub Token을 입력해주세요")
            return False
        if not username:
            print("❌ GitHub 사용자명이 비어있음")
            messagebox.showerror("오류", "GitHub 사용자명을 입력해주세요")
            return False
        if not repo:
            print("❌ GitHub 리포지토리명이 비어있음")
            messagebox.showerror("오류", "GitHub 리포지토리명을 입력해주세요")
            return False
        
        print("✅ 모든 설정 검증 통과")
        return True
    
    def copy_result(self):
        """결과 복사"""
        content = self.result_text.get(1.0, tk.END).strip()
        if content:
            # 마크다운 링크만 추출
            lines = content.split('\n')
            for line in lines:
                if line.startswith('!['):
                    pyperclip.copy(line)
                    self.status_var.set("마크다운 링크가 클립보드에 복사되었습니다")
                    return
            
            # 전체 내용 복사
            pyperclip.copy(content)
            self.status_var.set("내용이 클립보드에 복사되었습니다")
        else:
            messagebox.showinfo("알림", "복사할 내용이 없습니다")
    
    def run(self):
        """프로그램 실행"""
        self.root.mainloop()

def main():
    print("=" * 50)
    print("🚀 GitHub 이미지 업로더 시작...")
    print("=" * 50)
    print("💡 모든 로그가 터미널에 표시됩니다")
    print("💡 GUI 창과 함께 이 터미널도 확인하세요")
    print("=" * 50)
    
    try:
        app = SimpleGitHubUploader()
        print("📱 GUI 애플리케이션 시작됨")
        app.run()
        print("🔚 GUI 애플리케이션 종료됨")
    except Exception as e:
        print("💥 메인 함수에서 예외 발생!")
        print(f"예외 유형: {type(e).__name__}")
        print(f"예외 메시지: {str(e)}")
        traceback.print_exc()
        input("엔터를 눌러 종료하세요...")

if __name__ == "__main__":
    main() 