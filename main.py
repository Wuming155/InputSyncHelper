# main.py
import tkinter as tk
from tkinter import ttk
import threading
import asyncio
import sys
import qrcode
from PIL import Image, ImageDraw, ImageTk
from pystray import Icon, Menu, MenuItem

import utils
import server

class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("输入同步助手")
        self.root.geometry("500x600")
        self.root.attributes("-topmost", True)
        
        main = ttk.Frame(root, padding="20")
        main.pack(fill=tk.BOTH, expand=True)
        
        url = f"http://{utils.get_local_ip()}:5000"
        
        ttk.Label(main, text="手机扫码立即连接", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.qr_label = ttk.Label(main)
        self.qr_label.pack(pady=10)
        self.gen_qr(url)

        self.ip_info = ttk.Label(main, text=url, foreground="#007AFF", font=("Arial", 11, "underline"), cursor="hand2")
        self.ip_info.pack(pady=5)
        self.ip_info.bind("<Button-1>", lambda e: __import__('webbrowser').open(url))
        
        self.status = ttk.Label(main, text="● 等待手机连接...", foreground="red", font=("Arial", 10, "bold"))
        self.status.pack(pady=10)
        
        ttk.Separator(main, orient='horizontal').pack(fill='x', pady=10)
        
        # 添加退格次数设置
        ttk.Label(main, text="退格次数限制", font=("Arial", 10, "bold")).pack(pady=5)
        
        # 创建输入框和默认值
        self.backspace_frame = ttk.Frame(main)
        self.backspace_frame.pack(pady=5)
        
        ttk.Label(self.backspace_frame, text="安全限制：").pack(side=tk.LEFT, padx=5)
        self.backspace_entry = ttk.Entry(self.backspace_frame, width=10)
        self.backspace_entry.pack(side=tk.LEFT, padx=5)
        self.backspace_entry.insert(0, "100")  # 默认值
        
        ttk.Label(self.backspace_frame, text="次").pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        ttk.Button(main, text="保存设置", command=self.save_settings).pack(pady=5)
        
        ttk.Label(main, text="提示：点击 [ — ] 缩小到托盘\n（请确保手机与电脑在同一 Wi-Fi）", foreground="gray", font=("Arial", 9)).pack()
        
        self.root.bind("<Unmap>", self.on_minimize)
        self.root.protocol('WM_DELETE_WINDOW', self.quit_all)
        self.create_tray()

    def gen_qr(self, data):
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        self.tk_qr = ImageTk.PhotoImage(img)
        self.qr_label.config(image=self.tk_qr)

    def update_st_callback(self, connected):
        """供后端调用的状态更新"""
        color = "#28a745" if connected else "red"
        text = "● 📱 手机已连接" if connected else "● 等待手机连接..."
        self.root.after(0, lambda: self.status.config(text=text, foreground=color))

    def create_tray(self):
        img = Image.new('RGB', (64, 64), (0, 122, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([16, 16, 48, 48], fill="white")
        
        # 1. 定义菜单，并将“显示窗口”设为默认动作 (default=True)
        # 这样双击图标时就会触发 self.show
        menu = Menu(
            MenuItem('显示窗口', self.show, default=True), 
            MenuItem('退出', self.quit_all)
        )
        
        self.icon = Icon("Sync", img, "输入同步助手", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def on_minimize(self, event):
        if self.root.state() == 'iconic': self.root.withdraw()

    def show(self): 
        self.root.after(0, self.root.deiconify)
        self.root.after(10, lambda: self.root.state('normal'))

    def save_settings(self):
        """保存用户设置"""
        try:
            backspace_limit = int(self.backspace_entry.get())
            if backspace_limit > 0:
                utils.set_backspace_limit(backspace_limit)
                # 显示保存成功提示
                self.status.config(text="● 设置保存成功", foreground="#28a745")
                self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))
            else:
                self.status.config(text="● 请输入正数", foreground="red")
                self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))
        except ValueError:
            self.status.config(text="● 请输入数字", foreground="red")
            self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))

    def quit_all(self): 
        self.icon.stop()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app_ui = DesktopApp(root)
    
    # 启动后端服务
    server_loop = asyncio.new_event_loop()
    t = threading.Thread(
        target=server.start_server_thread, 
        args=(server_loop, app_ui.update_st_callback), 
        daemon=True
    )
    t.start()
    
    root.mainloop()