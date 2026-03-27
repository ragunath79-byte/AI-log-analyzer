#!/usr/bin/env python3
"""
🔍 AI Log Analyzer — Web UI
Run this and open http://localhost:5000 in your browser.
Teammates just paste their error logs and click Analyze.

Usage:
    python3 log_analyser_web.py
    python3 log_analyser_web.py --port 8080
    python3 log_analyser_web.py --host 0.0.0.0      # allow access from other machines
"""

import json
import re
import os
import sys
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# ─── Import patterns from log_analyser.py ────────────────────────────────────
try:
    from log_analyser import PATTERNS, analyze_offline
except ImportError:
    print("❌ Error: log_analyser.py must be in the same directory.")
    print("   Make sure log_analyser.py exists at:", os.path.dirname(os.path.abspath(__file__)))
    sys.exit(1)

# ─── HTML Template ───────────────────────────────────────────────────────────
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🔍 AI Log Analyzer</title>
<style>
  :root {
    --bg: #0d1117;
    --card: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --dim: #8b949e;
    --accent: #58a6ff;
    --green: #3fb950;
    --yellow: #d29922;
    --red: #f85149;
    --orange: #db6d28;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 2rem;
  }
  .container { max-width: 900px; margin: 0 auto; }
  
  h1 {
    font-size: 1.8rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .subtitle { color: var(--dim); margin-bottom: 1.5rem; font-size: 0.9rem; }
  
  textarea {
    width: 100%;
    height: 220px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.85rem;
    padding: 1rem;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
  }
  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--dim); }
  
  .btn-row { margin-top: 1rem; display: flex; gap: 0.75rem; align-items: center; }
  
  button {
    background: #238636;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 0.65rem 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }
  button:hover { background: #2ea043; }
  button:active { background: #238636; }
  button:disabled { opacity: 0.5; cursor: wait; }
  
  .btn-clear {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--dim);
  }
  .btn-clear:hover { border-color: var(--dim); color: var(--text); background: transparent; }
  
  .spinner { display: none; color: var(--dim); font-size: 0.9rem; }
  .spinner.active { display: inline; }
  
  #results { margin-top: 2rem; }
  
  .no-match {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    color: var(--yellow);
    text-align: center;
  }
  
  .summary-bar {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-weight: 600;
  }
  .summary-bar .count { color: var(--green); font-size: 1.1rem; }
  
  .issue-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    animation: fadeIn 0.3s ease;
  }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  
  .issue-card h3 {
    font-size: 1rem;
    margin-bottom: 1rem;
    color: var(--dim);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
  }
  
  .field { margin-bottom: 0.85rem; }
  .field-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--dim);
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  .field-value { font-size: 0.95rem; line-height: 1.5; }
  
  .severity {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.8rem;
  }
  .severity-high { background: rgba(248,81,73,0.15); color: var(--red); border: 1px solid var(--red); }
  .severity-medium { background: rgba(210,153,34,0.15); color: var(--yellow); border: 1px solid var(--yellow); }
  .severity-low { background: rgba(63,185,80,0.15); color: var(--green); border: 1px solid var(--green); }
  
  .fix-steps { list-style: none; padding: 0; }
  .fix-steps li {
    padding: 0.4rem 0.6rem;
    margin-bottom: 0.3rem;
    font-size: 0.9rem;
    line-height: 1.5;
  }
  .fix-steps li.step-heading {
    font-weight: 600;
    color: var(--accent);
    margin-top: 0.8rem;
    padding-left: 0;
  }
  .fix-steps li.step-text {
    color: var(--text);
    padding-left: 0.5rem;
  }
  .fix-steps li.step-empty {
    height: 0.3rem;
  }

  .code-block {
    position: relative;
    background: #0d1117;
    border: 1px solid var(--border);
    border-radius: 6px;
    margin: 0.4rem 0;
    padding: 0.8rem 1rem;
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 0.82rem;
    line-height: 1.6;
    overflow-x: auto;
    white-space: pre;
    color: #e6edf3;
  }
  .code-block .lang-tag {
    position: absolute;
    top: 0.3rem;
    right: 2.8rem;
    font-size: 0.65rem;
    color: var(--dim);
    text-transform: uppercase;
  }
  .code-block .copy-code-btn {
    position: absolute;
    top: 0.3rem;
    right: 0.5rem;
    background: transparent;
    border: 1px solid var(--border);
    color: var(--dim);
    font-size: 0.65rem;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    cursor: pointer;
  }
  .code-block .copy-code-btn:hover {
    color: var(--text);
    border-color: var(--dim);
    background: transparent;
  }

  /* Syntax highlighting colors */
  .code-block .kw   { color: #ff7b72; }  /* keywords, flags */
  .code-block .str  { color: #a5d6ff; }  /* strings */
  .code-block .cmt  { color: #8b949e; }  /* comments */
  .code-block .num  { color: #79c0ff; }  /* numbers */
  
  .patterns-count {
    color: var(--dim);
    font-size: 0.8rem;
    margin-top: 2rem;
    text-align: center;
    padding: 1rem;
    border-top: 1px solid var(--border);
  }

  /* Copy button for fix steps */
  .copy-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--dim);
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    float: right;
  }
  .copy-btn:hover { color: var(--text); border-color: var(--dim); background: transparent; }
</style>
</head>
<body>
<div class="container">
  <h1>🔍 AI Log Analyzer</h1>
  <p class="subtitle">Paste your error log below and click Analyze. Instant results — no API key needed.</p>
  
  <textarea id="logInput" placeholder="Paste your error log here...&#10;&#10;Examples:&#10;  CrashLoopBackOff, mapper_parsing_exception, OOMKilled,&#10;  connection refused, NullPointerException, certificate expired..."></textarea>
  
  <div class="btn-row">
    <button id="analyzeBtn" onclick="analyze()">🔍 Analyze</button>
    <button class="btn-clear" onclick="clearAll()">Clear</button>
    <span class="spinner" id="spinner">Analyzing...</span>
  </div>
  
  <div id="results"></div>
  
  <div class="patterns-count">Supports PATTERN_COUNT known error patterns across Kubernetes, OpenSearch, Vault, TLS, Python, Java, Go, DNS, Terraform, and more.</div>
</div>

<script>
async function analyze() {
  const logs = document.getElementById('logInput').value.trim();
  if (!logs) return;
  
  const btn = document.getElementById('analyzeBtn');
  const spinner = document.getElementById('spinner');
  btn.disabled = true;
  spinner.classList.add('active');
  
  try {
    const resp = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ logs })
    });
    const data = await resp.json();
    renderResults(data);
  } catch (e) {
    document.getElementById('results').innerHTML = '<div class="no-match">❌ Error connecting to server.</div>';
  } finally {
    btn.disabled = false;
    spinner.classList.remove('active');
  }
}

