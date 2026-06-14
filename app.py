import io
import os
import json
import base64
import urllib.parse
import anthropic
from flask import Flask, request, send_file, render_template_string, Response, jsonify

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
    textarea { height: 80px; resize: vertical; }
    .row { display: flex; gap: 12px; }
    .row > div { flex: 1; }
    button.generate { margin-top: 24px; width: 100%; padding: 14px; background: #7ec8e3; color: #1a1a2e; border: none; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; font-family: inherit; }
    button.generate:hover { background: #5bb8d4; }
    button.generate:disabled { background: #4a6a7a; color: #888; cursor: not-allowed; }
    .tip { margin-top: 16px; font-size: 12px; color: #666; text-align: center; }
    .loading { display: none; text-align: center; margin-top: 16px; color: #7ec8e3; font-size: 14px; }
    .error { display: none; margin-top: 16px; padding: 12px; background: #3a1a1a; border-radius: 8px; color: #e88; font-size: 13px; }
    .preview { display: none; margin-top: 16px; padding: 12px; background: #1a3a1a; border-radius: 8px; font-size: 13px; color: #8e8; }
    .img-upload { border: 2px dashed #2a4a7a; border-radius: 8px; padding: 20px; text-align: center; cursor: pointer; color: #aaa; font-size: 13px; margin-top: 6px; }
    .img-upload:hover { border-color: #7ec8e3; }
    .img-preview { margin-top: 10px; max-width: 100%; border-radius: 8px; display: none; }
  </style>
</head>
<body>
  <h1>⛏ MC 建築產生器</h1>
  <p class="sub">輸入需求，自動生成 .litematic 檔案</p>
  <div class="card">
    <div class="tabs">
      <button class="tab active" onclick="switchTab('ai', this)">AI 描述生成</button>
      <button class="tab" onclick="switchTab('img', this)">圖片生成</button>
      <button class="tab" onclick="switchTab('manual', this)">手動設定</button>
    </div>

    <!-- AI 描述模式 -->
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

    <!-- 圖片模式 -->
    <div class="panel" id="panel-img">
      <label>建築名稱</label>
      <input type="text" id="img-name" placeholder="我的建築" value="我的建築">
      <label>上傳建築圖片</label>
      <div class="img-upload" id="img-drop" onclick="document.getElementById('img-file').click()">
        點擊或拖曳上傳圖片
        <input type="file" id="img-file" accept="image/*" style="display:none" onchange="previewImg(this)">
      </div>
      <img class="img-preview" id="img-preview-el">
      <label>補充說明（選填）</label>
      <textarea id="img-hint" placeholder="例如：參考這張圖，做石頭風格，大小約12x12"></textarea>
      <div class="preview" id="img-preview-text"></div>
      <div class="error" id="img-error"></div>
      <div class="loading" id="img-loading">AI 正在分析圖片...</div>
      <button class="generate" id="img-btn" onclick="generateImg()">圖片分析並下載 .litematic</button>
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
function switchTab(tab, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + tab).classList.add('active');
  el.classList.add('active');
}

function previewImg(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const el = document.getElementById('img-preview-el');
    el.src = e.target.result;
    el.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

// 拖曳上傳
const drop = document.getElementById('img-drop');
drop.addEventListener('dragover', e => { e.preventDefault(); drop.style.borderColor = '#7ec8e3'; });
drop.addEventListener('dragleave', () => { drop.style.borderColor = '#2a4a7a'; });
drop.addEventListener('drop', e => {
  e.preventDefault();
  drop.style.borderColor = '#2a4a7a';
  const file = e.dataTransfer.files[0];
  if (file) {
    document.getElementById('img-file').files = e.dataTransfer.files;
    previewImg({ files: [file] });
  }
});

async function generateAI() {
  const name = document.getElementById('ai-name').value || '我的建築';
  const desc = document.getElementById('ai-desc').value.trim();
  if (!desc) { alert('請輸入建築描述！'); return; }
  await callGenerate('/ai-generate', { name, description: desc }, 'ai');
}

async function generateImg() {
  const name = document.getElementById('img-name').value || '我的建築';
  const fileInput = document.getElementById('img-file');
  const hint = document.getElementById('img-hint').value.trim();
  if (!fileInput.files[0]) { alert('請上傳圖片！'); return; }

  const reader = new FileReader();
  reader.onload = async e => {
    const b64 = e.target.result.split(',')[1];
    const mediaType = fileInput.files[0].type;
    await callGenerate('/img-generate', { name, image_b64: b64, media_type: mediaType, hint }, 'img');
  };
  reader.readAsDataURL(fileInput.files[0]);
}

async function callGenerate(url, body, prefix) {
  const btn = document.getElementById(prefix + '-btn');
  const loading = document.getElementById(prefix + '-loading');
  const error = document.getElementById(prefix + '-error');
  const preview = document.getElementById(prefix + '-preview' + (prefix === 'ai' ? '' : '-text'));

  btn.disabled = true;
  loading.style.display = 'block';
  error.style.display = 'none';
  if (preview) preview.style.display = 'none';

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || '生成失敗');
    }

    const blob = await res.blob();
    const dlUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = dlUrl;
    a.download = (body.name || '建築') + '.litematic';
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

BUILDING_PROMPT = """你是一個 Minecraft 建築參數解析器。
根據以下{source}，回傳 JSON 格式的建築參數。

{content}

請回傳以下 JSON（只回傳 JSON，不要其他文字）：
{{
  "style": "木頭或石頭或深板岩或沙岩或雲杉（選最符合的）",
  "width": 數字（6-20）,
  "length": 數字（6-20）,
  "height": 數字（4-10）,
  "towers": true或false（是否有角塔）
}}"""

def build_and_send(params, name):
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
    safe_name = urllib.parse.quote(name + ".litematic")
    response = Response(buf.read(), mimetype="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{safe_name}"
    return response

def parse_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

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
    safe_name = urllib.parse.quote(name + ".litematic")
    response = Response(buf.read(), mimetype="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{safe_name}"
    return response

@app.route("/ai-generate", methods=["POST"])
def ai_generate():
    data = request.get_json()
    name = data.get("name", "我的建築")
    description = data.get("description", "")

    prompt = BUILDING_PROMPT.format(
        source="玩家描述",
        content=f"玩家描述：{description}"
    )
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    params = parse_json(message.content[0].text)
    return build_and_send(params, name)

@app.route("/img-generate", methods=["POST"])
def img_generate():
    data = request.get_json()
    name = data.get("name", "我的建築")
    image_b64 = data.get("image_b64", "")
    media_type = data.get("media_type", "image/jpeg")
    hint = data.get("hint", "")

    content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": image_b64}
        },
        {
            "type": "text",
            "text": BUILDING_PROMPT.format(
                source="圖片",
                content=f"請分析這張建築圖片。{('補充說明：' + hint) if hint else ''}"
            )
        }
    ]

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": content}]
    )
    params = parse_json(message.content[0].text)
    return build_and_send(params, name)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
