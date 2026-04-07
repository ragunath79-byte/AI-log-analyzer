# AI Log Analyzer

**563 Intelligent Pattern Engine + AI Fallback for Kubernetes & SAP Cloud Logs**

A powerful, offline-first log analysis tool that combines a curated database of 563 error patterns with optional AI-powered analysis (Claude/ChatGPT) for unrecognized errors.

![Python 3](https://img.shields.io/badge/Python-3.x-blue.svg)
![Patterns](https://img.shields.io/badge/Patterns-563-green.svg)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen.svg)
![AI Optional](https://img.shields.io/badge/AI-Optional-orange.svg)

---

## ✨ Features

### 🎯 Core Capabilities
- **563 Curated Patterns** - Kubernetes, Istio, SAP, Cloud providers, and more
- **Offline-First** - Works 100% without internet
- **Zero Dependencies** - Only Python 3 standard library
- **AI Fallback** - Claude/ChatGPT for unmatched errors (optional)
- **Modern Web UI** - Glassmorphism design with animations
- **Pattern Explorer** - Browse all 563 patterns by category
- **Feedback Loop** - Track and learn from unmatched errors
- **GitHub Integration** - Auto-create issues for team collaboration

### 🎨 Modern UI
- Glassmorphism design with animated gradients
- Dark theme optimized for readability
- Real-time pattern filtering and search
- Responsive layout for all screen sizes

### 📊 Pattern Categories
| Category | Patterns | Description |
|----------|----------|-------------|
| Istio/Envoy | 45 | Service mesh proxy errors |
| Kubernetes | 87 | Pod, deployment, node issues |
| SAP/BTP | 63 | Business Technology Platform |
| Cloud Providers | 52 | AWS, Azure, GCP errors |
| Networking | 41 | DNS, SSL, connectivity |
| Storage | 35 | PVC, volume mount issues |
| Security | 48 | Auth, RBAC, certificates |
| Databases | 39 | PostgreSQL, Redis, MongoDB |
| Application | 153 | Java, Node.js, Python errors |

---

## 🚀 Quick Start

### Installation
```bash
git clone https://github.com/ragunath79-byte/AI-log-analyzer.git
cd AI-log-analyzer
```

### Run Web UI (Recommended)
```bash
python3 log_analyser_web.py
# Open http://localhost:5000 in your browser
```

### Run CLI
```bash
python3 log_analyser.py
# Paste your logs and press Ctrl+D (or Ctrl+Z on Windows)
```

---

## 🌐 Web UI Features

### Main Panel
- Paste logs and get instant analysis
- Pattern matches highlighted with severity
- AI analysis for unmatched errors (if configured)

### Pattern Explorer
- Browse all 563 patterns organized by category
- Search patterns by name, regex, or description
- Filter by category chips
- See pattern details and severity levels

### Settings Panel
- Configure AI providers (Claude/ChatGPT)
- Set GitHub token for issue creation
- Enable/disable feedback loop

### Feedback Panel
- View analysis statistics
- Track unmatched error patterns
- Monitor AI fallback usage

---

## ⚙️ Configuration

### Environment Variables (Optional)
```bash
# For AI fallback
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# For GitHub integration
export GITHUB_TOKEN="ghp_..."
export GITHUB_REPO="owner/repo"
```

### Web UI Settings
Configure directly in the Settings panel - no restart required.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Demo Guide](AI_Log_Analyzer_Demo_Guide.md) | Step-by-step demo walkthrough |
| [Technical Reference](TECHNICAL_REFERENCE.md) | Architecture and API docs |
| [Presentation](AI_Log_Analyzer_Presentation.md) | Management presentation slides |

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI interface |
| `/analyze` | POST | Analyze log input |
| `/patterns` | GET | Get all patterns summary |
| `/feedback` | POST | Submit feedback |
| `/feedback/stats` | GET | Get analysis statistics |
| `/github/issues` | POST | Create GitHub issue |

---

## 📈 Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Web UI / CLI                          │
├──────────────────────────────────────────────────────────┤
│                   Pattern Engine                         │
│              (563 Regex Patterns)                        │
├──────────────────────────────────────────────────────────┤
│                   AI Fallback                            │
│           (Claude / ChatGPT - Optional)                  │
├──────────────────────────────────────────────────────────┤
│                 Feedback Loop                            │
│         (Local logging + GitHub Issues)                  │
└──────────────────────────────────────────────────────────┘
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- SAP ERP4SME Team for pattern contributions
- OpenAI and Anthropic for AI capabilities
- The Kubernetes community for documentation

---

**Made with ❤️ for the DevOps community**
