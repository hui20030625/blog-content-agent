from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import html
import re
import os

HOST = "127.0.0.1"
PORT = 8890




def get_llm_config():
    """
    读取 LLM 配置。
    当前只读取配置，不调用外部 API。
    注意：不要把 LLM_API_KEY 输出到页面或日志。
    """
    enabled = os.getenv("ENABLE_LLM", "false").lower() == "true"
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "")
    api_key = os.getenv("LLM_API_KEY", "")

    return {
        "enabled": enabled,
        "provider": provider,
        "model": model,
        "api_key_configured": bool(api_key),
    }


# =========================
# 基础工具函数
# =========================

def is_public_ipv4(ip):
    parts = ip.split(".")
    if len(parts) != 4:
        return False

    try:
        nums = [int(x) for x in parts]
    except ValueError:
        return False

    if any(n < 0 or n > 255 for n in nums):
        return False

    if nums[0] == 10:
        return False
    if nums[0] == 127:
        return False
    if nums[0] == 192 and nums[1] == 168:
        return False
    if nums[0] == 172 and 16 <= nums[1] <= 31:
        return False

    return True


# =========================
# Agent Tools
# =========================

def tool_recommend_tags(text):
    """根据文章内容推荐标签"""
    keyword_candidates = [
        "AI Agent", "Agent", "Python", "Linux", "Docker", "Nginx",
        "systemd", "云服务器", "部署", "GitHub", "Halo", "LLM",
        "工具调用", "工作流", "自动化", "MCP", "RAG", "博客", "写作"
    ]

    tags = []
    for word in keyword_candidates:
        if word.lower() in text.lower():
            tags.append(word)

    if not tags:
        tags = ["技术实践", "项目复盘"]

    return tags[:6]


def tool_generate_title(text, tags):
    """根据内容和标签生成标题建议"""
    if "博客" in text or "文章" in text or "写作" in text:
        return "技术实践复盘：博客内容助手 Agent"

    if "部署" in text or "Nginx" in text or "systemd" in text:
        main = tags[0] if tags else "项目部署"
        return f"技术实践复盘：{main} 部署"

    main = tags[0] if tags else "项目记录"
    return f"技术实践复盘：{main}"


def tool_generate_summary(text, tags):
    """生成概括性摘要，而不是简单截断原文"""
    clean = re.sub(r"\s+", " ", text).strip()

    if not clean:
        return "暂无文章内容，建议先补充项目背景、实现过程和复盘总结。"

    topic_text = "、".join(tags[:3]) if tags else "技术实践"

    points = []

    if any(x in clean for x in ["部署", "Nginx", "systemd", "云服务器", "Docker"]):
        points.append("部署流程")

    if any(x in clean for x in ["Agent", "工具调用", "工作流", "自动化"]):
        points.append("Agent 工作流")

    if any(x in clean for x in ["问题", "报错", "解决", "排查"]):
        points.append("问题排查")

    if any(x in clean for x in ["博客", "文章", "摘要", "标签", "发布"]):
        points.append("内容发布流程")

    if any(x in clean.lower() for x in ["password", "token", "secret", "api_key", "密钥", "密码"]):
        points.append("发布前敏感信息检查")

    if not points:
        points.append("项目实现过程")

    point_text = "、".join(points[:3])
    return f"本文围绕 {topic_text} 展开，主要记录{point_text}，用于整理技术实践并辅助后续复盘。"


def tool_check_sensitive_info(text):
    """检查文章草稿中可能存在的敏感信息"""
    findings = []

    patterns = [
        ("密码相关关键词", r"\b(password|passwd|pwd)\b|密码"),
        ("Token / API Key / Secret 关键词", r"\b(token|api[_-]?key|access[_-]?key|secret)\b|密钥"),
        ("私钥内容", r"BEGIN\s+(RSA\s+|OPENSSH\s+)?PRIVATE\s+KEY"),
        (".env 配置文件", r"\.env"),
        ("服务器敏感路径", r"(/root/|/etc/nginx/|/etc/systemd/|/opt/agent-lab/)"),
        ("SSH 相关内容", r"(ssh-rsa|ssh-ed25519|authorized_keys)"),
    ]

    for label, pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(label)

    ipv4_candidates = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    public_ips = sorted({ip for ip in ipv4_candidates if is_public_ipv4(ip)})

    if public_ips:
        findings.append("疑似公网 IP：" + "、".join(public_ips[:3]))

    unique_findings = []
    for item in findings:
        if item not in unique_findings:
            unique_findings.append(item)

    if unique_findings:
        return {
            "level": "需要注意",
            "items": unique_findings,
            "suggestion": "建议发布前删除、替换或脱敏上述内容。"
        }

    return {
        "level": "未发现明显敏感信息",
        "items": ["未发现明显密码、密钥、公网 IP 或服务器敏感路径。"],
        "suggestion": "发布前仍建议人工复查。"
    }


def tool_generate_publish_checklist():
    """生成发布前检查清单"""
    return [
        "标题是否清晰表达文章主题",
        "是否说明项目背景和目标",
        "是否包含关键技术栈",
        "是否记录遇到的问题和解决过程",
        "是否附上 Demo、源码或相关链接",
        "是否避免暴露密码、密钥和服务器敏感信息"
    ]


