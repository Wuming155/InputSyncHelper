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
# 智能感知始终开启
smart_detection = True
# 默认自动清空开关
auto_clear = False
# 默认自动清空时间（秒）
auto_clear_time = 15
# 默认设置
settings = {
    'ip': '',  # 默认自动获取局域网 IP
    'port': 5000,
    'auto_clear': False,
    'auto_clear_time': 15
}

# 保存设置的文件
# 使用用户数据目录，确保打包后有写入权限
def get_settings_path():
    """获取配置文件路径，兼容 PyInstaller 打包"""
    app_name = "InputSyncHelper"
    
    try:
        if platform.system() == 'Windows':
            # Windows: 强制使用 APPDATA 目录，避免权限问题
            base_dir = os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))
        elif platform.system() == 'Darwin':
            # macOS: 使用 Application Support 目录
            base_dir = os.path.expanduser('~/Library/Application Support')
        else:
            # Linux: 使用 XDG 配置目录
            base_dir = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        
        app_dir = os.path.join(base_dir, app_name)
        
        # 确保目录存在
        try:
            if not os.path.exists(app_dir):
                os.makedirs(app_dir, exist_ok=True)
        except Exception:
            # 如果连家目录都没权限，最后保命措施：使用当前目录
            return "settings.json"
            
        return os.path.join(app_dir, 'settings.json')
    except Exception:
        # 极端情况下，使用当前目录
        return "settings.json"

# 确保 SETTINGS_FILE 在加载前已经确定
SETTINGS_FILE = get_settings_path()

def get_old_settings_path():
    """获取旧的配置文件路径（程序目录）"""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'settings.json')
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')

def migrate_old_settings():
    """迁移旧的配置文件到新位置"""
    old_path = get_old_settings_path()
    # 如果旧文件存在且新文件不存在，则迁移
    if os.path.exists(old_path) and not os.path.exists(SETTINGS_FILE):
        try:
            import shutil
            shutil.copy2(old_path, SETTINGS_FILE)
            print(f"配置文件已迁移到：{SETTINGS_FILE}")
            return True
        except Exception as e:
            print(f"迁移失败：{e}")
            return False
    return False

def load_settings():
    """加载设置"""
    global settings, backspace_limit, smart_detection, auto_clear, auto_clear_time
    
    # 先尝试迁移旧配置
    migrate_old_settings()
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                settings.update(loaded)
                
                # 只有当 JSON 里有值时才覆盖，否则保留默认
                backspace_limit = loaded.get('backspace_limit', backspace_limit)
                smart_detection = loaded.get('smart_detection', smart_detection)
                auto_clear = loaded.get('auto_clear', auto_clear)
                auto_clear_time = loaded.get('auto_clear_time', auto_clear_time)
            print(f"成功加载：{SETTINGS_FILE}")
        except Exception as e:
            print(f"读取配置异常：{e}")
    else:
        print(f"配置文件不存在：{SETTINGS_FILE}，将使用默认设置")

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
        print(f"设置已保存到：{SETTINGS_FILE}")
    except Exception as e:
        print(f"保存设置失败：{e}")
        print(f"配置文件路径：{SETTINGS_FILE}")

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

def compute_diff(old, new):
    common = 0
    for i in range(min(len(old), len(new))):
        if old[i] == new[i]: common += 1
        else: break
    return len(old) - common, new[common:]

def type_text(text):
    """使用剪贴板方式输入文本"""
    global typing_in_progress
    if not text: return
    typing_in_progress = True
    with clipboard_lock:
        try:
            pyperclip.copy(text)
            cmd = 'command' if platform.system() == 'Darwin' else 'ctrl'
            pyautogui.hotkey(cmd, 'v')
            time.sleep(0.01)
            pyperclip.copy('')
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

def get_backspace_limit():
    """获取退格次数限制"""
    global backspace_limit
    return backspace_limit

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

# 初始化时加载设置
load_settings()

# 初始化时保存默认设置（如果文件不存在）
# 注意：只有在配置文件确实不存在时才保存，避免覆盖已有配置
try:
    if not os.path.exists(SETTINGS_FILE):
        save_settings()
except Exception:
    # 如果保存失败，可能是权限问题，使用当前目录作为备选
    pass

def is_typing():
    return typing_in_progress