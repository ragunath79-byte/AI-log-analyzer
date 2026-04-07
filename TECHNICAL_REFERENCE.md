# AI Log Analyzer — Technical Reference

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│  ┌─────────────────┐              ┌─────────────────────────────┐   │
│  │  CLI            │              │  Web UI (Browser)           │   │
│  │  log_analyser.py│              │  log_analyser_web.py        │   │
│  └────────┬────────┘              └──────────────┬──────────────┘   │
│           │                                      │                  │
│           │         paste logs                   │ HTTP POST        │
│           ▼                                      ▼                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PATTERN ENGINE                            │   │
│  │                                                              │   │
│  │   PATTERNS = [                                               │   │
│  │     { regex, summary, cause, impact, fix, severity },        │   │
│  │     { regex, summary, cause, impact, fix, severity },        │   │
│  │     ... 563 patterns                                         │   │
│  │   ]                                                          │   │
│  │                                                              │   │
│  │   analyze_offline(logs) → matches                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    OUTPUT                                    │   │
│  │   • Summary of each matched issue                            │   │
│  │   • Root cause explanation                                   │   │
│  │   • Impact assessment                                        │   │
│  │   • Step-by-step fix commands                                │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. File Structure

```
AI-log-analyzer/
├── log_analyser.py              # Core engine + CLI (563 patterns)
├── log_analyser_web.py          # Web UI server (imports from log_analyser.py)
├── AI_Log_Analyzer_Presentation.md
├── AI_Log_Analyzer_Demo_Guide.md
└── TECHNICAL_REFERENCE.md       # This file
```

---

## 3. Core Components

### A. Pattern Definition (`log_analyser.py`)

Each pattern is a Python dictionary:

```python
{
    "regex": r"(?i)CrashLoopBackOff|crash.*loop",    # What to match
    "summary": "Kubernetes pod in CrashLoopBackOff", # One-line title
    "cause": "Container keeps crashing on startup.", # Why it happens
    "impact": "Pod is not running; service down.",   # Business impact
    "fix": [                                          # Step-by-step solution
        "Step 1 — Check pod logs:",
        "```bash",
        "kubectl logs <pod> --previous",
        "```",
        "",
        "Step 2 — Check events:",
        "```bash", 
        "kubectl describe pod <pod>",
        "```",
    ],
    "severity": "High",                              # High/Medium/Low
}
```

### B. Pattern Matching Function

```python
def analyze_offline(logs):
    """Match logs against known patterns and return structured results."""
    matches = []
    seen = set()
    
    for pat in PATTERNS:                              # Loop through 563 patterns
        if re.search(pat["regex"], logs):             # Does this pattern match?
            if pat["summary"] not in seen:            # Avoid duplicates
                matches.append(pat)
                seen.add(pat["summary"])
    
    return matches
```

**How it works:**
1. Takes raw log text as input
2. Loops through all 563 patterns
3. Uses `re.search()` to check if regex matches anywhere in logs
4. Returns list of matching patterns (deduplicated)

### C. Regex Matching

```python
# Example pattern regex:
r"(?i)CrashLoopBackOff|crash.*loop"

# (?i)           = Case-insensitive matching
# CrashLoopBackOff = Exact match
# |              = OR operator
# crash.*loop    = "crash" followed by anything, then "loop"
```

**Common regex patterns used:**

| Pattern | Meaning |
|---------|---------|
| `(?i)` | Case-insensitive |
| `.*` | Any characters (0 or more) |
| `\|` | OR |
| `\b` | Word boundary |
| `[0-9]+` | One or more digits |
| `error\|fail\|exception` | Match any of these words |

---

## 4. Web Server Flow (`log_analyser_web.py`)

```python
# 1. Import patterns from core engine
from log_analyser import PATTERNS, analyze_offline

# 2. HTTP Server handles requests
class LogAnalyzerHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """User visits http://localhost:5000"""
        # Serve HTML page with pattern count
        page = HTML_PAGE.replace('PATTERN_COUNT', str(len(PATTERNS)))
        self.send_response(200)
        self.wfile.write(page.encode())
    
    def do_POST(self):
        """User clicks 'Analyze Now'"""
        # 1. Read JSON body
        body = self.rfile.read(content_length)
        data = json.loads(body)
        logs = data.get('logs', '')
        
        # 2. Call pattern matching engine
        matches = analyze_offline(logs)
        
        # 3. Return results as JSON
        result = {"matches": [...]}
        self.wfile.write(json.dumps(result).encode())
```

---

## 5. Request/Response Flow

```
USER BROWSER                    WEB SERVER                    PATTERN ENGINE
     │                              │                              │
     │  GET /                       │                              │
     │─────────────────────────────>│                              │
     │                              │                              │
     │  HTML page (with JS)         │                              │
     │<─────────────────────────────│                              │
     │                              │                              │
     │  User pastes log,            │                              │
     │  clicks "Analyze Now"        │                              │
     │                              │                              │
     │  POST /analyze               │                              │
     │  {"logs": "CrashLoop..."}    │                              │
     │─────────────────────────────>│  analyze_offline(logs)       │
     │                              │─────────────────────────────>│
     │                              │                              │
     │                              │  [match1, match2, ...]       │
     │                              │<─────────────────────────────│
     │                              │                              │
     │  {"matches": [...]}          │                              │
     │<─────────────────────────────│                              │
     │                              │                              │
     │  JavaScript renders          │                              │
     │  results in browser          │                              │
     │                              │                              │
```

---

## 6. JavaScript Frontend

```javascript
// In HTML_PAGE template

