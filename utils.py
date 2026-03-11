# utils.py
import socket
import pyautogui
import pyperclip
import platform
import time
import threading
import json
import os
import sys

clipboard_lock = threading.Lock()
typing_in_progress = False
# 默认退格次数限制
backspace_limit = 100
# 默认设置
settings = {
    'ip': '192.168.10.23',  # 默认使用 192.168.10.23
    'port': 5000,
    'window_size': '350x500'
}

# 保存设置的文件
# 使用绝对路径，确保设置文件保存在应用程序根目录
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')

def load_settings():
    """加载设置"""
    global settings, backspace_limit
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                settings.update(loaded)
                if 'backspace_limit' in loaded:
                    backspace_limit = loaded['backspace_limit']
        except Exception:
            pass

def save_settings():
    """保存设置"""
    global settings, backspace_limit
    try:
        data = settings.copy()
        data['backspace_limit'] = backspace_limit
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]; s.close()
        return ip
    except: return '23.0.0.1'

def get_ip():
    """获取IP地址，优先使用用户设置的IP"""
    return settings['ip'] if settings['ip'] else get_local_ip()

def get_port():
    """获取端口号"""
    return settings['port']

def get_window_size():
    """获取窗口大小"""
    return settings['window_size']

def set_ip(ip):
    """设置IP地址"""
    global settings
    settings['ip'] = ip
    save_settings()

def set_port(port):
    """设置端口号"""
    global settings
    settings['port'] = port
    save_settings()

def set_window_size(size):
    """设置窗口大小"""
    global settings
    settings['window_size'] = size
    save_settings()

def compute_diff(old, new):
    common = 0
    for i in range(min(len(old), len(new))):
        if old[i] == new[i]: common += 1
        else: break
    return len(old) - common, new[common:]

def type_text(text):
    global typing_in_progress
    if not text: return
    typing_in_progress = True
    with clipboard_lock:
        try:
            orig = pyperclip.paste()
            pyperclip.copy(text)
            cmd = 'command' if platform.system() == 'Darwin' else 'ctrl'
            pyautogui.hotkey(cmd, 'v')
            time.sleep(0.01)
            pyperclip.copy(orig)
        except: pass
    typing_in_progress = False

def send_backspaces(count):
    global typing_in_progress
    if count <= 0: return
    # 安全阀：单词同步删除操作不允许超过设定的退格次数，防止误删电脑原生内容
    safe_count = min(count, backspace_limit)
    typing_in_progress = True
    pyautogui.press('backspace', presses=safe_count, interval=0.005) 
    typing_in_progress = False

def set_backspace_limit(limit):
    """设置退格次数限制"""
    global backspace_limit
    backspace_limit = limit
    save_settings()

# 初始化时加载设置
load_settings()

# 初始化时保存默认设置（如果文件不存在）
if not os.path.exists(SETTINGS_FILE):
    save_settings()

def is_typing():
    return typing_in_progress