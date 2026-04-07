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
    from log_analyser import (
        PATTERNS, analyze_offline, analyze_with_ai,
        log_unmatched_error, get_unmatched_errors, update_unmatched_error,
        clear_unmatched_errors, get_feedback_stats, suggest_pattern_from_log,
        create_github_issue, get_github_issues, get_patterns_summary
    )
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-primary: #030712;
    --bg-secondary: #0a0f1a;
    --bg-card: rgba(15, 23, 42, 0.6);
    --bg-card-solid: #0f172a;
    --bg-card-hover: rgba(30, 41, 59, 0.7);
    --border: rgba(148, 163, 184, 0.1);
    --border-glow: rgba(99, 102, 241, 0.5);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-dim: #475569;
    --accent: #6366f1;
    --accent-light: #818cf8;
    --accent-glow: rgba(99, 102, 241, 0.4);
    --green: #10b981;
    --green-light: #34d399;
    --green-glow: rgba(16, 185, 129, 0.25);
    --yellow: #fbbf24;
    --yellow-glow: rgba(251, 191, 36, 0.25);
    --red: #f43f5e;
    --red-glow: rgba(244, 63, 94, 0.25);
    --cyan: #22d3ee;
    --purple: #a855f7;
    --gradient-1: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
    --gradient-2: linear-gradient(135deg, #22d3ee 0%, #6366f1 50%, #a855f7 100%);
    --gradient-3: linear-gradient(180deg, rgba(99, 102, 241, 0.15) 0%, transparent 50%);
  }
  
  * { margin: 0; padding: 0; box-sizing: border-box; }
  
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    padding: 2rem;
    line-height: 1.6;
    overflow-x: hidden;
  }
  
  /* Animated background */
  body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.3), transparent),
      radial-gradient(ellipse 60% 40% at 100% 100%, rgba(168, 85, 247, 0.15), transparent),
      radial-gradient(ellipse 40% 30% at 0% 100%, rgba(34, 211, 238, 0.1), transparent);
    pointer-events: none;
    z-index: -1;
    animation: bgPulse 8s ease-in-out infinite alternate;
  }
  
  @keyframes bgPulse {
    0% { opacity: 0.8; }
    100% { opacity: 1; }
  }
  
  /* Noise texture overlay */
  body::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
    opacity: 0.03;
    pointer-events: none;
    z-index: -1;
  }
  
  .container { 
    max-width: 1000px; 
    margin: 0 auto;
    position: relative;
  }
  
  /* Header Section */
  .header {
    text-align: center;
    margin-bottom: 3rem;
    padding: 2.5rem 0;
    position: relative;
  }
  
  .logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 1.25rem;
    margin-bottom: 1.25rem;
  }
  
  .logo-icon {
    width: 64px;
    height: 64px;
    background: var(--gradient-1);
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    box-shadow: 
      0 0 40px var(--accent-glow),
      0 20px 40px -10px rgba(99, 102, 241, 0.5);
    animation: float 3s ease-in-out infinite;
    position: relative;
  }
  
  .logo-icon::after {
    content: '';
    position: absolute;
    inset: -2px;
    background: var(--gradient-1);
    border-radius: 22px;
    z-index: -1;
    opacity: 0.5;
    filter: blur(15px);
  }
  
  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
  }
  
  h1 {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #fff 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    text-shadow: 0 0 80px rgba(99, 102, 241, 0.5);
  }
  
  .subtitle { 
    color: var(--text-secondary); 
    font-size: 1.1rem;
    font-weight: 400;
    max-width: 550px;
    margin: 0 auto;
    line-height: 1.7;
  }
  
  .subtitle strong {
    color: var(--accent-light);
    font-weight: 600;
  }
  
  /* Glassmorphism Card */
  .main-card {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 2rem;
    box-shadow: 
      0 25px 50px -12px rgba(0, 0, 0, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    position: relative;
    overflow: hidden;
  }
  
  .main-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  }
  
  .input-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  
  textarea {
    width: 100%;
    height: 200px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    border-radius: 16px;
    color: var(--text-primary);
    font-family: 'JetBrains Mono', 'SF Mono', monospace;
    font-size: 0.875rem;
    padding: 1.25rem;
    resize: vertical;
    outline: none;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  textarea:focus { 
    border-color: var(--accent);
    box-shadow: 
      0 0 0 4px var(--accent-glow),
      inset 0 0 20px rgba(99, 102, 241, 0.1);
    background: rgba(0, 0, 0, 0.4);
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
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: none;
  }
  
  .btn-primary {
    background: var(--gradient-1);
    color: #fff;
    border-radius: 14px;
    padding: 1rem 2rem;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: 
      0 4px 15px var(--accent-glow),
      0 0 0 0 rgba(99, 102, 241, 0);
    position: relative;
    overflow: hidden;
  }
  .btn-primary::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
  }
  .btn-primary:hover::before {
    left: 100%;
  }
  .btn-primary:hover { 
    transform: translateY(-3px) scale(1.02);
    box-shadow: 
      0 20px 40px -10px var(--accent-glow),
      0 0 20px var(--accent-glow);
  }
  .btn-primary:active { 
    transform: translateY(-1px) scale(1);
  }
  .btn-primary:disabled { 
    opacity: 0.6; 
    cursor: wait;
    transform: none;
  }
  
  .btn-secondary {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    border-radius: 14px;
    padding: 1rem 1.5rem;
    backdrop-filter: blur(10px);
  }
  .btn-secondary:hover { 
    border-color: var(--accent);
    color: var(--text-primary);
    background: rgba(99, 102, 241, 0.1);
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
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
    background: rgba(251, 191, 36, 0.05);
    border: 1px solid rgba(251, 191, 36, 0.2);
    border-radius: 16px;
    padding: 2.5rem;
    text-align: center;
    color: var(--yellow);
    font-weight: 500;
    backdrop-filter: blur(10px);
  }
  
  .summary-bar {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(34, 211, 238, 0.05) 100%);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
  }
  .summary-bar::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.3), transparent);
  }
  .summary-bar .icon {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, var(--green) 0%, var(--cyan) 100%);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
  }
  .summary-bar .count { 
    color: var(--green-light); 
    font-size: 1.5rem;
    font-weight: 800;
  }
  .summary-bar .label {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
  
  .issue-card {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.75rem;
    margin-bottom: 1.25rem;
    animation: slideUp 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
    opacity: 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }
  .issue-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
  }
  .issue-card:hover {
    border-color: var(--border-glow);
    box-shadow: 
      0 25px 50px -12px rgba(0, 0, 0, 0.4),
      0 0 30px rgba(99, 102, 241, 0.1);
    transform: translateY(-4px);
  }
  @keyframes slideUp { 
    from { opacity: 0; transform: translateY(30px); } 
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
    font-size: 0.85rem;
    margin-top: 3rem;
    text-align: center;
    padding: 1.75rem;
    border-top: 1px solid var(--border);
    background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.03));
    border-radius: 0 0 20px 20px;
    transition: all 0.3s;
  }
  .patterns-count:hover {
    background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.08));
  }
  .patterns-count span {
    color: var(--accent-light);
    font-weight: 700;
  }

  .copy-btn {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 0.7rem;
    padding: 0.3rem 0.7rem;
    border-radius: 8px;
    cursor: pointer;
    float: right;
    font-family: 'Inter', sans-serif;
    transition: all 0.3s;
  }
  .copy-btn:hover { 
    color: var(--text-primary); 
    border-color: var(--accent);
    background: rgba(99, 102, 241, 0.1);
  }
  
  /* Keyboard shortcut hint */
  .hint {
    color: var(--text-dim);
    font-size: 0.8rem;
    margin-top: 1rem;
  }
  .hint kbd {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.2rem 0.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    box-shadow: 0 2px 0 rgba(0,0,0,0.2);
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
  
  /* Settings Panel */
  .settings-btn {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: var(--accent-light);
    padding: 0.5rem 1rem;
    border-radius: 10px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
  }
  .settings-btn:hover {
    background: rgba(99, 102, 241, 0.2);
    border-color: var(--accent);
    color: #fff;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
    transform: translateY(-2px);
  }
  .settings-panel {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.75rem;
    margin-bottom: 1.5rem;
    animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }
  .settings-panel::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent);
  }
  .settings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.25rem;
  }
  .settings-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
  }
  .settings-close {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border);
    color: var(--text-dim);
    width: 32px;
    height: 32px;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }
  .settings-close:hover { 
    color: var(--text-primary); 
    background: rgba(255, 255, 255, 0.1);
    border-color: var(--accent);
  }
  .settings-field {
    margin-bottom: 1.25rem;
  }
  .settings-field label {
    display: block;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
  }
  .settings-field input {
    width: 100%;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    color: var(--text-primary);
    font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
    transition: all 0.3s;
  }
  .settings-field input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 4px var(--accent-glow);
    background: rgba(0, 0, 0, 0.4);
  }
  .no-match-card {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(251, 191, 36, 0.2);
    border-radius: 20px;
    padding: 2.5rem;
    text-align: center;
  }
  .no-match-card h3 {
    color: var(--yellow);
    margin-bottom: 0.75rem;
    font-size: 1.25rem;
  }
  .no-match-card p {
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
  }
  .no-match-card .btn-primary {
    display: inline-flex;
  }
  
  /* Feedback Queue Panel */
  .feedback-btn {
    background: rgba(168, 85, 247, 0.1);
    border: 1px solid rgba(168, 85, 247, 0.2);
    color: var(--purple);
    padding: 0.5rem 1rem;
    border-radius: 10px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-left: 0.5rem;
    backdrop-filter: blur(10px);
  }
  .feedback-btn:hover {
    background: rgba(168, 85, 247, 0.2);
    border-color: var(--purple);
    color: #fff;
    box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
    transform: translateY(-2px);
  }
  .feedback-badge {
    background: linear-gradient(135deg, var(--red) 0%, #f97316 100%);
    color: white;
    font-size: 0.65rem;
    padding: 0.2rem 0.5rem;
    border-radius: 10px;
    margin-left: 0.3rem;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(244, 63, 94, 0.4);
  }
  .feedback-panel {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.75rem;
    margin-bottom: 1.5rem;
    animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }
  .feedback-panel::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(168, 85, 247, 0.3), transparent);
  }
  .feedback-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.25rem;
  }
  .feedback-stats {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.25rem;
    padding: 1.25rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 16px;
    border: 1px solid var(--border);
  }
  .stat-item {
    text-align: center;
    flex: 1;
    padding: 0.5rem;
    position: relative;
  }
  .stat-item:not(:last-child)::after {
    content: '';
    position: absolute;
    right: 0;
    top: 20%;
    height: 60%;
    width: 1px;
    background: var(--border);
  }
  .stat-value {
    font-size: 2rem;
    font-weight: 800;
    background: var(--gradient-2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .stat-label {
    font-size: 0.7rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-top: 0.25rem;
  }
  .feedback-list {
    max-height: 400px;
    overflow-y: auto;
  }
  .feedback-list::-webkit-scrollbar {
    width: 6px;
  }
  .feedback-list::-webkit-scrollbar-track {
    background: transparent;
  }
  .feedback-list::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 3px;
  }
  .feedback-item {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    transition: all 0.3s;
  }
  .feedback-item:hover {
    border-color: var(--accent);
    background: rgba(99, 102, 241, 0.05);
  }
  .feedback-item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }
  .feedback-item-meta {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .feedback-count {
    background: var(--red-glow);
    color: var(--red);
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
    border-radius: 8px;
    font-weight: 600;
  }
  .feedback-time {
    font-size: 0.75rem;
    color: var(--text-dim);
  }
  .feedback-snippet {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-secondary);
    background: var(--bg-secondary);
    padding: 0.5rem;
    border-radius: 8px;
    max-height: 80px;
    overflow: hidden;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .feedback-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.75rem;
  }
  .feedback-action-btn {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 0.3rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  .feedback-action-btn:hover {
    border-color: var(--accent);
    color: var(--text-primary);
  }
  .feedback-action-btn.primary {
    background: var(--accent);
    border-color: var(--accent);
    color: white;
  }
  .feedback-action-btn.primary:hover {
    background: var(--accent-light);
  }
  .pattern-suggestion {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    margin-top: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    white-space: pre-wrap;
    color: var(--text-secondary);
    max-height: 200px;
    overflow-y: auto;
  }
  
  /* Patterns Explorer Panel */
  .patterns-btn {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.2);
    color: var(--green);
    padding: 0.5rem 1rem;
    border-radius: 10px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-left: 0.5rem;
    backdrop-filter: blur(10px);
  }
  .patterns-btn:hover {
    background: rgba(16, 185, 129, 0.2);
    border-color: var(--green);
    color: #fff;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    transform: translateY(-2px);
  }
  .patterns-panel {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.75rem;
    margin-bottom: 1.5rem;
    animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }
  .patterns-panel::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.3), transparent);
  }
  .patterns-search {
    width: 100%;
    padding: 1rem 1.25rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    border-radius: 14px;
    color: var(--text-primary);
    font-size: 0.9rem;
    margin-bottom: 1.25rem;
    transition: all 0.3s;
  }
  .patterns-search:focus {
    outline: none;
    border-color: var(--green);
    box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2);
    background: rgba(0, 0, 0, 0.4);
  }
  .patterns-search::placeholder {
    color: var(--text-dim);
  }
  .patterns-categories {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.25rem;
  }
  .category-chip {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 0.4rem 0.9rem;
    border-radius: 20px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.3s;
    font-weight: 500;
  }
  .category-chip:hover {
    border-color: var(--accent);
    color: var(--text-primary);
    background: rgba(99, 102, 241, 0.1);
    transform: translateY(-2px);
  }
  .category-chip.active {
    background: var(--gradient-1);
    border-color: transparent;
    color: white;
    box-shadow: 0 4px 15px var(--accent-glow);
  }
  .category-chip .count {
    background: rgba(255,255,255,0.2);
    padding: 0.15rem 0.5rem;
    border-radius: 10px;
    font-size: 0.65rem;
    margin-left: 0.4rem;
    font-weight: 600;
  }
  .patterns-list {
    max-height: 500px;
    overflow-y: auto;
  }
  .patterns-list::-webkit-scrollbar {
    width: 6px;
  }
  .patterns-list::-webkit-scrollbar-track {
    background: transparent;
  }
  .patterns-list::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 3px;
  }
  .pattern-item {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.6rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .pattern-item:hover {
    border-color: var(--accent);
    background: rgba(99, 102, 241, 0.1);
    transform: translateX(4px);
  }
  .pattern-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
  }
  .pattern-summary {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.85rem;
  }
  .pattern-severity {
    font-size: 0.65rem;
    padding: 0.2rem 0.6rem;
    border-radius: 8px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .pattern-severity.high {
    background: rgba(244, 63, 94, 0.2);
    color: var(--red);
    border: 1px solid rgba(244, 63, 94, 0.3);
  }
  .pattern-severity.medium {
    background: rgba(251, 191, 36, 0.2);
    color: var(--yellow);
    border: 1px solid rgba(251, 191, 36, 0.3);
  }
  .pattern-severity.low {
    background: rgba(16, 185, 129, 0.2);
    color: var(--green);
    border: 1px solid rgba(16, 185, 129, 0.3);
  }
  .pattern-regex {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
    word-break: break-all;
    line-height: 1.5;
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
    <p class="subtitle"><strong>563</strong> built-in patterns + optional AI fallback for unknown errors</p>
  </header>
  
  <!-- Settings Panel -->
  <div id="settingsPanel" class="settings-panel" style="display: none;">
    <div class="settings-header">
      <h3>⚙️ Settings</h3>
      <button class="settings-close" onclick="toggleSettings()">✕</button>
    </div>
    <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem;">
      Configure API keys. All keys are stored locally in your browser.
    </p>
    
    <h4 style="color: var(--text-primary); font-size: 0.9rem; margin: 1rem 0 0.5rem;">AI Analysis (Optional)</h4>
    <div class="settings-field">
      <label>Claude API Key (Anthropic)</label>
      <input type="password" id="anthropicKey" placeholder="sk-ant-api03-..." />
      <a href="https://console.anthropic.com/settings/keys" target="_blank" style="font-size: 0.75rem; color: var(--accent-light);">Get key →</a>
    </div>
    <div class="settings-field">
      <label>OpenAI API Key</label>
      <input type="password" id="openaiKey" placeholder="sk-..." />
      <a href="https://platform.openai.com/api-keys" target="_blank" style="font-size: 0.75rem; color: var(--accent-light);">Get key →</a>
    </div>
    
    <h4 style="color: var(--text-primary); font-size: 0.9rem; margin: 1.5rem 0 0.5rem;">GitHub Integration (Team Sharing)</h4>
    <p style="color: var(--text-dim); font-size: 0.8rem; margin-bottom: 0.5rem;">
      Enable to share unmatched errors as GitHub Issues for team visibility.
    </p>
    <div class="settings-field">
      <label>GitHub Token (Personal Access Token)</label>
      <input type="password" id="githubToken" placeholder="ghp_..." />
      <a href="https://github.com/settings/tokens" target="_blank" style="font-size: 0.75rem; color: var(--accent-light);">Create token →</a>
    </div>
    <div class="settings-field" style="display: flex; align-items: center; gap: 0.5rem;">
      <input type="checkbox" id="autoCreateIssue" style="width: auto;" />
      <label for="autoCreateIssue" style="margin: 0; cursor: pointer;">Auto-create GitHub Issue for unmatched errors</label>
    </div>
    
    <button class="btn-primary" onclick="saveSettings()" style="margin-top: 1rem;">Save Settings</button>
  </div>
  
  <!-- Feedback Queue Panel -->
  <div id="feedbackPanel" class="feedback-panel" style="display: none;">
    <div class="feedback-header">
      <h3>📊 Feedback Queue — Continuous Improvement</h3>
      <button class="settings-close" onclick="toggleFeedback()">✕</button>
    </div>
    <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem;">
      Unmatched errors are logged here for review. Use this to identify new patterns to add.
    </p>
    <div style="margin-bottom: 1rem;">
      <button class="feedback-action-btn" onclick="loadGitHubIssues()" style="margin-right: 0.5rem;">🔗 View GitHub Issues</button>
    </div>
    <div class="feedback-stats" id="feedbackStats">
      <div class="stat-item">
        <div class="stat-value" id="statPending">-</div>
        <div class="stat-label">Pending</div>
      </div>
      <div class="stat-item">
        <div class="stat-value" id="statTotal">-</div>
        <div class="stat-label">Total</div>
      </div>
      <div class="stat-item">
        <div class="stat-value" id="statPatterns">-</div>
        <div class="stat-label">Patterns Created</div>
      </div>
    </div>
    <div class="feedback-list" id="feedbackList">
      <p style="text-align: center; color: var(--text-dim);">Loading...</p>
    </div>
  </div>
  
  <!-- Patterns Explorer Panel -->
  <div id="patternsPanel" class="patterns-panel" style="display: none;">
    <div class="feedback-header">
      <h3>📚 Pattern Explorer — PATTERN_COUNT Patterns</h3>
      <button class="settings-close" onclick="togglePatterns()">✕</button>
    </div>
    <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem;">
      Browse all error patterns. Click a category to filter, or search by keyword.
    </p>
    <input type="text" class="patterns-search" id="patternsSearch" placeholder="🔍 Search patterns by keyword, regex, or error type..." oninput="filterPatterns()">
    <div class="patterns-categories" id="patternsCategories">
      <p style="color: var(--text-dim);">Loading categories...</p>
    </div>
    <div class="patterns-list" id="patternsList">
      <p style="text-align: center; color: var(--text-dim);">Loading patterns...</p>
    </div>
  </div>
  
  <div class="main-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <label class="input-label">
        <span>📋</span> Paste Your Logs
      </label>
      <div>
        <button class="patterns-btn" onclick="togglePatterns()">📚 Patterns</button>
        <button class="settings-btn" onclick="toggleSettings()">⚙️ AI Settings</button>
        <button class="feedback-btn" onclick="toggleFeedback()">📊 Feedback<span class="feedback-badge" id="feedbackBadge" style="display:none;">0</span></button>
      </div>
    </div>
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
  
  <div class="patterns-count" onclick="togglePatterns()" style="cursor: pointer;">
    Powered by <span>PATTERN_COUNT</span> intelligent error patterns covering Kubernetes, Elasticsearch, AWS, Kafka, Vault, Terraform, PostgreSQL, MongoDB, Docker, Nginx, Java/Spring, Python, Prometheus, Gardener, and more. <span style="color: var(--accent-light);">Click to explore →</span>
  </div>
</div>

<script>
// Load saved API keys on page load
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('anthropicKey').value = localStorage.getItem('anthropic_key') || '';
  document.getElementById('openaiKey').value = localStorage.getItem('openai_key') || '';
  document.getElementById('githubToken').value = localStorage.getItem('github_token') || '';
  document.getElementById('autoCreateIssue').checked = localStorage.getItem('auto_create_issue') === 'true';
});

