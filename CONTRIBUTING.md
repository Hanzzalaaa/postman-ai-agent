# Contributing

Contributions are welcome! Here's how to get started.

## Setup

```bash
git clone https://github.com/Hanzzalaaa/postman-ai-agent
cd postman-ai-agent
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
pip install -e ".[dev]"
```

## Project Structure

```
postman-ai-agent/
├── postman_agent/          # PyPI CLI package
│   ├── agent/graph.py      # LangGraph agent
│   ├── tools/code_parser.py# Route extraction logic
│   └── cli.py              # CLI entry point
├── backend/                # FastAPI web server
│   └── app/
│       ├── main.py         # API endpoints
│       └── agent/graph.py  # Agent (web version)
└── frontend/               # React + Vite UI
    └── src/
```

## Making Changes

1. Fork the repo and create a branch: `git checkout -b feat/your-feature`
2. Make your changes
3. Test manually: `postman-agent generate --file your_routes.js`
4. Open a Pull Request

## Adding Framework Support

To add a new framework, update `extract_routes()` in:
- `postman_agent/tools/code_parser.py` (CLI)
- `backend/app/agent/graph.py` (web backend)

## Reporting Bugs

Open an issue with:
- Framework and language used
- Sample code that failed to parse
- Expected vs actual output