# =========================
# Agent 编排逻辑
# =========================

def is_meaningful_content(text):
    """
    判断输入是否像一段可分析的文章草稿。
    规则：
    1. 至少有一定长度
    2. 需要包含中文或英文字母
    3. 不能只是数字、符号或极短文本
    """
    clean = text.strip()
    meaningful_chars = re.findall(r"[\u4e00-\u9fffA-Za-z]", clean)

    if len(clean) < 20:
        return False

    if len(meaningful_chars) < 10:
        return False

    return True


def run_blog_content_agent(text):
    """
    这里模拟一个简单 Agent 的工作流：
    先判断输入是否有效，再调用标签、标题、摘要、敏感信息检查和发布检查工具。
    后续可以把这里替换成 LLM + tool calling。
    """
    clean = text.strip()
    trace = []

    trace.append("接收文章草稿")

    llm_config = get_llm_config()
    if llm_config["enabled"]:
        trace.append("读取 LLM 配置：ENABLE_LLM=true，后续可接入大模型生成标题和摘要")
    else:
        trace.append("读取 LLM 配置：ENABLE_LLM=false，当前使用规则型工具流程")

    security = tool_check_sensitive_info(clean)
    checklist = tool_generate_publish_checklist()

    if not is_meaningful_content(clean):
        trace.append("调用 input_validation：输入内容不足，停止生成标题、摘要和标签")
        trace.append("调用 tool_check_sensitive_info：仍然执行敏感信息检查")
        trace.append("调用 tool_generate_publish_checklist：生成基础发布检查清单")

        return {
            "length": len(clean),
            "title": "输入内容不足，无法生成有效标题",
            "summary": "当前输入过短或缺少有效文章内容，请输入一段完整的项目复盘、技术笔记或部署记录后再生成建议。",
            "tags": ["内容不足"],
            "security": security,
            "checklist": checklist,
            "trace": trace,
            "llm_config": llm_config
        }

    tags = tool_recommend_tags(clean)
    trace.append("调用 tool_recommend_tags：生成推荐标签")

    title = tool_generate_title(clean, tags)
    trace.append("调用 tool_generate_title：生成标题建议")

    summary = tool_generate_summary(clean, tags)
    trace.append("调用 tool_generate_summary：生成概括性摘要")

    trace.append("调用 tool_check_sensitive_info：检查敏感信息")

    trace.append("调用 tool_generate_publish_checklist：生成发布检查清单")

    return {
        "length": len(clean),
        "title": title,
        "summary": summary,
        "tags": tags,
        "security": security,
        "checklist": checklist,
        "trace": trace,
        "llm_config": llm_config
    }


# =========================
# Web 页面
# =========================

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
      box-sizing: border-box;
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
    <p>输入文章草稿，Agent 会依次调用多个工具，生成标题、摘要、标签、敏感信息检查和发布检查清单。</p>

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

        result = run_blog_content_agent(content)

        tags_html = "".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in result["tags"])
        checklist_html = "".join(f"<li>{html.escape(item)}</li>" for item in result["checklist"])
        security_html = "".join(f"<li>{html.escape(item)}</li>" for item in result["security"]["items"])
        trace_html = "".join(f"<li>{html.escape(item)}</li>" for item in result["trace"])

        llm_config = result["llm_config"]
        llm_status = "已开启" if llm_config["enabled"] else "未开启"
        api_key_status = "已配置" if llm_config["api_key_configured"] else "未配置"

        security_level = result["security"]["level"]
        security_class = "warning" if security_level == "需要注意" else "safe"

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
    .safe {{
      color: #047857;
      font-weight: 700;
    }}
    .warning {{
      color: #b45309;
      font-weight: 700;
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
      <p><strong>文章长度：</strong>{result["length"]} 字符</p>
      <p><strong>标题建议：</strong>{html.escape(result["title"])}</p>
      <p><strong>摘要：</strong>{html.escape(result["summary"])}</p>
      <p><strong>推荐标签：</strong></p>
      <p>{tags_html}</p>
    </div>

    <div class="card">
      <h2>Agent 工具调用流程</h2>
      <ul>
        {trace_html}
      </ul>
    </div>

    <div class="card">
      <h2>LLM 配置状态</h2>
      <p><strong>LLM 开关：</strong>{html.escape(llm_status)}</p>
      <p><strong>Provider：</strong>{html.escape(llm_config["provider"])}</p>
      <p><strong>Model：</strong>{html.escape(llm_config["model"])}</p>
      <p><strong>API Key：</strong>{html.escape(api_key_status)}（页面不会显示密钥内容）</p>
    </div>

    <div class="card">
      <h2>敏感信息检查</h2>
      <p><strong>检查结果：</strong><span class="{security_class}">{html.escape(security_level)}</span></p>
      <ul>
        {security_html}
      </ul>
      <p><strong>建议：</strong>{html.escape(result["security"]["suggestion"])}</p>
    </div>

    <div class="card">
      <h2>发布检查清单</h2>
      <ul>
        {checklist_html}
      </ul>
    </div>

    <p><a href="./">返回重新输入</a></p>
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