function toggleSettings() {
  const panel = document.getElementById('settingsPanel');
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  // Close other panels if open
  document.getElementById('feedbackPanel').style.display = 'none';
  document.getElementById('patternsPanel').style.display = 'none';
}

// ─── Patterns Explorer Functions ────────────────────────────────────────────
let allPatterns = null;
let currentCategory = null;

function togglePatterns() {
  const panel = document.getElementById('patternsPanel');
  const isHidden = panel.style.display === 'none';
  panel.style.display = isHidden ? 'block' : 'none';
  // Close other panels if open
  document.getElementById('settingsPanel').style.display = 'none';
  document.getElementById('feedbackPanel').style.display = 'none';
  
  if (isHidden && !allPatterns) {
    loadPatterns();
  }
}

async function loadPatterns() {
  try {
    const resp = await fetch('/patterns');
    allPatterns = await resp.json();
    
    renderCategories();
    renderPatterns();
  } catch (e) {
    console.error('Failed to load patterns:', e);
    document.getElementById('patternsList').innerHTML = '<p style="color: var(--red);">Failed to load patterns</p>';
  }
}

function renderCategories() {
  const container = document.getElementById('patternsCategories');
  if (!allPatterns || !allPatterns.categories) return;
  
  let html = `<div class="category-chip ${!currentCategory ? 'active' : ''}" onclick="selectCategory(null)">All <span class="count">${allPatterns.total}</span></div>`;
  
  allPatterns.categories.forEach(cat => {
    const isActive = currentCategory === cat.name ? 'active' : '';
    html += `<div class="category-chip ${isActive}" onclick="selectCategory('${cat.name}')">${cat.name} <span class="count">${cat.count}</span></div>`;
  });
  
  container.innerHTML = html;
}

