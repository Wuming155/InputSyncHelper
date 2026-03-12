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
# 默认智能感知开关
smart_detection = True
# 默认自动清空开关
auto_clear = False
# 默认自动清空时间（秒）
auto_clear_time = 15
# 默认设置
settings = {
    'ip': '',  # 默认自动获取局域网 IP
    'port': 5000,
    'window_size': '350x500',
    'settings_window_size': '400x300',
    'smart_detection': True,
    'auto_clear': False,
    'auto_clear_time': 15
}

# 保存设置的文件
# 使用绝对路径，确保设置文件保存在应用程序根目录
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')

def load_settings():
    """加载设置"""
    global settings, backspace_limit, smart_detection, auto_clear, auto_clear_time
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                settings.update(loaded)
                if 'backspace_limit' in loaded:
                    backspace_limit = loaded['backspace_limit']
                if 'smart_detection' in loaded:
                    smart_detection = loaded['smart_detection']
                if 'auto_clear' in loaded:
                    auto_clear = loaded['auto_clear']
                if 'auto_clear_time' in loaded:
                    auto_clear_time = loaded['auto_clear_time']
        except Exception:
            pass

def save_settings():
    """保存设置"""
    global settings, backspace_limit, smart_detection, auto_clear, auto_clear_time
    try:
        data = settings.copy()
        data['backspace_limit'] = backspace_limit
        data['smart_detection'] = smart_detection
        data['auto_clear'] = auto_clear
        data['auto_clear_time'] = auto_clear_time
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

def get_smart_detection():
    """获取智能感知开关状态"""
    global smart_detection
    return smart_detection

def set_smart_detection(enabled):
    """设置智能感知开关状态"""
    global smart_detection
    smart_detection = enabled
    save_settings()

def get_auto_clear():
    """获取自动清空开关状态"""
    global auto_clear
    return auto_clear

def set_auto_clear(enabled):
    """设置自动清空开关状态"""
    global auto_clear
    auto_clear = enabled
    save_settings()

def get_auto_clear_time():
    """获取自动清空时间"""
    global auto_clear_time
    return auto_clear_time

def set_auto_clear_time(time):
    """设置自动清空时间"""
    global auto_clear_time
    auto_clear_time = time
    save_settings()

def get_settings_window_size():
    """获取设置窗口大小"""
    return settings.get('settings_window_size', '400x300')

def set_settings_window_size(size):
    """设置设置窗口大小"""
    global settings
    settings['settings_window_size'] = size
    save_settings()

# 初始化时加载设置
load_settings()

# 初始化时保存默认设置（如果文件不存在）
if not os.path.exists(SETTINGS_FILE):
    save_settings()

def is_typing():
    return typing_in_progress