function renderResults(data) {
  const el = document.getElementById('results');
  
  if (!data.matches || data.matches.length === 0) {
    el.innerHTML = '<div class="no-match">⚠️ No known error patterns matched. Try pasting a more complete log.</div>';
    return;
  }
  
  let html = `<div class="summary-bar">📊 <span class="count">Found ${data.matches.length} issue(s)</span></div>`;
  
  data.matches.forEach((m, i) => {
    const sevClass = 'severity-' + m.severity.toLowerCase();
    const fixHtml = renderFixSteps(m.fix);
    
    html += `
    <div class="issue-card" style="animation-delay: ${i * 0.1}s">
      <h3>Issue ${i + 1}</h3>
      <div class="field">
        <div class="field-label">📋 Summary</div>
        <div class="field-value">${escapeHtml(m.summary)}</div>
      </div>
      <div class="field">
        <div class="field-label">🔎 Root Cause</div>
        <div class="field-value">${escapeHtml(m.cause)}</div>
      </div>
      <div class="field">
        <div class="field-label">💥 Impact</div>
        <div class="field-value">${escapeHtml(m.impact)}</div>
      </div>
      <div class="field">
        <div class="field-label">🏷️ Severity</div>
        <div class="field-value"><span class="severity ${sevClass}">${m.severity}</span></div>
      </div>
      <div class="field">
        <div class="field-label">🛠️ Solution</div>
        <div class="fix-steps">${fixHtml}</div>
      </div>
    </div>`;
  });
  
  el.innerHTML = html;
}

