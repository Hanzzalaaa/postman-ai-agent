# 🤖 Postman Collection AI Agent

> An AI-powered CLI tool that automatically analyzes your backend code, detects API routes, groups them into smart folders, and imports a complete Postman Collection — in seconds.

[![PyPI version](https://badge.fury.io/py/postman-agent.svg)](https://pypi.org/project/postman-agent/)
[![PyPI downloads](https://img.shields.io/pypi/dm/postman-agent)](https://pypi.org/project/postman-agent/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-Hanzzalaaa-black)](https://github.com/Hanzzalaaa)

---

## 📖 Why This Was Built

Every backend developer faces the same problem: after building an API, you have to manually create Postman Collections — naming every route, adding request bodies, setting up folders, configuring auth headers. For a project with 30-50 routes, this takes **hours**.

This tool solves that. Point it at any backend project and it automatically:
- Scans all files by **content** (not filename)
- Detects base paths from `app.use()` and combines with route paths
- Groups routes into **smart folders** (Authentication, Products, Orders...)
- Generates **realistic request bodies** based on route context
- Detects **auth type** (JWT, OAuth, API Key)
- Enhances routes with **AI** (names, descriptions, bodies)
- Imports the complete collection directly into **your Postman workspace**

---

## ⚡ Quick Start

```bash
# 1. Install
pip install postman-agent

# 2. Setup (one time only)
postman-agent setup
# → Choose LLM provider (Groq, Gemini, Ollama, OpenAI...)
# → Enter API key for chosen provider
# → Enter Postman API Key (free at postman.com → Settings → API Keys)

# 3. Generate from any project
cd your-backend-project
postman-agent generate --scan .

# Output:
# ✅ Found 53 routes!
# 📁 Authentication (7 routes)
# 📁 Products (5 routes)
# 📁 Orders (4 routes)
# 🚀 Imported to Postman!
# 🔗 https://go.postman.co/collection/xxxxx
```

---

## 🎯 Features

| Feature | Details |
|---------|---------|
| 🔍 Smart File Detection | Scans files by content — works with any filename |
| 📍 Base Path Detection | Detects `app.use('/api/auth', authRoutes)` automatically |
| 📁 Auto Folder Grouping | Authentication, Products, Orders, Payments... |
| 🔐 Auth Type Detection | JWT, OAuth, API Key auto-detected |
| 📝 Smart Route Names | Login, Register, Get All Products, Delete Order... |
| 🎯 Path Params | `:id`, `{userId}` detected and added as `{{id}}` |
| 🔍 Query Params | `?page=1&limit=10&q=search` auto-detected |
| 📦 Request Bodies | Realistic bodies based on route context |
| 🤖 AI Enhancement | LLM-powered names, descriptions & request bodies |
| 🌍 Environment Variables | `base_url`, `token`, `refresh_token`, dynamic params |
| 🔄 Upsert Collections | Updates existing collection — no duplicates |
| 🚀 Auto Import | Direct import to Postman workspace via API |
| 🔗 Instant Link | Get Postman collection URL after import |
| 👁️ Watch Mode | Auto re-generate on file changes |
| 💾 Save to File | Export collection as JSON with `--output` |
| 🧪 Dry Run | Preview routes without importing |
| ⚡ Fast | Entire project analyzed in seconds |

Every request includes:
- ✅ Proper HTTP method
- ✅ Full path with base URL (`{{base_url}}`)
- ✅ Auth header (`Bearer {{token}}`)
- ✅ Realistic request body
- ✅ Path params as variables (`{{id}}`)
- ✅ Query params (`?page=1&limit=10`)
- ✅ Environment variables

---

## 🌐 Supported Frameworks

| Framework | Language | Detection Pattern |
|-----------|----------|-------------------|
| ✅ Express.js | JavaScript | `router.get('/path', handler)` |
| ✅ Fastify | JavaScript | `fastify.get('/path', handler)` / `register()` with prefix |
| ✅ NestJS | TypeScript | `@Get('/path')`, `@Post('/path')` decorators |
| ✅ FastAPI | Python | `@app.get('/path')` |
| ✅ Flask | Python | `@app.route('/path', methods=['GET'])` |
| ✅ Django | Python | `path('endpoint/', view)` |

---

## 🤖 Supported LLM Providers

| # | Provider | Free | Default Model |
|---|----------|------|---------------|
| 1 | **Groq** | ✅ Free | `llama-3.1-8b-instant` |
| 2 | **Google Gemini** | ✅ Free | `gemini-2.0-flash` |
| 3 | **GLM / Zhipu AI** | ✅ Free | `glm-4-flash` |
| 4 | **Ollama (Local)** | ✅ Free | `llama3.2` |
| 5 | **Cerebras** | ✅ Free | `llama3.1-8b` |
| 6 | **SambaNova** | ✅ Free | `Meta-Llama-3.1-8B-Instruct` |
| 7 | **Cloudflare AI** | ✅ Free | `@cf/meta/llama-3.1-8b-instruct` |
| 8 | **Together AI** | ✅ Free | `Llama-3.2-3B-Instruct-Turbo` |
| 9 | **Fireworks AI** | ✅ Free | `llama-v3p1-8b-instruct` |
| 10 | **Hugging Face** | ✅ Free | `Llama-3.2-3B-Instruct` |
| 11 | **OpenRouter** | ✅ Free | `gemma-2-9b-it:free` |
| 12 | **OpenAI** | 💳 Paid | `gpt-4o-mini` |
| 13 | **Anthropic Claude** | 💳 Paid | `claude-3-haiku-20240307` |
| 14 | **Mistral** | 💳 Paid | `mistral-small-latest` |
| 15 | **Cohere** | 💳 Paid | `command-r-plus` |

```bash
postman-agent generate --scan . --provider gemini
postman-agent generate --scan . --provider ollama --model deepseek-r1
postman-agent generate --scan . --provider openai --model gpt-4o
```

---

## 🛠️ CLI Commands

### `setup` — Configure provider & API keys
```bash
postman-agent setup
```

### `providers` — List all available providers
```bash
postman-agent providers
```

### `models` — List models for a provider
```bash
postman-agent models --provider groq
postman-agent models --provider gemini
```

### `generate` — Generate Postman Collection
```bash
# Scan entire directory
postman-agent generate --scan .

# Single file
postman-agent generate --file routes/auth.js

# Custom options
postman-agent generate --scan . \
  --provider gemini \
  --model gemini-2.0-flash \
  --base-url https://api.myapp.com \
  --token my_jwt_token \
  --name "My API Collection" \
  --output collection.json \
  --dry-run
```

| Flag | Short | Description |
|------|-------|-------------|
| `--scan` | `-s` | Directory to scan |
| `--file` | `-f` | Single route file |
| `--provider` | `-p` | LLM provider |
| `--model` | `-m` | Model name |
| `--base-url` | `-b` | Base URL (default: `http://localhost:3000`) |
| `--token` | `-t` | JWT token value |
| `--name` | `-n` | Override collection name |
| `--output` | `-o` | Save as JSON file |
| `--dry-run` | `-d` | Preview without importing |
| `--ai` | | Force AI enhancement for large projects (>100 routes) |

### `watch` — Auto re-generate on file changes
```bash
postman-agent watch --scan . --interval 5
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  CLI Entry Point                     │
│              postman_agent/cli.py                    │
│                                                      │
│  • Smart file scanner (content-based)                │
│  • 15 LLM provider support                          │
│  • API key management (setup/update/delete)          │
│  • Watch mode (auto re-generate on changes)          │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               LangGraph AI Agent                     │
│            postman_agent/agent/graph.py              │
│                                                      │
│  ┌─────────┐   ┌────────────┐   ┌──────────┐        │
│  │  agent  │──▶│ ai_enhance │──▶│ generate │──▶ END │
│  │  node   │   │    node    │   │   node   │        │
│  └─────────┘   └────────────┘   └──────────┘        │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                Code Parser                           │
│           postman_agent/tools/code_parser.py         │
│                                                      │
│  1. detect_auth_type()    → JWT / OAuth / API Key    │
│  2. Extract base paths    → app.use('/api/auth', .)  │
│  3. Split by file         → per-file route extract   │
│  4. Combine paths         → /api/auth + /login       │
│  5. detect_folder()       → Authentication folder    │
│  6. generate_name()       → "Login", "Get Products"  │
│  7. extract_path_params() → :id → {{id}}             │
│  8. extract_query_params()→ ?page=1&limit=10         │
│  9. generate_body()       → Realistic request body   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Postman Collection Builder              │
│           build_postman_collection()                 │
│                                                      │
│  • Groups routes into folders                        │
│  • Auth first (Authentication folder always first)   │
│  • Builds Postman v2.1 JSON format                   │
│  • Adds environment variables                        │
│  • Upsert by name (no duplicates)                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               Postman API Import                     │
│           import_to_postman()                        │
│                                                      │
│  POST/PUT https://api.getpostman.com/collections     │
│  → Creates or updates collection                     │
│  → Returns collection URL                            │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| 🧠 Agent Framework | LangGraph | 3-node pipeline: parse → enhance → generate |
| 🤖 LLM | 15 Providers (Groq, Gemini, Ollama...) | AI route enhancement |
| ⚡ Parallel Execution | `concurrent.futures` | Parallel LLM batches (3x faster) |
| 🔧 Code Parser | Python AST + Regex | Route extraction for 6 frameworks |
| 🔗 Integration | Postman REST API via `httpx` | Collection create/update |
| 🐍 CLI | Python + `rich` | Beautiful animated terminal UI |
| 🔑 Config | `python-dotenv` + `pydantic` | Secure API key storage |
| 📦 Package | PyPI | `pip install postman-agent` |

---

## 🔑 API Keys Setup

| Key | Where to Get | Cost |
|-----|-------------|------|
| GROQ_API_KEY | [console.groq.com](https://console.groq.com) → API Keys | Free |
| GOOGLE_API_KEY | [aistudio.google.com](https://aistudio.google.com) → API Keys | Free |
| POSTMAN_API_KEY | [postman.com](https://postman.com) → Settings → API Keys | Free |
| OPENAI_API_KEY | [platform.openai.com](https://platform.openai.com) → API Keys | Paid |

Keys are stored securely at `~/.postman-agent/.env`

---

## 📦 Installation with Extra Providers

```bash
# Default (Groq only)
pip install postman-agent

# With Gemini support
pip install "postman-agent[gemini]"

# With Ollama support
pip install "postman-agent[ollama]"

# All free providers
pip install "postman-agent[all-free]"

# Everything
pip install "postman-agent[all]"
```

---

## 🗓️ Changelog

### v1.0.15 — Performance & Bug Fixes (Latest)
- Parallel LLM batching — 25 routes per batch, max 3 batches simultaneously (3x faster)
- LLM call timeout (60s) — no more infinite hangs
- Progress bar simulation window increased (120s) — accurate for large projects
- Duplicate route fix — `method:path` deduplication before and after AI enhancement
- `userRoutes.js` base path fix — `app.use()` now matches any variable name, not just `*Routes`/`*Router`
- Bare route folder fix — routes like `GET /{{id}}` now correctly inherit folder from base path
- Phantom route fix — bmap fallback only triggers when variable is declared in that file

### v1.0.13 — Stability
- Single batch LLM call for all routes
- Removed unused file section helpers
- Tightened bmap variable matching

### v1.0.12 — Multi-Provider LLM
- 15 LLM providers: Groq, Gemini, GLM, Ollama, Cerebras, SambaNova, Cloudflare, Together, Fireworks, HuggingFace, OpenRouter, OpenAI, Anthropic, Mistral, Cohere
- `providers` command to list all providers
- `models` command to list models per provider
- `--provider` and `--model` flags on generate/watch

### v1.0.5 — Smart Collection
- Base path detection (`app.use('/api/auth', authRoutes)`)
- Full path combining (`/api/auth` + `/login` = `/api/auth/login`)
- Smart folder grouping (Authentication, Products, Orders...)
- Human-readable route names (Login, Get All Products...)
- Path params as Postman variables (`{{id}}`)
- Query params auto-detection (`?page=1&limit=10`)
- Realistic request body generation
- Auth type detection (JWT, OAuth, API Key)
- `watch` command for auto re-generation
- Upsert collections (no duplicates)

### v1.0.3 — Multi-Framework Support
- FastAPI, Flask, Django support added
- Python AST parsing for accurate detection
- Content-based file detection (not filename)
- Fastify `register()` with prefix support

### v1.0.1 — CLI Tool
- Python CLI package (`postman-agent` command)
- Auto-import to Postman via API
- Setup command for API key management
- PyPI package published

### v1.0.0 — Foundation
- Basic Express.js route detection with Regex
- Simple Postman Collection generation
- LangGraph ReAct agent

---

## 🔗 Links

| Resource | Link |
|----------|------|
| 📦 PyPI | [pypi.org/project/postman-agent]() |
| 💼 GitHub | [Hanzzalaaa/postman-ai-agent](https://github.com/Hanzzalaaa/postman-ai-agent) |
| 🌐 Portfolio | [https://hanzzalaaa.github.io/hanzala-portfolio/](https://hanzzalaaa.github.io/hanzala-portfolio/) |

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 👨‍💻 Author

**Hanzala Kashif** — Full Stack Developer & AI Agent Builder

- 📧 hanzalakashif2003@gmail.com
- 💼 [@Hanzzalaaa](https://github.com/Hanzzalaaa)

---

## 📄 License

MIT License — feel free to use and modify!

---

⭐ **If this saved you time, please star the repo!**
"# postman-ai-agents" 