async function analyze() {
  const logs = document.getElementById('logInput').value;
  
  // Send logs to server
  const resp = await fetch('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ logs })
  });
  
  // Get matching patterns
  const data = await resp.json();
  
  // Render results
  renderResults(data);
}

function renderResults(data) {
  // Loop through matches and create HTML cards
  data.matches.forEach((m, i) => {
    // Display: summary, cause, impact, severity, fix steps
  });
}
```

---

## 7. Example End-to-End

**Input Log:**
```
Error: CrashLoopBackOff - container exited with code 137
```

**Step 1 — Regex Match:**
```python
re.search(r"(?i)CrashLoopBackOff", "Error: CrashLoopBackOff...")
# Returns: <Match object>  ✓ Pattern matches!
```

**Step 2 — Return Pattern Data:**
```python
{
    "summary": "Kubernetes pod in CrashLoopBackOff",
    "cause": "Container keeps crashing on startup.",
    "impact": "Pod is not running; service unavailable.",
    "severity": "High",
    "fix": ["Step 1 — Check logs...", ...]
}
```

**Step 3 — Display to User:**
```
┌─────────────────────────────────────────────┐
│ 🔴 HIGH  Kubernetes pod in CrashLoopBackOff │
├─────────────────────────────────────────────┤
│ Cause: Container keeps crashing on startup  │
│ Impact: Service unavailable                 │
│                                             │
│ Fix:                                        │
│ → Step 1: kubectl logs <pod> --previous    │
│ → Step 2: kubectl describe pod <pod>       │
└─────────────────────────────────────────────┘
```

---

## 8. Key Design Decisions

| Decision | Why |
|----------|-----|
| **Regex-based** | Fast, deterministic, no ML needed |
| **No external dependencies** | Works anywhere with Python 3 |
| **Single file patterns** | Easy to add/edit patterns |
| **Severity levels** | Prioritize critical issues |
| **Step-by-step fixes** | Actionable, not just diagnosis |
| **Deduplication** | Don't show same issue twice |
| **Case-insensitive** | Match logs regardless of case |

---

## 9. Adding a New Pattern

```python
# In log_analyser.py, add to PATTERNS list:

{
    "regex": r"(?i)your-error-message|alternate-form",
    "summary": "Short description",
    "cause": "Why this error happens.",
    "impact": "What breaks when this occurs.",
    "fix": [
        "Step 1 — First action:",
        "```bash",
        "command to run",
        "```",
        "",
        "Step 2 — Second action:",
        "Explanation...",
    ],
    "severity": "High",  # High, Medium, or Low
},
```

---

## 10. Pattern Categories (563 Total)

| Category | Count | Examples |
|----------|-------|----------|
| Kubernetes | 40+ | CrashLoopBackOff, OOMKilled, ImagePullBackOff |
| Elasticsearch | 24 | Circuit breaker, shards, mapping errors |
| Kafka | 27 | Consumer lag, rebalance, broker errors |
| AWS | 12 | ThrottlingException, AccessDenied, S3/EC2/Lambda |
| Vault | 16 | Sealed, auth errors, lease expiry |
| Terraform | 20 | State lock, provider errors, plan failures |
| Prometheus | 20 | Scrape errors, TSDB, alerting |
| PostgreSQL | 7 | Connection, locks, replication |
| MongoDB | 7 | Replica set, auth, disk space |
| Docker | 8 | Build, network, volume, OOM |
| Nginx | 7 | Upstream timeout, SSL, DNS |
| Java/Spring | 17 | OOM, NPE, Bean creation, Hibernate |
| Python | 8 | Traceback, ImportError, encoding |
| HTTP/API | 10 | 400-504 status codes, CORS |
| Microservices | 8 | Circuit breaker, gRPC, tracing |
| Gardener | 24 | Shoot, Seed, gardenlet |
| Fluent Bit | 13 | Input/output, backpressure |
| Linux System | 9 | OOM killer, systemd, filesystem |
| Git/GitHub | 10 | Merge conflict, auth, rate limit |
| Others | Various | Redis, Helm, ArgoCD, cert-manager, Istio |

---

## 11. Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `log_analyser.py` | ~13,000 | 563 patterns + `analyze_offline()` function |
| `log_analyser_web.py` | ~800 | HTTP server + HTML/CSS/JS frontend |

---

## 12. Quick Reference Commands

```bash
# Run CLI
python3 log_analyser.py

# Run Web UI
python3 log_analyser_web.py

# Run Web UI on custom port
python3 log_analyser_web.py --port 8080

# Allow network access (for demo)
python3 log_analyser_web.py --host 0.0.0.0

# Count patterns
grep -c '"regex":' log_analyser.py

# Validate syntax
python3 -m py_compile log_analyser.py

# Clear Python cache
rm -rf __pycache__
```

---

## 13. Deployment Options

### Local Development
```bash
python3 log_analyser_web.py
# Open http://localhost:5000
```

### Team Access (Same Network)
```bash
python3 log_analyser_web.py --host 0.0.0.0
# Others access via http://YOUR_IP:5000
```

### Share via GitHub
```bash
git clone https://github.com/ragunath79-byte/AI-log-analyzer.git
cd AI-log-analyzer
python3 log_analyser_web.py
```

---

## 14. Contributing New Patterns

1. Identify a common error from your logs
2. Find the unique error signature (what text always appears)
3. Create regex pattern
4. Add to `PATTERNS` list in `log_analyser.py`
5. Test with `python3 -m py_compile log_analyser.py`
6. Commit and push

---

## Author
Ragunath | April 2026
