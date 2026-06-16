from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import html
import re

HOST = "127.0.0.1"
PORT = 8890

def analyze_text(text):
    clean = text.strip()
    length = len(clean)

    keywords = []
    keyword_candidates = [
        "AI Agent", "Agent", "Python", "Linux", "Docker", "Nginx",
        "systemd", "云服务器", "部署", "GitHub", "Halo", "LLM",
        "工具调用", "工作流", "自动化"
    ]

    for word in keyword_candidates:
        if word.lower() in clean.lower():
            keywords.append(word)

    if not keywords:
        keywords = ["技术实践", "项目复盘"]

    summary = clean[:120] + ("..." if length > 120 else "")

    title = "技术实践复盘：" + (keywords[0] if keywords else "项目记录")

    checklist = [
        "标题是否清晰表达文章主题",
        "是否说明项目背景和目标",
        "是否包含关键技术栈",
        "是否记录遇到的问题和解决过程",
        "是否附上 Demo、源码或相关链接",
        "是否避免暴露密码、密钥和服务器敏感信息"
    ]

    return title, summary, keywords[:6], checklist, length

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        page = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Blog Content Agent Demo</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f5f7fb;
      color: #111827;
      margin: 0;
      padding: 40px;
      line-height: 1.7;
    }
    main {
      max-width: 960px;
      margin: 0 auto;
    }
    .card {
      background: white;
      border-radius: 18px;
      padding: 24px;
      margin: 20px 0;
      box-shadow: 0 12px 36px rgba(15, 23, 42, 0.08);
    }
    textarea {
      width: 100%;
      min-height: 220px;
      padding: 16px;
      border-radius: 12px;
      border: 1px solid #cbd5e1;
      font-size: 16px;
      line-height: 1.6;
    }
    button {
      margin-top: 16px;
      padding: 10px 18px;
      border: 0;
      border-radius: 999px;
      background: #2563eb;
      color: white;
      font-size: 16px;
      cursor: pointer;
    }
    .tag {
      display: inline-block;
      background: #dbeafe;
      color: #1d4ed8;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 14px;
      margin-right: 8px;
      margin-bottom: 8px;
    }
  </style>
</head>
<body>
  <main>
    <h1>Blog Content Agent Demo</h1>
    <p class="tag">AI Agent 实践项目 · 博客内容工作流方向</p>
    <p>输入文章草稿，Agent 会生成标题建议、摘要、标签和发布检查清单。</p>

    <div class="card">
      <form method="POST">
        <textarea name="content" placeholder="请粘贴你的文章草稿，例如项目复盘、技术笔记、部署记录..."></textarea>
        <br>
        <button type="submit">生成内容建议</button>
      </form>
    </div>
  </main>
</body>
</html>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)
        content = data.get("content", [""])[0]

        title, summary, tags, checklist, text_length = analyze_text(content)

        tags_html = "".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in tags)
        checklist_html = "".join(f"<li>{html.escape(item)}</li>" for item in checklist)

        page = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Blog Content Agent Result</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f5f7fb;
      color: #111827;
      margin: 0;
      padding: 40px;
      line-height: 1.7;
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
    }}
    .card {{
      background: white;
      border-radius: 18px;
      padding: 24px;
      margin: 20px 0;
      box-shadow: 0 12px 36px rgba(15, 23, 42, 0.08);
    }}
    .tag {{
      display: inline-block;
      background: #dbeafe;
      color: #1d4ed8;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 14px;
      margin-right: 8px;
      margin-bottom: 8px;
    }}
    a {{
      color: #2563eb;
      text-decoration: none;
      font-weight: 600;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Blog Content Agent Demo</h1>

    <div class="card">
      <h2>Agent 分析结果</h2>
      <p><strong>文章长度：</strong>{text_length} 字符</p>
      <p><strong>标题建议：</strong>{html.escape(title)}</p>
      <p><strong>摘要：</strong>{html.escape(summary)}</p>
      <p><strong>推荐标签：</strong></p>
      <p>{tags_html}</p>
    </div>

    <div class="card">
      <h2>发布检查清单</h2>
      <ul>
        {checklist_html}
      </ul>
    </div>

    <p><a href="/">返回重新输入</a></p>
  </main>
</body>
</html>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Blog Content Agent running at http://{HOST}:{PORT}")
    server.serve_forever()