function selectCategory(category) {
  currentCategory = category;
  renderCategories();
  renderPatterns();
}

function filterPatterns() {
  renderPatterns();
}

function renderPatterns() {
  const container = document.getElementById('patternsList');
  const searchTerm = document.getElementById('patternsSearch').value.toLowerCase();
  
  if (!allPatterns || !allPatterns.categories) {
    container.innerHTML = '<p style="color: var(--text-dim);">No patterns loaded</p>';
    return;
  }
  
  let patterns = [];
  allPatterns.categories.forEach(cat => {
    if (!currentCategory || currentCategory === cat.name) {
      cat.patterns.forEach(p => {
        patterns.push({...p, category: cat.name});
      });
    }
  });
  
  // Filter by search term
  if (searchTerm) {
    patterns = patterns.filter(p => 
      p.summary.toLowerCase().includes(searchTerm) ||
      p.regex.toLowerCase().includes(searchTerm) ||
      p.category.toLowerCase().includes(searchTerm)
    );
  }
  
  if (patterns.length === 0) {
    container.innerHTML = '<p style="text-align: center; color: var(--text-dim); padding: 2rem;">No patterns match your search.</p>';
    return;
  }
  
  let html = '';
  patterns.slice(0, 100).forEach(p => {
    const severityClass = p.severity.toLowerCase();
    html += `
      <div class="pattern-item">
        <div class="pattern-item-header">
          <span class="pattern-summary">${escapeHtml(p.summary)}</span>
          <span class="pattern-severity ${severityClass}">${p.severity}</span>
        </div>
        <div class="pattern-regex">${escapeHtml(p.regex)}</div>
      </div>
    `;
  });
  
  if (patterns.length > 100) {
    html += `<p style="text-align: center; color: var(--text-dim); padding: 1rem;">Showing 100 of ${patterns.length} patterns. Use search to narrow down.</p>`;
  }
  
  container.innerHTML = html;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ─── Feedback Queue Functions ───────────────────────────────────────────────
function toggleFeedback() {
  const panel = document.getElementById('feedbackPanel');
  const isHidden = panel.style.display === 'none';
  panel.style.display = isHidden ? 'block' : 'none';
  // Close other panels if open
  document.getElementById('settingsPanel').style.display = 'none';
  document.getElementById('patternsPanel').style.display = 'none';
  
  if (isHidden) {
    loadFeedbackStats();
    loadFeedbackList();
  }
}

async function loadFeedbackStats() {
  try {
    const resp = await fetch('/feedback/stats');
    const stats = await resp.json();
    
    document.getElementById('statPending').textContent = stats.pending || 0;
    document.getElementById('statTotal').textContent = stats.total || 0;
    document.getElementById('statPatterns').textContent = stats.pattern_created || 0;
    
    // Update badge
    const badge = document.getElementById('feedbackBadge');
    if (stats.pending > 0) {
      badge.style.display = 'inline';
      badge.textContent = stats.pending;
    } else {
      badge.style.display = 'none';
    }
  } catch (e) {
    console.error('Failed to load feedback stats:', e);
  }
}

async function loadFeedbackList() {
  const list = document.getElementById('feedbackList');
  
  try {
    const resp = await fetch('/feedback');
    const errors = await resp.json();
    
    if (!errors || errors.length === 0) {
      list.innerHTML = '<p style="text-align: center; color: var(--text-dim); padding: 2rem;">No unmatched errors logged yet. Great! All errors are matching patterns.</p>';
      return;
    }
    
    let html = '';
    errors.forEach(err => {
      const time = new Date(err.timestamp).toLocaleDateString();
      const snippet = (err.log_snippet || '').substring(0, 200);
      
      html += `
      <div class="feedback-item" data-id="${err.id}">
        <div class="feedback-item-header">
          <div class="feedback-item-meta">
            <span class="feedback-count">×${err.count || 1}</span>
            <span class="feedback-time">${time}</span>
            <span style="font-size: 0.7rem; color: var(--text-dim);">${err.source || 'unknown'}</span>
          </div>
        </div>
        <div class="feedback-snippet">${escapeHtml(snippet)}${snippet.length >= 200 ? '...' : ''}</div>
        <div class="feedback-actions">
          <button class="feedback-action-btn primary" onclick="suggestPattern(${err.id}, this)">💡 Suggest Pattern</button>
          <button class="feedback-action-btn" onclick="markReviewed(${err.id})">✓ Reviewed</button>
          <button class="feedback-action-btn" onclick="markIgnored(${err.id})">✕ Ignore</button>
        </div>
        <div class="pattern-suggestion" id="suggestion-${err.id}" style="display: none;"></div>
      </div>`;
    });
    
    list.innerHTML = html;
  } catch (e) {
    list.innerHTML = '<p style="text-align: center; color: var(--red);">Failed to load feedback queue.</p>';
    console.error('Failed to load feedback list:', e);
  }
}

async function suggestPattern(errorId, btn) {
  const suggestionDiv = document.getElementById('suggestion-' + errorId);
  
  // Toggle if already showing
  if (suggestionDiv.style.display === 'block') {
    suggestionDiv.style.display = 'none';
    return;
  }
  
  const apiKey = localStorage.getItem('anthropic_key') || localStorage.getItem('openai_key');
  if (!apiKey) {
    suggestionDiv.innerHTML = '<p style="color: var(--yellow);">⚠️ Configure an AI API key in Settings to generate pattern suggestions.</p>';
    suggestionDiv.style.display = 'block';
    return;
  }
  
  btn.textContent = '⏳ Generating...';
  btn.disabled = true;
  
  try {
    const resp = await fetch('/feedback/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        error_id: errorId,
        api_key: apiKey
      })
    });
    const data = await resp.json();
    
    if (data.suggestion) {
      suggestionDiv.innerHTML = `<strong style="color: var(--green);">📋 Suggested Pattern (copy to log_analyser.py):</strong>\\n\\n${escapeHtml(data.suggestion)}`;
    } else {
      suggestionDiv.innerHTML = `<p style="color: var(--red);">❌ ${data.error || 'Failed to generate suggestion'}</p>`;
    }
    suggestionDiv.style.display = 'block';
  } catch (e) {
    suggestionDiv.innerHTML = '<p style="color: var(--red);">❌ Failed to connect to server.</p>';
    suggestionDiv.style.display = 'block';
  } finally {
    btn.textContent = '💡 Suggest Pattern';
    btn.disabled = false;
  }
}

