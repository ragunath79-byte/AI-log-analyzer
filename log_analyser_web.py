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
<title>AI Log Analyzer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-primary: #0f0f1a;
    --bg-secondary: #1a1a2e;
    --bg-card: #16213e;
    --bg-card-hover: #1c2a4a;
    --border: rgba(99, 102, 241, 0.2);
    --border-glow: rgba(99, 102, 241, 0.4);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-dim: #64748b;
    --accent: #6366f1;
    --accent-light: #818cf8;
    --accent-glow: rgba(99, 102, 241, 0.3);
    --green: #10b981;
    --green-glow: rgba(16, 185, 129, 0.2);
    --yellow: #f59e0b;
    --yellow-glow: rgba(245, 158, 11, 0.2);
    --red: #ef4444;
    --red-glow: rgba(239, 68, 68, 0.2);
    --gradient-1: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
    --gradient-2: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
  }
  
  * { margin: 0; padding: 0; box-sizing: border-box; }
  
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    background-image: 
      radial-gradient(ellipse at 20% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 100%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
    color: var(--text-primary);
    min-height: 100vh;
    padding: 2rem;
    line-height: 1.6;
  }
  
  .container { 
    max-width: 960px; 
    margin: 0 auto;
  }
  
  /* Header Section */
  .header {
    text-align: center;
    margin-bottom: 3rem;
    padding: 2rem 0;
  }
  
  .logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .logo-icon {
    width: 56px;
    height: 56px;
    background: var(--gradient-1);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    box-shadow: 0 8px 32px var(--accent-glow);
  }
  
  h1 {
    font-size: 2.5rem;
    font-weight: 700;
    background: var(--gradient-1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
  }
  
  .subtitle { 
    color: var(--text-secondary); 
    font-size: 1.1rem;
    font-weight: 400;
    max-width: 500px;
    margin: 0 auto;
  }
  
  /* Main Card */
  .main-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 
      0 4px 6px -1px rgba(0, 0, 0, 0.3),
      0 2px 4px -2px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
  }
  
  .input-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  textarea {
    width: 100%;
    height: 200px;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text-primary);
    font-family: 'JetBrains Mono', 'SF Mono', monospace;
    font-size: 0.875rem;
    padding: 1.25rem;
    resize: vertical;
    outline: none;
    transition: all 0.3s ease;
  }
  textarea:focus { 
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
  textarea::placeholder { color: var(--text-dim); }
  
  .btn-row { 
    margin-top: 1.5rem; 
    display: flex; 
    gap: 1rem; 
    align-items: center;
  }
  
  button {
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    border: none;
  }
  
  .btn-primary {
    background: var(--gradient-1);
    color: #fff;
    border-radius: 12px;
    padding: 0.875rem 2rem;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: 0 4px 15px var(--accent-glow);
  }
  .btn-primary:hover { 
    transform: translateY(-2px);
    box-shadow: 0 8px 25px var(--accent-glow);
  }
  .btn-primary:active { transform: translateY(0); }
  .btn-primary:disabled { 
    opacity: 0.6; 
    cursor: wait;
    transform: none;
  }
  
  .btn-secondary {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-secondary);
    border-radius: 12px;
    padding: 0.875rem 1.5rem;
  }
  .btn-secondary:hover { 
    border-color: var(--text-dim);
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.03);
  }
  
  .spinner { 
    display: none; 
    color: var(--accent-light); 
    font-size: 0.9rem;
    font-weight: 500;
  }
  .spinner.active { 
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }
  .spinner::before {
    content: '';
    width: 16px;
    height: 16px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  
  #results { margin-top: 2rem; }
  
  .no-match {
    background: var(--bg-secondary);
    border: 1px solid var(--yellow-glow);
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    color: var(--yellow);
    font-weight: 500;
  }
  
  .summary-bar {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
    border: 1px solid var(--green-glow);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .summary-bar .icon {
    width: 40px;
    height: 40px;
    background: var(--green);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
  }
  .summary-bar .count { 
    color: var(--green); 
    font-size: 1.25rem;
    font-weight: 700;
  }
  .summary-bar .label {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
  
  .issue-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.75rem;
    margin-bottom: 1.25rem;
    animation: slideUp 0.4s ease forwards;
    opacity: 0;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
  }
  .issue-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  }
  @keyframes slideUp { 
    from { opacity: 0; transform: translateY(20px); } 
    to { opacity: 1; transform: translateY(0); } 
  }
  
  .issue-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.25rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
  }
  
  .issue-number {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .issue-badge {
    width: 32px;
    height: 32px;
    background: var(--gradient-1);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.9rem;
  }
  
  .issue-card h3 {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .field { margin-bottom: 1.25rem; }
  .field:last-child { margin-bottom: 0; }
  
  .field-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-dim);
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
  }
  .field-value { 
    font-size: 0.95rem; 
    line-height: 1.7;
    color: var(--text-secondary);
  }
  
  .severity {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.85rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .severity::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  .severity-high { 
    background: var(--red-glow); 
    color: var(--red);
  }
  .severity-high::before { background: var(--red); }
  .severity-medium { 
    background: var(--yellow-glow); 
    color: var(--yellow);
  }
  .severity-medium::before { background: var(--yellow); }
  .severity-low { 
    background: var(--green-glow); 
    color: var(--green);
  }
  .severity-low::before { background: var(--green); }
  
  .fix-steps { list-style: none; padding: 0; }

  .code-block {
    position: relative;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin: 0.75rem 0;
    padding: 1rem 1.25rem;
    padding-top: 2rem;
    font-family: 'JetBrains Mono', 'SF Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.7;
    overflow-x: auto;
    white-space: pre;
    color: var(--text-primary);
  }
  .code-block .lang-tag {
    position: absolute;
    top: 0.5rem;
    left: 1rem;
    font-size: 0.65rem;
    color: var(--accent-light);
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.05em;
  }
  .code-block .copy-code-btn {
    position: absolute;
    top: 0.5rem;
    right: 0.75rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 0.7rem;
    padding: 0.25rem 0.6rem;
    border-radius: 6px;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    transition: all 0.2s ease;
  }
  .code-block .copy-code-btn:hover {
    color: var(--text-primary);
    border-color: var(--accent);
    background: var(--bg-card);
  }

  /* Syntax highlighting */
  .code-block .kw   { color: #c792ea; }
  .code-block .str  { color: #c3e88d; }
  .code-block .cmt  { color: #546e7a; }
  .code-block .num  { color: #f78c6c; }
  
  .patterns-count {
    color: var(--text-dim);
    font-size: 0.8rem;
    margin-top: 3rem;
    text-align: center;
    padding: 1.5rem;
    border-top: 1px solid var(--border);
  }
  .patterns-count span {
    color: var(--accent-light);
    font-weight: 600;
  }

  .copy-btn {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 0.7rem;
    padding: 0.25rem 0.6rem;
    border-radius: 6px;
    cursor: pointer;
    float: right;
    font-family: 'Inter', sans-serif;
  }
  .copy-btn:hover { 
    color: var(--text-primary); 
    border-color: var(--accent);
  }
  
  /* Keyboard shortcut hint */
  .hint {
    color: var(--text-dim);
    font-size: 0.8rem;
    margin-top: 1rem;
  }
  .hint kbd {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.15rem 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
  }
  
  /* Step styling */
  .step-heading {
    font-weight: 600;
    color: var(--accent-light);
    margin-top: 1rem;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .step-heading::before {
    content: '→';
    color: var(--accent);
  }
</style>
</head>
<body>
<div class="container">
  <header class="header">
    <div class="logo">
      <div class="logo-icon">🔍</div>
      <h1>AI Log Analyzer</h1>
    </div>
    <p class="subtitle">Instantly analyze error logs with AI-powered pattern matching. No API key required.</p>
  </header>
  
  <div class="main-card">
    <label class="input-label">
      <span>📋</span> Paste Your Logs
    </label>
    <textarea id="logInput" placeholder="Paste your error log here...&#10;&#10;Examples:&#10;  • CrashLoopBackOff, OOMKilled&#10;  • CircuitBreakingException, unassigned shards&#10;  • ThrottlingException, AccessDenied&#10;  • NullPointerException, OutOfMemoryError&#10;  • kafka consumer lag, rebalance&#10;  • vault sealed, certificate expired"></textarea>
    
    <div class="btn-row">
      <button class="btn-primary" id="analyzeBtn" onclick="analyze()">
        <span>⚡</span> Analyze Now
      </button>
      <button class="btn-secondary" onclick="clearAll()">Clear</button>
      <span class="spinner" id="spinner">Processing...</span>
    </div>
    <p class="hint">Pro tip: Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to analyze</p>
  </div>
  
  <div id="results"></div>
  
  <div class="patterns-count">
    Powered by <span>PATTERN_COUNT</span> intelligent error patterns covering Kubernetes, Elasticsearch, AWS, Kafka, Vault, Terraform, PostgreSQL, MongoDB, Docker, Nginx, Java/Spring, Python, Prometheus, Gardener, and more.
  </div>
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
  
  let html = `<div class="summary-bar">
    <div class="icon">✓</div>
    <div>
      <div class="count">Found ${data.matches.length} issue${data.matches.length > 1 ? 's' : ''}</div>
      <div class="label">Analysis complete</div>
    </div>
  </div>`;
  
  data.matches.forEach((m, i) => {
    const sevClass = 'severity-' + m.severity.toLowerCase();
    const fixHtml = renderFixSteps(m.fix);
    
    html += `
    <div class="issue-card" style="animation-delay: ${i * 0.1}s">
      <div class="issue-header">
        <div class="issue-number">
          <div class="issue-badge">${i + 1}</div>
          <h3>${escapeHtml(m.summary.substring(0, 50))}${m.summary.length > 50 ? '...' : ''}</h3>
        </div>
        <span class="severity ${sevClass}">${m.severity}</span>
      </div>
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
      inCodeBlock = true;
      codeLang = line.slice(3).trim() || '';
      codeLines = [];
    } else if (line === '```' && inCodeBlock) {
      inCodeBlock = false;
      const codeId = 'code-' + Math.random().toString(36).substr(2, 9);
      const codeText = codeLines.join('\\n');
      const langTag = codeLang ? `<span class="lang-tag">${escapeHtml(codeLang)}</span>` : '';
      html += `<div class="code-block" id="${codeId}">${langTag}<button class="copy-code-btn" onclick="copyCode('${codeId}')">Copy</button>${highlightCode(escapeHtml(codeLines.join('\\n')), codeLang)}</div>`;
    } else if (inCodeBlock) {
      codeLines.push(line);
    } else if (line.startsWith('Step ')) {
      html += `<div class="step-heading">${escapeHtml(line)}</div>`;
    } else if (line.trim() === '') {
      // empty line spacer
    } else if (line.startsWith('  •') || line.startsWith('  -')) {
      html += `<div style="padding:0.3rem 0 0.3rem 1.5rem;color:var(--text-secondary);font-size:0.9rem;line-height:1.6;">${escapeHtml(line)}</div>`;
    } else {
      html += `<div style="padding:0.3rem 0;color:var(--text-secondary);font-size:0.9rem;line-height:1.6;">${escapeHtml(line)}</div>`;
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
