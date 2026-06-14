import io
import os
from flask import Flask, request, send_file, render_template_string

from builder import generate_house

app = Flask(__name__)

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
    .card { background: #16213e; border-radius: 16px; padding: 32px; width: 100%; max-width: 480px; box-shadow: 0 4px 24px rgba(0,0,0,0.4); }
    label { display: block; font-size: 13px; color: #aaa; margin-top: 16px; margin-bottom: 6px; }
    input, select { width: 100%; padding: 10px 14px; background: #0f3460; border: 1px solid #2a4a7a; border-radius: 8px; color: #eee; font-size: 14px; font-family: inherit; }
    .row { display: flex; gap: 12px; }
    .row > div { flex: 1; }
    button { margin-top: 24px; width: 100%; padding: 14px; background: #7ec8e3; color: #1a1a2e; border: none; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; font-family: inherit; }
    button:hover { background: #5bb8d4; }
    .tip { margin-top: 20px; font-size: 12px; color: #666; text-align: center; }
  </style>
</head>
<body>
  <h1>⛏ MC 建築產生器</h1>
  <p class="sub">輸入需求，自動生成 .litematic 檔案</p>
  <div class="card">
    <form method="POST" action="/generate">
      <label>建築名稱</label>
      <input type="text" name="name" placeholder="我的房子" value="我的房子">

      <label>建築風格（材料）</label>
      <select name="style">
        <option value="木頭">木頭</option>
        <option value="石頭">石頭</option>
        <option value="深板岩">深板岩</option>
        <option value="沙岩">沙岩</option>
      </select>

      <label>尺寸（最小 6，最大 20）</label>
      <div class="row">
        <div>
          <label>寬度</label>
          <input type="number" name="width" value="10" min="6" max="20">
        </div>
        <div>
          <label>長度</label>
          <input type="number" name="length" value="10" min="6" max="20">
        </div>
        <div>
          <label>高度</label>
          <input type="number" name="height" value="6" min="4" max="10">
        </div>
      </div>

      <button type="submit">生成並下載 .litematic</button>
    </form>
    <p class="tip">下載後放入 Minecraft 的 schematics 資料夾，用 Litematica 模組載入</p>
  </div>
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

    schem = generate_house(style=style, width=width, length=length, height=height, name=name)

    buf = io.BytesIO()
    schem.save(buf)
    buf.seek(0)

    filename = f"{name}.litematic"
    return send_file(buf, as_attachment=True, download_name=filename, mimetype="application/octet-stream")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
