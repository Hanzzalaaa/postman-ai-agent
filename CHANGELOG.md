# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.12] - 2025-06-01

### Added
- 15 LLM providers: Groq, Gemini, GLM, Ollama, Cerebras, SambaNova, Cloudflare, Together, Fireworks, HuggingFace, OpenRouter, OpenAI, Anthropic, Mistral, Cohere
- `providers` command to list all providers
- `models` command to list models per provider
- `--provider` and `--model` flags on generate/watch
- Optional dependencies per provider (`pip install postman-agent[gemini]`)

## [1.0.5] - 2025-01-15

### Added
- Groq LLM integration for AI-enhanced route names, descriptions, and smart request bodies
- `--base-url` and `--token` flags for custom environment variables in collection
- `--name` flag to manually override collection name
- `--output` flag to save collection as JSON file
- `--dry-run` flag to preview routes without importing to Postman
- `watch` command to auto re-generate collection on file changes
- Fastify `register()` with prefix support for base path detection
- Query params (page, limit, q) added to Postman collection requests
- Path params (:id, :productId) converted to Postman variables
- Collection update instead of duplicate create (upsert by name)
- Project name auto-detected from folder name

### Changed
- Routes now grouped into named folders by module (Authentication, Products, Cart etc.)
- Route pattern extended to support fastify, server, instance variable names

### Fixed
- project_name crash when neither --file nor --scan provided
- Path traversal vulnerability in file/directory input handling
- Hardcoded sample credentials replaced with Postman variables

## [1.0.3] - 2025-01-01

### Added
- Fastify framework detection
- Smart content-based API file detection (not filename-based)

### Changed
- Improved route grouping in generated Postman collections
- Better sample request bodies based on route path keywords

### Fixed
- Unicode banner rendering on Windows terminals

## [1.0.2] - 2024-12-15

### Added
- Django `urlpatterns` support
- Flask `@app.route` support

## [1.0.1] - 2024-12-01

### Added
- FastAPI and Flask decorator parsing via Python AST
- Auto-import to Postman workspace via REST API

## [1.0.0] - 2024-11-15

### Added
- Initial release
- Express.js route extraction
- LangGraph ReAct agent
- Groq LLM integration
- Postman Collection v2.1 generation
