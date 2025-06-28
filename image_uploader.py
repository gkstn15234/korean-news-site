import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import requests
import json
import os
from pathlib import Path
import threading
import pyperclip
from tkinterdnd2 import DND_FILES, TkinterDnD
import base64
import hashlib

class CloudflareImageUploader:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("한국뉴스 이미지 업로더 📸")
        self.root.geometry("500x600")
        self.root.configure(bg='#f5f7fa')
        
        # API 설정
        self.api_token = ""
        self.account_id = ""
        self.config_file = "cloudflare_config.json"
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        # 메인 프레임
        main_frame = tk.Frame(self.root, bg='#f5f7fa', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 제목
        title_font = font.Font(family="맑은 고딕", size=16, weight="bold")
        title_label = tk.Label(main_frame, text="📸 한국뉴스 이미지 업로더", 
                              font=title_font, bg='#f5f7fa', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # API 설정 프레임
        config_frame = tk.LabelFrame(main_frame, text="📋 클라우드플레어 설정", 
                                   bg='#f5f7fa', fg='#34495e', font=("맑은 고딕", 10, "bold"))
        config_frame.pack(fill='x', pady=(0, 20))
        
        # API Token
        tk.Label(config_frame, text="API Token:", bg='#f5f7fa', fg='#2c3e50').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.token_entry = tk.Entry(config_frame, width=50, show="*")
        self.token_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Account ID
        tk.Label(config_frame, text="Account ID:", bg='#f5f7fa', fg='#2c3e50').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.account_entry = tk.Entry(config_frame, width=50)
        self.account_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # 설정 저장 버튼
        save_btn = tk.Button(config_frame, text="💾 설정 저장", command=self.save_config,
                           bg='#3498db', fg='white', font=("맑은 고딕", 9, "bold"))
        save_btn.grid(row=2, column=1, sticky='e', padx=10, pady=10)
        
        # 도움말 버튼
        help_btn = tk.Button(config_frame, text="❓ 설정 도움말", command=self.show_help,
                           bg='#95a5a6', fg='white', font=("맑은 고딕", 9, "bold"))
        help_btn.grid(row=2, column=0, sticky='w', padx=10, pady=10)
        
        # 드래그앤드롭 영역
        drop_frame = tk.Frame(main_frame, bg='#ecf0f1', relief='dashed', bd=2)
        drop_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        self.drop_label = tk.Label(drop_frame, 
                                  text="🖼️ 이미지를 여기로 드래그하세요\n또는 클릭해서 파일을 선택하세요",
                                  bg='#ecf0f1', fg='#7f8c8d',
                                  font=("맑은 고딕", 12),
                                  justify='center')
        self.drop_label.pack(expand=True)
        
        # 드래그앤드롭 이벤트 바인딩
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.drop_files)
        self.drop_label.bind("<Button-1>", self.select_file)
        
        # 상태 표시
        self.status_var = tk.StringVar(value="📁 이미지를 선택해주세요")
        status_label = tk.Label(main_frame, textvariable=self.status_var,
                              bg='#f5f7fa', fg='#34495e', font=("맑은 고딕", 10))
        status_label.pack(pady=(0, 10))
        
        # 진행률 바
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(0, 20))
        
        # 결과 영역
        result_frame = tk.LabelFrame(main_frame, text="📋 업로드 결과", 
                                   bg='#f5f7fa', fg='#34495e', font=("맑은 고딕", 10, "bold"))
        result_frame.pack(fill='x')
        
        # 마크다운 링크
        tk.Label(result_frame, text="마크다운 링크:", bg='#f5f7fa', fg='#2c3e50').pack(anchor='w', padx=10, pady=(10,0))
        self.markdown_text = tk.Text(result_frame, height=2, wrap='word')
        self.markdown_text.pack(fill='x', padx=10, pady=5)
        
        # 직접 링크
        tk.Label(result_frame, text="직접 링크:", bg='#f5f7fa', fg='#2c3e50').pack(anchor='w', padx=10)
        self.url_text = tk.Text(result_frame, height=2, wrap='word')
        self.url_text.pack(fill='x', padx=10, pady=5)
        
        # 복사 버튼들
        btn_frame = tk.Frame(result_frame, bg='#f5f7fa')
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        copy_md_btn = tk.Button(btn_frame, text="📋 마크다운 복사", command=self.copy_markdown,
                              bg='#27ae60', fg='white', font=("맑은 고딕", 9, "bold"))
        copy_md_btn.pack(side='left', padx=(0, 10))
        
        copy_url_btn = tk.Button(btn_frame, text="🔗 링크 복사", command=self.copy_url,
                               bg='#e74c3c', fg='white', font=("맑은 고딕", 9, "bold"))
        copy_url_btn.pack(side='left')
        
    def load_config(self):
        """저장된 설정 불러오기"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.token_entry.insert(0, config.get('api_token', ''))
                    self.account_entry.insert(0, config.get('account_id', ''))
        except Exception as e:
            pass
    
    def save_config(self):
        """설정 저장하기"""
        try:
            config = {
                'api_token': self.token_entry.get(),
                'account_id': self.account_entry.get()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            messagebox.showinfo("성공", "설정이 저장되었습니다! 🎉")
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 실패: {str(e)}")
    
    def show_help(self):
        """도움말 표시"""
        help_text = """🔧 클라우드플레어 설정 방법:

