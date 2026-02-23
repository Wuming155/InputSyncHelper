# server.py
import asyncio
import json
import aiohttp
from aiohttp import web
from pynput import keyboard, mouse
import utils
from templates import HTML_PAGE

# 全局状态
connected_clients = set()
client_configs = {}
synced_text = ""
rebase_triggered = False  # 标记是否已触发增量模式
pending_strip_punctuation = False  # 标记重置后的第一笔输入是否剔除标点
main_loop = None

async def handle_ws(req):
    global synced_text, rebase_triggered, pending_strip_punctuation
    ws = web.WebSocketResponse()
    await ws.prepare(req)
    connected_clients.add(ws)
    
    # 通知桌面UI连接状态
    if req.app.get('ui_callback'):
        req.app['ui_callback'](True)

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                
                # 处理配置（如键盘检测开关）
                if data.get('type') == 'config':
                    client_configs[ws] = {'detect_keyboard': data.get('detectKeyboard')}
                
                # 核心同步逻辑
                elif data.get('type') == 'diff':
                    new_txt = data.get('newText', '')
                    d_cnt, add_txt = utils.compute_diff(synced_text, new_txt)
                    
                    # 【安全锁定】如果刚才电脑介入过，本次输入强制不退格
                    if rebase_triggered:
                        d_cnt = 0
                        rebase_triggered = False
                    
                    # 处理语音输入法自动带出的首位标点
                    if pending_strip_punctuation and d_cnt == 0 and add_txt:
                        punc = "，。、；：？！\"\"''·…—～,.;:?!'\""
                        if add_txt[0] in punc: 
                            add_txt = add_txt[1:]
                        pending_strip_punctuation = False
                    
                    # 执行电脑端操作
                    if d_cnt: 
                        utils.send_backspaces(d_cnt)
                    if add_txt: 
                        utils.type_text(add_txt)
                    
                    synced_text = new_txt
                
                # 处理手动重置
                elif data.get('type') == 'reset':
                    synced_text = ""
                    pending_strip_punctuation = True
                    rebase_triggered = False

    finally:
        connected_clients.discard(ws)
        if ws in client_configs: del client_configs[ws]
        if not connected_clients and req.app.get('ui_callback'):
            req.app['ui_callback'](False)
    return ws

def start_server_thread(loop, ui_callback):
    global main_loop
    main_loop = loop
    asyncio.set_event_loop(loop)
    
    app = web.Application()
    app['ui_callback'] = ui_callback
    app.router.add_get('/', lambda r: web.Response(text=HTML_PAGE, content_type='text/html'))
    app.router.add_get('/ws', handle_ws)
    
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    loop.run_until_complete(web.TCPSite(runner, '0.0.0.0', 5000).start())
    
    # --- 智能感知：监听电脑动作 ---
    def reset_synced_text():
        global synced_text, rebase_triggered, pending_strip_punctuation
        if utils.is_typing() or not connected_clients: return
        
        # 只要动了电脑，就重置后端状态并通知手机锁定锚点
        if synced_text and any(c.get('detect_keyboard') for c in client_configs.values()):
            synced_text = ""
            rebase_triggered = True
            pending_strip_punctuation = True
            for ws in list(connected_clients):
                if not ws.closed:
                    asyncio.run_coroutine_threadsafe(ws.send_json({'type': 'rebase'}), loop)

    # 监听键盘（仅限字符输入）和鼠标左键
    keyboard.Listener(on_press=lambda k: reset_synced_text() if hasattr(k, 'char') else None).start()
    mouse.Listener(on_click=lambda x,y,b,p: reset_synced_text() if p and b==mouse.Button.left else None).start()
    
    loop.run_forever()