import io
import os
import json
import anthropic
from flask import Flask, request, send_file, render_template_string

from builder import generate_house

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MC 建築產生器</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: "Microsoft JhengHei", "PingFang TC", sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 40px 20px; }
    h1 { font-size: 28px; margin-bottom: 8px; color: #7ec8e3; }
    p.sub { color: #aaa; margin-bottom: 32px; font-size: 14px; }
    .card { background: #16213e; border-radius: 16px; padding: 32px; width: 100%; max-width: 520px; box-shadow: 0 4px 24px rgba(0,0,0,0.4); }
    .tabs { display: flex; gap: 8px; margin-bottom: 24px; }
    .tab { flex: 1; padding: 10px; background: #0f3460; border: none; border-radius: 8px; color: #aaa; font-size: 14px; cursor: pointer; font-family: inherit; }
    .tab.active { background: #7ec8e3; color: #1a1a2e; font-weight: bold; }
    .panel { display: none; }
    .panel.active { display: block; }
    label { display: block; font-size: 13px; color: #aaa; margin-top: 16px; margin-bottom: 6px; }
    input, select, textarea { width: 100%; padding: 10px 14px; background: #0f3460; border: 1px solid #2a4a7a; border-radius: 8px; color: #eee; font-size: 14px; font-family: inherit; }
    textarea { height: 100px; resize: vertical; }
    .row { display: flex; gap: 12px; }
    .row > div { flex: 1; }
    button.generate { margin-top: 24px; width: 100%; padding: 14px; background: #7ec8e3; color: #1a1a2e; border: none; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; font-family: inherit; }
    button.generate:hover { background: #5bb8d4; }
    button.generate:disabled { background: #4a6a7a; color: #888; cursor: not-allowed; }
    .tip { margin-top: 16px; font-size: 12px; color: #666; text-align: center; }
    .loading { display: none; text-align: center; margin-top: 16px; color: #7ec8e3; font-size: 14px; }
    .error { display: none; margin-top: 16px; padding: 12px; background: #3a1a1a; border-radius: 8px; color: #e88; font-size: 13px; }
    .preview { display: none; margin-top: 16px; padding: 12px; background: #1a3a1a; border-radius: 8px; font-size: 13px; color: #8e8; }
  </style>
</head>
<body>
  <h1>⛏ MC 建築產生器</h1>
  <p class="sub">輸入需求，自動生成 .litematic 檔案</p>
  <div class="card">
    <div class="tabs">
      <button class="tab active" onclick="switchTab('ai')">AI 描述生成</button>
      <button class="tab" onclick="switchTab('manual')">手動設定</button>
    </div>

    <!-- AI 模式 -->
    <div class="panel active" id="panel-ai">
      <label>建築名稱</label>
      <input type="text" id="ai-name" placeholder="我的城堡" value="我的建築">
      <label>描述你想要的建築</label>
      <textarea id="ai-desc" placeholder="例如：我想要一個中世紀風格的石頭城堡，有四個角塔，大概15x15大小，高度8層"></textarea>
      <div class="preview" id="ai-preview"></div>
      <div class="error" id="ai-error"></div>
      <div class="loading" id="ai-loading">AI 正在解讀你的描述...</div>
      <button class="generate" id="ai-btn" onclick="generateAI()">AI 生成並下載 .litematic</button>
    </div>

    <!-- 手動模式 -->
    <div class="panel" id="panel-manual">
      <form method="POST" action="/generate">
        <label>建築名稱</label>
        <input type="text" name="name" placeholder="我的房子" value="我的房子">
        <label>建築風格（材料）</label>
        <select name="style">
          <option value="木頭">木頭</option>
          <option value="石頭">石頭</option>
          <option value="深板岩">深板岩</option>
          <option value="沙岩">沙岩</option>
          <option value="雲杉">雲杉木</option>
        </select>
        <label>尺寸（最小 6，最大 20）</label>
        <div class="row">
          <div><label>寬度</label><input type="number" name="width" value="10" min="6" max="20"></div>
          <div><label>長度</label><input type="number" name="length" value="10" min="6" max="20"></div>
          <div><label>高度</label><input type="number" name="height" value="6" min="4" max="10"></div>
        </div>
        <label><input type="checkbox" name="towers" value="1" style="width:auto;margin-right:6px">加入角塔</label>
        <button type="submit" class="generate">生成並下載 .litematic</button>
      </form>
    </div>

    <p class="tip">下載後放入 Minecraft 的 schematics 資料夾，用 Litematica 模組載入</p>
  </div>

<script>
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + tab).classList.add('active');
  event.target.classList.add('active');
}

async function generateAI() {
  const name = document.getElementById('ai-name').value || '我的建築';
  const desc = document.getElementById('ai-desc').value.trim();
  if (!desc) { alert('請輸入建築描述！'); return; }

  const btn = document.getElementById('ai-btn');
  const loading = document.getElementById('ai-loading');
  const error = document.getElementById('ai-error');
  const preview = document.getElementById('ai-preview');

  btn.disabled = true;
  loading.style.display = 'block';
  error.style.display = 'none';
  preview.style.display = 'none';

  try {
    const res = await fetch('/ai-generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description: desc })
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || '生成失敗');
    }

    const info = res.headers.get('X-Building-Info');
    if (info) {
      preview.textContent = '生成參數：' + decodeURIComponent(info);
      preview.style.display = 'block';
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name + '.litematic';
    a.click();
  } catch (e) {
    error.textContent = '錯誤：' + e.message;
    error.style.display = 'block';
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/generate", methods=["POST"])
def generate():
    name   = request.form.get("name", "建築") or "建築"
    style  = request.form.get("style", "木頭")
    width  = int(request.form.get("width", 10))
    length = int(request.form.get("length", 10))
    height = int(request.form.get("height", 6))
    towers = request.form.get("towers") == "1"

    schem = generate_house(style=style, width=width, length=length, height=height, name=name, towers=towers)
    buf = io.BytesIO()
    schem.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{name}.litematic", mimetype="application/octet-stream")

@app.route("/ai-generate", methods=["POST"])
def ai_generate():
    from flask import jsonify
    data = request.get_json()
    name = data.get("name", "我的建築")
    description = data.get("description", "")

    prompt = f"""你是一個 Minecraft 建築參數解析器。
根據以下玩家描述，回傳 JSON 格式的建築參數。

玩家描述：{description}

請回傳以下 JSON（只回傳 JSON，不要其他文字）：
{{
  "style": "木頭或石頭或深板岩或沙岩或雲杉（選最符合的）",
  "width": 數字（6-20）,
  "length": 數字（6-20）,
  "height": 數字（4-10）,
  "towers": true或false（是否有角塔）,
  "summary": "一句話描述這個建築"
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    params = json.loads(raw)

    schem = generate_house(
        style=params.get("style", "木頭"),
        width=params.get("width", 10),
        length=params.get("length", 10),
        height=params.get("height", 6),
        name=name,
        towers=params.get("towers", False)
    )

    buf = io.BytesIO()
    schem.save(buf)
    buf.seek(0)

    import urllib.parse
    from flask import Response
    safe_name = urllib.parse.quote(name + ".litematic")
    response = Response(buf.read(), mimetype="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{safe_name}"
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
