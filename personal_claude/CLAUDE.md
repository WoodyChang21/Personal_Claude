# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Workspace Is

This is a personal Claude Code workspace directory, not a traditional application codebase. It contains:
- `.mcp.json` — MCP server configuration for this project scope
- `.mcp-servers/chrome-devtools-mcp/` — A vendored MCP server that bridges Claude to Chrome DevTools Protocol
- `.env` — Environment variables (OpenAI API key, model selection)

## MCP Server Setup (chrome-devtools-mcp)

The `.mcp.json` points to a Python venv that must be created before the MCP server works:

```bash
cd .mcp-servers/chrome-devtools-mcp

# Install dependencies (requires uv)
uv sync

# Or with pip (conda base environment is available)
pip install -r requirements.txt
```

The `.mcp.json` is pre-configured to use the venv Python at:
`.mcp-servers/chrome-devtools-mcp/.venv/Scripts/python.exe`

Chrome must be started with remote debugging on port 9222 (`CHROME_DEBUG_PORT=9222`) before connecting.

## chrome-devtools-mcp Development Commands

```bash
cd .mcp-servers/chrome-devtools-mcp

uv run ruff format .      # Format
uv run ruff check .       # Lint
uv run mypy src/          # Type check
uv run pytest             # Tests
make check                # Run all checks
make package              # Build .dxt extension
```

## Architecture Note

The MCP server (`server.py`) is the sole entry point. It exposes tools over MCP protocol that Claude uses to control Chrome via the Chrome DevTools Protocol (CDP) over WebSocket on `localhost:9222`. No web server is involved — the server runs as a subprocess spawned by Claude Code.