function renderFixSteps(steps) {
  let html = '';
  let inCodeBlock = false;
  let codeLines = [];
  let codeLang = '';
  
  for (let i = 0; i < steps.length; i++) {
    const line = steps[i];
    
    if (line.startsWith('```') && !inCodeBlock) {
      // Start of code block
      inCodeBlock = true;
      codeLang = line.slice(3).trim() || '';
      codeLines = [];
    } else if (line === '```' && inCodeBlock) {
      // End of code block
      inCodeBlock = false;
      const codeId = 'code-' + Math.random().toString(36).substr(2, 9);
      const codeText = codeLines.join('\\n');
      const langTag = codeLang ? `<span class="lang-tag">${escapeHtml(codeLang)}</span>` : '';
      html += `<div class="code-block" id="${codeId}">${langTag}<button class="copy-code-btn" onclick="copyCode('${codeId}')">📋 Copy</button>${highlightCode(escapeHtml(codeLines.join('\\n')), codeLang)}</div>`;
    } else if (inCodeBlock) {
      codeLines.push(line);
    } else if (line.startsWith('Step ')) {
      html += `<div class="step-heading" style="font-weight:600;color:var(--accent);margin-top:0.8rem;font-size:0.95rem;">${escapeHtml(line)}</div>`;
    } else if (line.trim() === '') {
      // empty line spacer
    } else if (line.startsWith('  •') || line.startsWith('  -')) {
      html += `<div style="padding:0.2rem 0 0.2rem 1rem;color:var(--text);font-size:0.9rem;">${escapeHtml(line)}</div>`;
    } else {
      html += `<div style="padding:0.2rem 0;color:var(--text);font-size:0.9rem;">${escapeHtml(line)}</div>`;
    }
  }
  return html;
}

function highlightCode(code, lang) {
  // Basic syntax highlighting
  // Comments
  code = code.replace(/(#[^\\n]*)/g, '<span class="cmt">$1</span>');
  code = code.replace(/(--[^\\n]*)/g, '<span class="cmt">$1</span>');
  // Strings
  code = code.replace(/(&quot;[^&]*&quot;)/g, '<span class="str">$1</span>');
  return code;
}

function copyCode(id) {
  const el = document.getElementById(id);
  const text = el.textContent.replace(/^[a-z]+ ?📋 Copy/, '').replace(/📋 Copy$/, '').trim();
  navigator.clipboard.writeText(text).then(() => {
    const btn = el.querySelector('.copy-code-btn');
    btn.textContent = '✅ Copied!';
    setTimeout(() => btn.textContent = '📋 Copy', 2000);
  });
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

function clearAll() {
  document.getElementById('logInput').value = '';
  document.getElementById('results').innerHTML = '';
}

// Submit on Ctrl+Enter
document.getElementById('logInput').addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') analyze();
});
</script>
</body>
</html>"""

# ─── Web Server ───────────────────────────────────────────────────────────────
class LogAnalyzerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve the HTML page."""
        page = HTML_PAGE.replace('PATTERN_COUNT', str(len(PATTERNS)))
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(page.encode())

    def do_POST(self):
        """Handle log analysis requests."""
        if self.path != '/analyze':
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()

        try:
            data = json.loads(body)
            logs = data.get('logs', '')
        except json.JSONDecodeError:
            logs = body

        matches = analyze_offline(logs)

        result = {
            "matches": [
                {
                    "summary": m["summary"],
                    "cause": m["cause"],
                    "impact": m.get("impact", "See summary."),
                    "severity": m["severity"],
                    "fix": m["fix"],
                }
                for m in matches
            ]
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def log_message(self, format, *args):
        """Custom logging to be cleaner."""
        msg = format % args
        if 'POST /analyze' in msg:
            print(f"  📨 {msg}")
        elif 'GET /' in msg and 'favicon' not in msg:
            print(f"  🌐 {msg}")


def main():
    parser = argparse.ArgumentParser(description="🔍 AI Log Analyzer — Web UI")
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1, use 0.0.0.0 for network access)')
    args = parser.parse_args()

    import socket
    server = HTTPServer((args.host, args.port), LogAnalyzerHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print(f"""
\033[96m╔══════════════════════════════════════════════════════════════╗
║   🔍  AI Log Analyzer — Web UI                              ║
║                                                              ║
║   Open in browser:  \033[1m\033[92mhttp://localhost:{args.port}\033[96m                    ║
║   {len(PATTERNS)} error patterns loaded                                  ║
║                                                              ║
║   Press Ctrl+C to stop                                       ║
╚══════════════════════════════════════════════════════════════╝\033[0m
""")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\033[96m  👋 Server stopped.\033[0m\n")
        server.server_close()


if __name__ == '__main__':
    main()
