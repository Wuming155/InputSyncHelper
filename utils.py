# utils.py
import socket
import pyautogui
import pyperclip
import platform
import time
import threading


clipboard_lock = threading.Lock()
typing_in_progress = False

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]; s.close()
        return ip
    except: return '127.0.0.1'

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
    typing_in_progress = True
    # 优化：pyautogui 支持一次性发送多个按键，速度比循环快得多
    pyautogui.press('backspace', presses=count, interval=0.005) 
    typing_in_progress = False

def is_typing():
    return typing_in_progress