async function markReviewed(errorId) {
  await updateFeedbackStatus(errorId, 'reviewed');
}

async function markIgnored(errorId) {
  await updateFeedbackStatus(errorId, 'ignored');
}

async function updateFeedbackStatus(errorId, status) {
  try {
    await fetch('/feedback/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error_id: errorId, status: status })
    });
    
    // Remove the item from the list with animation
    const item = document.querySelector(`.feedback-item[data-id="${errorId}"]`);
    if (item) {
      item.style.opacity = '0';
      item.style.transform = 'translateX(-20px)';
      setTimeout(() => {
        item.remove();
        loadFeedbackStats();
      }, 300);
    }
  } catch (e) {
    console.error('Failed to update feedback status:', e);
  }
}

// Load feedback badge count on page load
document.addEventListener('DOMContentLoaded', function() {
  loadFeedbackStats();
});

function saveSettings() {
  const anthropicKey = document.getElementById('anthropicKey').value.trim();
  const openaiKey = document.getElementById('openaiKey').value.trim();
  const githubToken = document.getElementById('githubToken').value.trim();
  const autoCreateIssue = document.getElementById('autoCreateIssue').checked;
  
  if (anthropicKey) localStorage.setItem('anthropic_key', anthropicKey);
  else localStorage.removeItem('anthropic_key');
  
  if (openaiKey) localStorage.setItem('openai_key', openaiKey);
  else localStorage.removeItem('openai_key');
  
  if (githubToken) localStorage.setItem('github_token', githubToken);
  else localStorage.removeItem('github_token');
  
  localStorage.setItem('auto_create_issue', autoCreateIssue ? 'true' : 'false');
  
  toggleSettings();
  
  // Show confirmation
  const results = document.getElementById('results');
  const githubMsg = githubToken ? ' GitHub integration enabled.' : '';
  results.innerHTML = `<div class="summary-bar" style="background: var(--green-glow); border-color: var(--green);"><div class="icon" style="background: var(--green);">✓</div><div><div class="count" style="color: var(--green);">Settings Saved</div><div class="label">Configuration updated.${githubMsg}</div></div></div>`;
  setTimeout(() => results.innerHTML = '', 3000);
}

