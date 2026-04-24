<p align="center">
  <img src="images/logo.svg" alt="MyAgent" width="400">
</p>

<p align="center">
  <strong>Autonomous AI Agent with Multi-Channel Gateway</strong></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=socketdotio&logoColor=white" alt="WebSocket">
</p>

<p align="center">
  <a href="README.zh-CN.md">简体中文</a>
</p>

**MyAgent** is an autonomous AI agent platform that connects to the messaging channels you already use. It features a powerful Gateway for multi-platform messaging, a TUI for terminal enthusiasts, and a Web UI for browser-based interaction.

Supported platforms: **Feishu/Lark, Slack, Discord, Telegram, DingTalk, WeCom, Weixin, QQ, Matrix, Webhook**.

## Features

- **Multi-Channel Gateway** — Unified inbox for all messaging platforms (Telegram, Discord, Slack, Feishu, etc.)
- **TUI Interface** — Rich terminal UI with ASCII art logo
- **Web UI** — Real-time WebSocket chat with JWT authentication and multi-user session isolation
- **Multi-LLM Support** — 19 Providers (Intl + China): Anthropic, OpenAI, DeepSeek, Gemini, xAI, Qwen, Ollama, OpenRouter, Zhipu/Zhipu-CN, Moonshot/Moonshot-CN, MiniMax/MiniMax-CN, Alibaba/Alibaba-CN, HuggingFace, NVIDIA, Arcee, Xiaomi
- **Context Compression** — Automatic conversation compaction with AutoCompactor
- **Session Management** — Per-user, per-group, per-thread sessions with persistent bindings
- **Tool Calling** — Bash, file edit, web search, image analysis, Git operations
- **Permission System** — Inline approval requests in Telegram and Web UI
- **GitHub Integration** — Webhook-based PR/Issue analysis and auto-comments
- **Production Ready** — Docker, health checks, metrics, structured logging

## Screenshots

### Web UI

![MyAgent Web UI](images/myagent-web-ui-2026-04-23T07-29-36-702Z.png)

### Web UI - Codebase Search

![Codebase Search](images/webui-codebase-search-2026-04-23T06-32-00-502Z.png)

### Web UI - Memory Management

![Memory Tab](images/webui-memory-tab-2026-04-23T04-10-30-994Z.png)

## Quick Start

```bash
# Install
pip install myagent

# Initialize (interactive wizard)
myagent init

# Verify setup
myagent doctor

# Start services
myagent gateway --port 18789    # Gateway server
myagent web --port 8000          # Web UI

# Or use the TUI
myagent --tui
```

Open http://localhost:8000 in your browser.

## Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** — First-time setup guide
- **[Production Deployment](docs/PRODUCTION.md)** — Docker, systemd, SSL, monitoring
- **[Configuration Reference](docs/CONFIGURATION.md)** — Complete config options

## CLI Commands

```bash
myagent init              # Interactive setup wizard
myagent doctor            # Diagnose configuration
myagent web               # Start Web UI server
myagent gateway           # Start Gateway server
myagent --tui             # Start TUI interface
myagent --version         # Show version
```

## Configuration

All user configuration lives in `~/.myagent/`:

```
~/.myagent/
├── config.yaml          # Agent settings (model, context, memory)
├── gateway.yaml         # Gateway platforms, sessions
├── .env                 # API keys and secrets
├── sessions/            # Session storage
├── logs/                # Log files
└── workspace/           # Agent workspace
```

### Environment Variables

```bash
# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
ZHIPU_API_KEY=...

# Gateway
FEISHU_APP_ID=cli_...
FEISHU_APP_SECRET=...
SLACK_BOT_TOKEN=xoxb-...
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...

# GitHub Integration
GITHUB_TOKEN=ghp_...
GITHUB_APP_ID=...
GITHUB_WEBHOOK_SECRET=...

# MyAgent
MYAGENT_HOME=/custom/path
MYAGENT_MODEL_DEFAULT=anthropic/claude-sonnet-4
```

## Docker

```bash
docker build -t myagent .
docker run -d \
  -p 8000:8000 \
  -p 18789:18789 \
  -v ~/.myagent:/app/.myagent \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  myagent
```

Or use `docker-compose up -d`.

## Development

```bash
git clone https://github.com/wjt0321/MyAgent.git
cd myagent
pip install -e ".[dev]"
pytest
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Feishu    │     │    Slack    │     │   Discord   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Gateway   │
                    │  (WebSocket)│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐
       │    TUI      │ │ Web UI │ │  Engine  │
       │  (Terminal) │ │(Browser│ │  (LLM)   │
       └─────────────┘ └────────┘ └──────────┘
```

## Security

MyAgent connects to real messaging platforms. Treat inbound messages as **untrusted input**.

- **Default**: Unknown senders receive a pairing request
- **Recommended**: Use allowlists and sandbox tools
- **Never commit**: `.env` files or API keys to version control

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgments

Inspired by [Hermes Agent](https://github.com/NousResearch/hermes-agent), [OpenClaw](https://github.com/openclaw/openclaw), [Claude Code](https://github.com/anthropics/claude-code), and [OpenHarness](https://github.com/HKUDS/OpenHarness).
