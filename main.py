# main.py
import tkinter as tk
from tkinter import ttk
import threading
import asyncio
import sys
import time
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
        self.backspace_entry = None
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
        
        # 退格次数限制设置
        backspace_frame = ttk.Frame(settings_frame)
        backspace_frame.pack(pady=5, fill=tk.X)
        ttk.Label(backspace_frame, text="退格限制：", width=10).pack(side=tk.LEFT, padx=5)
        self.backspace_entry = ttk.Entry(backspace_frame, width=10)
        self.backspace_entry.pack(side=tk.LEFT, padx=5)
        self.backspace_entry.insert(0, str(utils.get_backspace_limit()))
        ttk.Label(backspace_frame, text="次").pack(side=tk.LEFT, padx=5)
        
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
    
    def _is_valid_ip(self, ip):
        """验证 IP 地址格式是否有效"""
        import re
        # IPv4 地址格式验证
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        # 检查每个数字段是否在 0-255 范围内
        parts = ip.split('.')
        for part in parts:
            if int(part) > 255:
                return False
        return True
    
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
            # 补全其他业务设置的保存
            utils.set_backspace_limit(int(self.backspace_entry.get()))
            utils.set_auto_clear(self.auto_clear_var.get())
            utils.set_auto_clear_time(int(self.auto_clear_time_entry.get()))

            # --- 核心修改：区分重启还是广播 ---
            # 只有改了 IP 或 端口，才需要重启服务器
            new_ip = self.ip_entry.get()
            new_port = int(self.port_entry.get())
            old_ip = utils.get_port_info()['ip']
            old_port = utils.get_port()

            if new_ip != old_ip or new_port != old_port:
                utils.set_port(new_port)
                utils.set_ip(new_ip)
                self.restart_server()
            else:
                # 仅仅修改业务配置（退格、清空等），直接广播，手机不掉线
                try:
                    server.broadcast_config()
                    self.update_url() # 更新主界面显示
                except:
                    pass
            # -------------------------------

            self.settings_window.destroy()
        except ValueError as e:
            print(f"保存设置失败：{e}")
            pass
    
    def restart_server(self):
        """重启服务器以应用新的设置"""
        global server_thread, server_loop
        
        try:
            # 停止当前服务器
            if server_loop and server_loop.is_running():
                server_loop.call_soon_threadsafe(server_loop.stop)
                
            # 等待服务器线程结束
            if server_thread:
                server_thread.join(timeout=3)
                
            # 关闭旧的事件循环
            if server_loop:
                server_loop.close()
        except Exception as e:
            print(f"停止服务器时出错：{e}")
        
        # 增加延迟时间，确保端口完全释放
        time.sleep(2.0)
        
        # 启动新服务器
        try:
            server_loop = asyncio.new_event_loop()
            server_thread = threading.Thread(
                target=server.start_server_thread, 
                args=(server_loop, self.update_st_callback), 
                daemon=True
            )
            server_thread.start()
            
            # 等待服务器启动完成
            time.sleep(0.5)
        except OSError as e:
            print(f"启动服务器失败：{e}")
            self.status.config(text=f"● 端口被占用，请更换端口", foreground="red")
            self.root.after(3000, lambda: self.status.config(text="● 等待手机连接...", foreground="red"))

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