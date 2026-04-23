# MyAgent — Autonomous AI Agent Platform

<pre align="center">
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███╗   ███╗██╗   ██╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗   ║
║   ████╗ ████║╚██╗ ██╔╝██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝   ║
║   ██╔████╔██║ ╚████╔╝ ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║      ║
║   ██║╚██╔╝██║  ╚██╔╝  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║      ║
║   ██║ ╚═╝ ██║   ██║   ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║      ║
║   ╚═╝     ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝      ║
║                                                              ║
║   ┌─────────────────────────────────────────────────────┐    ║
║   │  01001101 01111001 01000001 01100111 01100101 01101110 01110100  │    ║
║   └─────────────────────────────────────────────────────┘    ║
║                                                              ║
║              Autonomous Agent Platform                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
</pre>

<p align="center">
  <strong>Autonomous AI Agent with Multi-Channel Gateway</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License"></a>
</p>

**MyAgent** is an autonomous AI agent platform that connects to the messaging channels you already use. It features a powerful Gateway for multi-platform messaging, a TUI for terminal enthusiasts, and a Web UI for browser-based interaction.

Supported platforms: **Feishu/Lark, Slack, Discord, Telegram, DingTalk, WeCom, Weixin, QQ, Matrix, Webhook**.

## Features

- **Multi-Channel Gateway** — Unified inbox for all messaging platforms
- **TUI Interface** — Rich terminal UI with ASCII art logo
- **Web UI** — Real-time WebSocket chat with settings and reset
- **Multi-LLM Support** — OpenAI, Anthropic, DeepSeek, Gemini, Qwen, Ollama, Azure, OpenRouter
- **Context Compression** — Automatic conversation compaction
- **Session Management** — Per-user, per-group, per-thread sessions
- **Tool Calling** — Bash, file edit, web search, image analysis
- **Production Ready** — Docker, health checks, metrics, structured logging

## Screenshots

### Web UI

<p align="center">
  <img src="https://raw.githubusercontent.com/wjt0321/MyAgent/main/images/myagent-web-ui-2026-04-23T07-29-36-702Z.png" alt="MyAgent Web UI" width="800">
</p>

### Web UI - Codebase Search

<p align="center">
  <img src="https://raw.githubusercontent.com/wjt0321/MyAgent/main/images/webui-codebase-search-2026-04-23T06-32-00-502Z.png" alt="Codebase Search" width="800">
</p>

### Web UI - Memory Management

<p align="center">
  <img src="https://raw.githubusercontent.com/wjt0321/MyAgent/main/images/webui-memory-tab-2026-04-23T04-10-30-994Z.png" alt="Memory Tab" width="800">
</p>

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

# Gateway
FEISHU_APP_ID=cli_...
FEISHU_APP_SECRET=...
SLACK_BOT_TOKEN=xoxb-...
TELEGRAM_BOT_TOKEN=...

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

Inspired by [Hermes Agent](https://github.com/hermes) and [OpenClaw](https://github.com/openclaw/openclaw).