function hasApiKeys() {
  return localStorage.getItem('anthropic_key') || localStorage.getItem('openai_key');
}

function hasGitHubToken() {
  return localStorage.getItem('github_token');
}

async function loadGitHubIssues() {
  const githubToken = localStorage.getItem('github_token');
  if (!githubToken) {
    alert('Please configure GitHub Token in Settings first.');
    return;
  }
  
  try {
    const resp = await fetch('/github/issues', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ github_token: githubToken })
    });
    const data = await resp.json();
    
    if (data.success && data.issues.length > 0) {
      // Open first issue in new tab, or show list
      const list = data.issues.map(i => `• #${i.number}: ${i.title}`).join('\\n');
      if (confirm(`Found ${data.issues.length} unmatched error issues:\\n\\n${list.substring(0, 500)}\\n\\nOpen GitHub Issues page?`)) {
        window.open(`https://github.com/ragunath79-byte/AI-log-analyzer/issues?q=is%3Aissue+label%3Aunmatched-error`, '_blank');
      }
    } else if (data.success) {
      alert('No unmatched error issues found in GitHub.');
    } else {
      alert('Failed to fetch GitHub issues: ' + (data.error || 'Unknown error'));
    }
  } catch (e) {
    alert('Error connecting to server: ' + e.message);
  }
}

