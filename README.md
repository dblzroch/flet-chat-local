# flet-chat-local

> Local LLM chat client for Ollama with streaming and conversation history.

[![CI](https://github.com/dblzroch/flet-chat-local/actions/workflows/ci.yml/badge.svg)](https://github.com/dblzroch/flet-chat-local/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](pyproject.toml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Cliente de chat para LLM local (Ollama) construído com [Flet](https://flet.dev/). Converse com modelos locais,
veja streaming de tokens em tempo real, salve conversas e edite o system prompt.

## Quickstart

```bash
# Clone
git clone https://github.com/dblzroch/flet-chat-local.git
cd flet-chat-local

# Install (uv)
uv sync --dev

# Run the desktop app
uv run flet-chat-local
```

## How it works

- **UI**: Flet (Flutter-based) desktop/mobile GUI.
- **Storage**: SQLite database for conversations and messages.
- **Backend**: Ollama API (http://localhost:11434) with streaming chat.
- **Features**: List available models, stream responses, save/load conversations,
  editable system prompt, export conversation to Markdown.
- **Tests**: `pytest` with coverage gate at 80%, `respx` for HTTP mocking.
- **CI**: GitHub Actions runs ruff, mypy and pytest on every push/PR.

## Tests & quality

```bash
make test      # pytest with coverage
make lint      # ruff + mypy
make fmt       # ruff format
```

## License

MIT
