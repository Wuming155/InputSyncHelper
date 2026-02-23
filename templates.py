# templates.py
HTML_PAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <style>
        :root { --bg: #F2F2F7; --card: #FFFFFF; --accent: #007AFF; --danger: #FF3B30; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, sans-serif; background: var(--bg); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        .nav { display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; background: #fff; border-bottom: 1px solid #e5e5e5; }
        .status-box { display: flex; align-items: center; gap: 6px; }
        .status-dot { width: 8px; height: 8px; background: #ff3b30; border-radius: 50%; }
        .status-dot.on { background: #4CD964; box-shadow: 0 0 5px #4CD964; }
        .status-text { font-size: 14px; color: #333; font-weight: 500; }
        .set-btn { padding: 4px 12px; border-radius: 6px; border: 1px solid #ddd; background: #f9f9f9; font-size: 13px; color: #666; }
        .paper { flex: 1; position: relative; background: #fff; display: flex; flex-direction: column; }
        textarea { flex: 1; border: none; outline: none; padding: 16px; font-size: 18px; line-height: 1.6; resize: none; width: 100%; }
        .bottom-bar { padding: 10px 16px calc(10px + env(safe-area-inset-bottom)); background: #fff; border-top: 1px solid #f2f2f2; }
        .clear-btn { 
            width: 100%; padding: 12px; border-radius: 10px; border: none;
            background: #FFF0F0; color: var(--danger); font-size: 15px; font-weight: 600;
            display: flex; align-items: center; justify-content: center; gap: 8px;
        }
        .info-row { display: flex; justify-content: space-between; padding: 4px 5px; font-size: 11px; color: #999; }
        .modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: none; align-items: center; justify-content: center; z-index: 100; }
        .modal-content { background: white; padding: 24px; border-radius: 20px; width: 85%; max-width: 300px; }
        .row { display: flex; justify-content: space-between; margin-bottom: 20px; align-items: center; }
        .close-btn { width: 100%; padding: 12px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="nav">
        <div class="status-box">
            <div class="status-dot" id="dot"></div>
            <span class="status-text" id="st">未连接</span>
        </div>
        <button class="set-btn" onclick="openM()">设置</button>
    </div>
    <div class="paper">
        <textarea id="tx" placeholder="在此输入，电脑端自动同步..." autofocus></textarea>
        <div class="info-row" style="padding: 5px 16px;">
            <span id="st_detail">实时同步中</span>
            <span id="count">已同步 0 字</span>
        </div>
    </div>
    <div class="bottom-bar">
        <button class="clear-btn" onclick="clearText()">清空输入记录</button>
    </div>
    <div class="modal" id="md">
        <div class="modal-content">
            <h3 style="margin-bottom:20px;">同步设置</h3>
            <div class="row"><span>发送延迟(ms)</span><input type="number" id="dly" value="300" style="width:60px"></div>
            <div class="row"><span>键盘检测</span><input type="checkbox" id="kb" checked></div>
            <button class="close-btn" onclick="closeM()">完成</button>
        </div>
    </div>
    <script>
        const tx = document.getElementById('tx'), st = document.getElementById('st'), 
              dot = document.getElementById('dot'), count = document.getElementById('count');
        let ws, lastText = '', total = 0, ignoreLen = 0, timer;

        function openM(){ document.getElementById('md').style.display='flex'; }
        function closeM(){ document.getElementById('md').style.display='none'; save(); }
        function save(){ localStorage.setItem('cfg', JSON.stringify({d:document.getElementById('dly').value, k:document.getElementById('kb').checked})); syncCfg(); }
        function syncCfg(){ if(ws?.readyState===1) ws.send(JSON.stringify({type:'config', detectKeyboard:document.getElementById('kb').checked})); }
        
        function connect(){
            ws = new WebSocket(`ws://${location.host}/ws`);
            ws.onopen = () => { st.innerText='已连接'; dot.className='status-dot on'; syncCfg(); };
            ws.onclose = () => { st.innerText='已断开'; dot.className='status-dot'; setTimeout(connect, 2000); };
            ws.onmessage = (e) => {
                const d = JSON.parse(e.data);
                if(d.type==='rebase'){ 
                    ignoreLen = tx.value.length; 
                    lastText = ''; 
                    st.innerText='电脑端已介入'; 
                    setTimeout(()=>st.innerText='已连接', 1500); 
                }
            };
        }
        tx.oninput = () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                const effective = tx.value.substring(ignoreLen);
                if(effective === lastText) return;
                if(ws?.readyState===1){
                    ws.send(JSON.stringify({type:'diff', oldText:lastText, newText:effective}));
                    total += (effective.length - lastText.length);
                    count.innerText = `已同步 ${total} 字`;
                    lastText = effective;
                }
            }, document.getElementById('dly').value);
        };
        function clearText(){ 
            if(confirm('确定要清空输入记录吗？')){
                tx.value=''; lastText=''; ignoreLen=0; 
                if(ws?.readyState===1) ws.send(JSON.stringify({type:'reset'})); 
            }
        }
        connect();
    </script>
</body>
</html>
"""