1. 클라우드플레어 대시보드 접속
2. 'Images' 메뉴로 이동
3. API 키 생성:
   - My Profile > API Tokens
   - Create Token
   - Cloudflare Images:Edit 권한 설정

4. Account ID 확인:
   - 대시보드 우측에서 확인 가능

💡 무료 플랜: 월 100,000회 요청, 5GB 저장공간"""
        
        messagebox.showinfo("설정 도움말", help_text)
    
    def drop_files(self, event):
        """드래그앤드롭 파일 처리"""
        files = self.root.tk.splitlist(event.data)
        if files:
            self.upload_image(files[0])
    
    def select_file(self, event=None):
        """파일 선택 다이얼로그"""
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
        """이미지 업로드 (백그라운드에서 실행)"""
        if not self.token_entry.get() or not self.account_entry.get():
            messagebox.showerror("오류", "API Token과 Account ID를 먼저 설정해주세요!")
            return
        
        # UI 상태 업데이트
        self.status_var.set("🚀 업로드 중...")
        self.progress.start()
        
        # 백그라운드에서 업로드 실행
        thread = threading.Thread(target=self._upload_worker, args=(file_path,))
        thread.daemon = True
        thread.start()
    
    def _upload_worker(self, file_path):
        """실제 업로드 작업"""
        try:
            # 파일 정보
            file_name = Path(file_path).name
            
            # API 요청 준비
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_entry.get()}/images/v1"
            headers = {
                'Authorization': f'Bearer {self.token_entry.get()}'
            }
            
            # 파일 업로드
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, 'image/*')
                }
                response = requests.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    image_url = data['result']['variants'][0]  # 기본 variant URL
                    
                    # UI 업데이트 (메인 스레드에서)
                    self.root.after(0, self._upload_success, file_name, image_url)
                else:
                    self.root.after(0, self._upload_error, f"API 오류: {data.get('errors', 'Unknown error')}")
            else:
                self.root.after(0, self._upload_error, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.root.after(0, self._upload_error, str(e))
    
    def _upload_success(self, file_name, image_url):
        """업로드 성공 처리"""
        self.progress.stop()
        self.status_var.set(f"✅ '{file_name}' 업로드 완료!")
        
        # 마크다운 링크 생성
        markdown_link = f"![{file_name}]({image_url})"
        
        # 텍스트 영역에 결과 표시
        self.markdown_text.delete('1.0', 'end')
        self.markdown_text.insert('1.0', markdown_link)
        
        self.url_text.delete('1.0', 'end')
        self.url_text.insert('1.0', image_url)
        
        # 자동으로 마크다운 링크 복사
        pyperclip.copy(markdown_link)
        self.status_var.set(f"✅ 업로드 완료! 마크다운 링크가 클립보드에 복사되었습니다.")
    
    def _upload_error(self, error_msg):
        """업로드 오류 처리"""
        self.progress.stop()
        self.status_var.set("❌ 업로드 실패")
        messagebox.showerror("업로드 오류", f"업로드에 실패했습니다:\n{error_msg}")
    
    def copy_markdown(self):
        """마크다운 링크 복사"""
        text = self.markdown_text.get('1.0', 'end-1c')
        if text:
            pyperclip.copy(text)
            messagebox.showinfo("복사 완료", "마크다운 링크가 클립보드에 복사되었습니다! 📋")
    
    def copy_url(self):
        """직접 링크 복사"""
        text = self.url_text.get('1.0', 'end-1c')
        if text:
            pyperclip.copy(text)
            messagebox.showinfo("복사 완료", "이미지 링크가 클립보드에 복사되었습니다! 🔗")
    
    def run(self):
        """프로그램 실행"""
        self.root.mainloop()

if __name__ == "__main__":
    app = CloudflareImageUploader()
    app.run() 