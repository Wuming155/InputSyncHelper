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

# 全局变量，用于保存服务器线程和事件循环
server_thread = None
server_loop = None

class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("输入同步助手")
        # 暂时不设置固定大小，让窗口根据内容自动调整
        self.root.attributes("-topmost", True)
        
        main = ttk.Frame(root, padding="20")
        main.pack(fill=tk.BOTH, expand=True)
        
        # 让窗口根据内容自动调整大小
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())
        
        # 创建工具栏
        toolbar = ttk.Frame(main)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # 自定义按钮
        ttk.Button(toolbar, text="自定义", command=self.open_settings).pack(side=tk.LEFT, padx=5)
        
        # 主内容区域
        content = ttk.Frame(main)
        content.pack(fill=tk.BOTH, expand=True)
        
        # 主界面内容
        ttk.Label(content, text="手机扫码立即连接", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.qr_label = ttk.Label(content)
        self.qr_label.pack(pady=10)
        
        self.ip_info = ttk.Label(content, font=("Arial", 11, "underline"), cursor="hand2")
        self.ip_info.pack(pady=5)
        
        self.status = ttk.Label(content, text="● 等待手机连接...", foreground="red", font=("Arial", 10, "bold"))
        self.status.pack(pady=10)
        
        ttk.Separator(content, orient='horizontal').pack(fill='x', pady=10)
        
        ttk.Label(content, text="提示：点击 [ — ] 缩小到托盘\n（请确保手机与电脑在同一 Wi-Fi）", foreground="gray", font=("Arial", 9)).pack()
        
        # 初始化输入控件和设置窗口
        self.settings_window = None
        self.ip_entry = None
        self.port_entry = None
        self.size_entry = None
        self.settings_size_entry = None
        self.backspace_entry = None
        self.smart_detection_var = None
        self.auto_clear_var = None
        self.auto_clear_time_entry = None
        
        # 初始化URL和二维码
        self.update_url()
        
        self.root.bind("<Unmap>", self.on_minimize)
        self.root.protocol('WM_DELETE_WINDOW', self.quit_all)
        self.create_tray()

    def open_settings(self):
        """打开设置窗口"""
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("自定义")
        # 暂时不设置固定大小，让窗口根据内容自动调整
        self.settings_window.transient(self.root)
        self.settings_window.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(self.settings_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 保存按钮放在顶部
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(side=tk.TOP, pady=10, fill=tk.X)
        ttk.Button(save_frame, text="保存设置", command=self.save_settings).pack()
        
        # 内容框架
        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # IP地址设置
        ip_frame = ttk.Frame(settings_frame)
        ip_frame.pack(pady=5, fill=tk.X)
        ttk.Label(ip_frame, text="局域网IP：", width=10).pack(side=tk.LEFT, padx=5)
        self.ip_entry = ttk.Entry(ip_frame)
        self.ip_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.ip_entry.insert(0, utils.settings.get('ip', ''))
        
        # 端口号设置
        port_frame = ttk.Frame(settings_frame)
        port_frame.pack(pady=5, fill=tk.X)
        ttk.Label(port_frame, text="端口号：", width=10).pack(side=tk.LEFT, padx=5)
        self.port_entry = ttk.Entry(port_frame, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, str(utils.get_port()))
        
        # 窗口大小设置
        size_frame = ttk.Frame(settings_frame)
        size_frame.pack(pady=5, fill=tk.X)
        ttk.Label(size_frame, text="窗口大小：", width=10).pack(side=tk.LEFT, padx=5)
        self.size_entry = ttk.Entry(size_frame, width=10)
        self.size_entry.pack(side=tk.LEFT, padx=5)
        self.size_entry.insert(0, utils.get_window_size())
        ttk.Label(size_frame, text="（格式：宽x高）").pack(side=tk.LEFT, padx=5)
        
        # 设置窗口大小设置
        settings_size_frame = ttk.Frame(settings_frame)
        settings_size_frame.pack(pady=5, fill=tk.X)
        ttk.Label(settings_size_frame, text="设置窗口：", width=10).pack(side=tk.LEFT, padx=5)
        self.settings_size_entry = ttk.Entry(settings_size_frame, width=10)
        self.settings_size_entry.pack(side=tk.LEFT, padx=5)
        self.settings_size_entry.insert(0, utils.get_settings_window_size())
        ttk.Label(settings_size_frame, text="（格式：宽x高）").pack(side=tk.LEFT, padx=5)
        
        # 退格次数限制设置
        backspace_frame = ttk.Frame(settings_frame)
        backspace_frame.pack(pady=5, fill=tk.X)
        ttk.Label(backspace_frame, text="退格限制：", width=10).pack(side=tk.LEFT, padx=5)
        self.backspace_entry = ttk.Entry(backspace_frame, width=10)
        self.backspace_entry.pack(side=tk.LEFT, padx=5)
        self.backspace_entry.insert(0, "100")  # 默认值
        ttk.Label(backspace_frame, text="次").pack(side=tk.LEFT, padx=5)
        
        # 智能感知开关设置
        smart_detection_frame = ttk.Frame(settings_frame)
        smart_detection_frame.pack(pady=5, fill=tk.X)
        ttk.Label(smart_detection_frame, text="智能感知：", width=10).pack(side=tk.LEFT, padx=5)
        self.smart_detection_var = tk.BooleanVar(value=utils.get_smart_detection())
        ttk.Checkbutton(smart_detection_frame, variable=self.smart_detection_var, text="开启电脑操作检测\n（开启后，电脑操作会重置同步状态）").pack(side=tk.LEFT, padx=5, anchor=tk.W)
        
        # 自动清空开关设置
        auto_clear_frame = ttk.Frame(settings_frame)
        auto_clear_frame.pack(pady=5, fill=tk.X)
        ttk.Label(auto_clear_frame, text="自动清空：", width=10).pack(side=tk.LEFT, padx=5)
        self.auto_clear_var = tk.BooleanVar(value=utils.get_auto_clear())
        ttk.Checkbutton(auto_clear_frame, variable=self.auto_clear_var, text="开启自动清空\n（开启后，输入一段时间后会自动清空输入框）").pack(side=tk.LEFT, padx=5, anchor=tk.W)
        
        # 自动清空时间设置
        auto_clear_time_frame = ttk.Frame(settings_frame)
        auto_clear_time_frame.pack(pady=5, fill=tk.X)
        ttk.Label(auto_clear_time_frame, text="清空时间：", width=10).pack(side=tk.LEFT, padx=5)
        self.auto_clear_time_entry = ttk.Entry(auto_clear_time_frame, width=10)
        self.auto_clear_time_entry.pack(side=tk.LEFT, padx=5)
        self.auto_clear_time_entry.insert(0, str(utils.get_auto_clear_time()))
        ttk.Label(auto_clear_time_frame, text="秒").pack(side=tk.LEFT, padx=5)
        
        # 让设置窗口根据内容自动调整大小
        self.settings_window.update()
        self.settings_window.minsize(self.settings_window.winfo_width(), self.settings_window.winfo_height())
    
    def update_url(self):
        """更新URL和二维码"""
        url = f"http://{utils.get_ip()}:{utils.get_port()}"
        self.gen_qr(url)
        self.ip_info.config(text=url, foreground="#007AFF")
        self.ip_info.bind("<Button-1>", lambda e: __import__('webbrowser').open(url))
    
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
            # 保存退格次数限制
            backspace_limit = int(self.backspace_entry.get())
            if backspace_limit <= 0:
                self.status.config(text="● 请输入正数", foreground="red")
                self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))
                return
            utils.set_backspace_limit(backspace_limit)
            
            # 保存IP地址
            ip = self.ip_entry.get().strip()
            utils.set_ip(ip)
            
            # 保存端口号
            port = int(self.port_entry.get())
            if port < 1 or port > 65535:
                self.status.config(text="● 端口号范围：1-65535", foreground="red")
                self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))
                return
            utils.set_port(port)
            
            # 保存窗口大小
            size = self.size_entry.get().strip()
            # 简单验证窗口大小格式
            if 'x' not in size:
                self.status.config(text="● 窗口大小格式错误", foreground="red")
                self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))
                return
            utils.set_window_size(size)
            
            # 保存设置窗口大小
            settings_size = self.settings_size_entry.get().strip()
            # 简单验证窗口大小格式
            if 'x' not in settings_size:
                self.status.config(text="● 设置窗口大小格式错误", foreground="red")
                self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))
                return
            utils.set_settings_window_size(settings_size)
            
            # 保存智能感知开关设置
            utils.set_smart_detection(self.smart_detection_var.get())
            
            # 保存自动清空开关设置
            utils.set_auto_clear(self.auto_clear_var.get())
            
            # 保存自动清空时间设置
            auto_clear_time = int(self.auto_clear_time_entry.get())
            if auto_clear_time <= 0:
                self.status.config(text="● 清空时间必须大于0", foreground="red")
                self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))
                return
            utils.set_auto_clear_time(auto_clear_time)
            
            # 重启服务器以应用新的IP和端口
            self.restart_server()
            
            # 更新窗口大小
            self.root.geometry(size)
            
            # 更新URL和二维码
            self.update_url()
            
            # 关闭设置窗口
            if self.settings_window and self.settings_window.winfo_exists():
                self.settings_window.destroy()
            
            # 显示保存成功提示
            self.status.config(text="● 设置保存成功", foreground="#28a745")
            self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))
        except ValueError:
            self.status.config(text="● 请输入正确的数字", foreground="red")
            self.root.after(2000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))
    
    def restart_server(self):
        """重启服务器以应用新的设置"""
        global server_thread, server_loop
        
        # 停止当前服务器
        if server_loop:
            server_loop.call_soon_threadsafe(server_loop.stop)
            if server_thread:
                server_thread.join(timeout=1)
        
        # 启动新服务器
        server_loop = asyncio.new_event_loop()
        server_thread = threading.Thread(
            target=server.start_server_thread, 
            args=(server_loop, self.update_st_callback), 
            daemon=True
        )
        server_thread.start()

    def quit_all(self): 
        self.icon.stop()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app_ui = DesktopApp(root)
    
    # 启动后端服务
    server_loop = asyncio.new_event_loop()
    server_thread = threading.Thread(
        target=server.start_server_thread, 
        args=(server_loop, app_ui.update_st_callback), 
        daemon=True
    )
    server_thread.start()
    
    root.mainloop()