async function analyze() {
  const logs = document.getElementById('logInput').value.trim();
  if (!logs) return;
  
  const btn = document.getElementById('analyzeBtn');
  const spinner = document.getElementById('spinner');
  btn.disabled = true;
  spinner.classList.add('active');
  
  try {
    const payload = { 
      logs,
      anthropic_key: localStorage.getItem('anthropic_key') || '',
      openai_key: localStorage.getItem('openai_key') || '',
      github_token: localStorage.getItem('github_token') || '',
      auto_create_issue: localStorage.getItem('auto_create_issue') === 'true'
    };
    
    const resp = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
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
  
  // If AI analysis is available (when no patterns matched)
  if (data.ai_analysis) {
    el.innerHTML = `
      <div class="summary-bar" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%); border-color: var(--accent-glow);">
        <div class="icon" style="background: var(--accent);">🤖</div>
        <div>
          <div class="count" style="color: var(--accent-light);">AI Analysis (${escapeHtml(data.ai_provider)})</div>
          <div class="label">No built-in patterns matched — analyzed with AI</div>
        </div>
      </div>
      <div class="issue-card">
        <div class="field">
          <div class="field-value" style="white-space: pre-wrap; line-height: 1.8;">${escapeHtml(data.ai_analysis)}</div>
        </div>
      </div>`;
    return;
  }
  
  if (!data.matches || data.matches.length === 0) {
    const hasKeys = hasApiKeys();
    
    // Show AI error if there was one
    if (data.ai_error) {
      el.innerHTML = `<div class="no-match-card" style="border-color: var(--red-glow);">
        <h3 style="color: var(--red);">❌ AI Analysis Failed</h3>
        <p>${escapeHtml(data.ai_error)}</p>
        <p style="font-size: 0.85rem; margin-top: 1rem;">Check that your API key is valid and has credits.</p>
        <button class="btn-primary" onclick="toggleSettings()" style="margin-top: 1rem;">
          <span>⚙️</span> Check AI Settings
        </button>
      </div>`;
      return;
    }
    
    if (hasKeys) {
      el.innerHTML = '<div class="no-match-card"><h3>⚠️ No Match Found</h3><p>This error doesn\\'t match any of our 563 built-in patterns, and AI analysis didn\\'t return results.<br>Try pasting a more complete error log.</p></div>';
    } else {
      el.innerHTML = `<div class="no-match-card">
        <h3>⚠️ No Match Found</h3>
        <p>This error doesn't match any of our 563 built-in patterns.<br>Enable AI analysis to get insights on unknown errors!</p>
        <button class="btn-primary" onclick="toggleSettings()">
          <span>⚙️</span> Configure AI Settings
        </button>
      </div>`;
    }
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
        """Serve the HTML page or API endpoints."""
        # Patterns summary endpoint
        if self.path == '/patterns':
            summary = get_patterns_summary()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(summary).encode())
            return
        
        # Feedback queue stats
        if self.path == '/feedback/stats':
            stats = get_feedback_stats()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            return
        
        # Feedback queue list
        if self.path == '/feedback':
            errors = get_unmatched_errors(status_filter='pending', limit=50)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(errors).encode())
            return
        
        # Serve main HTML page
        page = HTML_PAGE.replace('PATTERN_COUNT', str(len(PATTERNS)))
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(page.encode())

    def do_POST(self):
        """Handle log analysis and feedback requests."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()
        
        # GitHub Issues endpoint
        if self.path == '/github/issues':
            try:
                data = json.loads(body)
                github_token = data.get('github_token')
                result = get_github_issues(github_token=github_token)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e), "issues": []}).encode())
            return
        
        # Update feedback status
        if self.path == '/feedback/update':
            try:
                data = json.loads(body)
                error_id = data.get('error_id')
                status = data.get('status')
                success = update_unmatched_error(error_id, status=status)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": success}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        
        # Generate pattern suggestion
        if self.path == '/feedback/suggest':
            try:
                data = json.loads(body)
                error_id = data.get('error_id')
                api_key = data.get('api_key')
                
                # Get the error log
                errors = get_unmatched_errors(limit=500)
                error_log = None
                for err in errors:
                    if err.get('id') == error_id:
                        error_log = err.get('log_snippet', '')
                        break
                
                if not error_log:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Error not found"}).encode())
                    return
                
                suggestion = suggest_pattern_from_log(error_log, api_key=api_key)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"suggestion": suggestion}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        
        # Log analysis
        if self.path != '/analyze':
            self.send_response(404)
            self.end_headers()
            return

        try:
            data = json.loads(body)
            logs = data.get('logs', '')
            anthropic_key = data.get('anthropic_key', '')
            openai_key = data.get('openai_key', '')
            github_token = data.get('github_token', '')
            auto_create_issue = data.get('auto_create_issue', False)
        except json.JSONDecodeError:
            logs = body
            anthropic_key = ''
            openai_key = ''
            github_token = ''
            auto_create_issue = False

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
            ],
            "ai_analysis": None,
            "ai_provider": None,
            "ai_error": None,
            "github_issue": None
        }

        # If no pattern matches, log for feedback loop and try AI analysis
        if not matches:
            # Debug: Show what we received
            print(f"  🔍 DEBUG: github_token={'***' + github_token[-4:] if github_token else 'None'}")
            print(f"  🔍 DEBUG: auto_create_issue={auto_create_issue}")
            
            # Log to local file and optionally create GitHub issue
            log_result = log_unmatched_error(
                logs, 
                source="web",
                create_issue=auto_create_issue,
                github_token=github_token
            )
            print(f"  📝 Unmatched error logged for feedback")
            print(f"  🔍 DEBUG: log_result={log_result}")
            
            # Include GitHub issue info in response
            if log_result and log_result.get("github_issue"):
                result["github_issue"] = log_result["github_issue"]
                print(f"  🔗 GitHub Issue created: #{log_result['github_issue']['number']}")
            
            if anthropic_key or openai_key:
                print(f"  🤖 No patterns matched. Trying AI analysis...")
                try:
                    ai_result = analyze_with_ai(logs, anthropic_key=anthropic_key, openai_key=openai_key)
                    if ai_result:
                        ai_name, ai_response = ai_result
                        result["ai_analysis"] = ai_response
                        result["ai_provider"] = ai_name
                        print(f"  ✅ AI analysis successful ({ai_name})")
                    else:
                        result["ai_error"] = "AI did not return a result. Check API key validity."
                        print(f"  ❌ AI analysis returned no result")
                except Exception as e:
                    result["ai_error"] = str(e)
                    print(f"  ❌ AI analysis error: {e}")

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
