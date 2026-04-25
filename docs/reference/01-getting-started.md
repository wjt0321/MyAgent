# Getting Started with MyAgent

Welcome to MyAgent — an autonomous AI agent platform with multi-channel Gateway support.

> 本文档为快速入门指南，帮助你 5 分钟内启动 MyAgent。
> 详细配置参考: [02-configuration.md](02-configuration.md)

---

## Quick Start (5 minutes)

### 1. Install

```bash
pip install myagent
```

Or from source:

```bash
git clone https://github.com/myagent/myagent.git
cd myagent
pip install -e ".[dev]"
```

### 2. Initialize

Recommended first boot:

```bash
myagent init --quick
```

This will:
- Create the base `~/.myagent/` directory structure
- Generate `config.yaml`, `gateway.yaml`, and `.env`
- Prepare the workspace so TUI and Web can enter a recoverable `Setup Required` state

When you want the full onboarding wizard, use:

```bash
myagent init
```

### 3. Verify

```bash
myagent doctor
```

Checks the current setup status, missing directories, missing config files, and missing LLM keys, then prints the next recommended action.

### 4. Start

```bash
# Recommended local entry
myagent --tui

# Or launch the Web UI
myagent web --port 8000
```

Open http://localhost:8000 in your browser.

If setup is incomplete:
- TUI shows `Setup Required` in the transcript and via modal handoff
- Web shows a setup gate before it starts a chat session
- `myagent doctor` tells you the exact next command

---

## Configuration Files

All user configuration lives in `~/.myagent/`:

| File | Purpose |
|------|---------|
| `~/.myagent/soul.md` | Agent personality |
| `~/.myagent/user.md` | User profile |
| `~/.myagent/identity.md` | Agent identity |
| `~/.myagent/config.yaml` | Agent settings |
| `~/.myagent/gateway.yaml` | Gateway platforms |
| `~/.myagent/.env` | API keys |
| `~/.myagent/memory/` | Persistent memory |
| `~/.myagent/sessions/` | Session storage |
| `~/.myagent/logs/` | Log files |
| `~/.myagent/projects/` | Project workspaces |

### Environment Variables

```bash
# LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
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

---

## LLM Providers

| Provider | Env Var | Default Model |
|----------|---------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| Google Gemini | `GEMINI_API_KEY` | `gemini-1.5-pro` |
| Alibaba Qwen | `DASHSCOPE_API_KEY` | `qwen-max` |
| SiliconFlow | `SILICONFLOW_API_KEY` | `deepseek-ai/DeepSeek-V3` |
| Ollama (local) | None | `llama3.2` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` | `gpt-4o` |
| OpenRouter | `OPENROUTER_API_KEY` | `anthropic/claude-sonnet-4` |

---

## Gateway Platforms

### Feishu / Lark

1. Create a Feishu app at [open.feishu.cn/app](https://open.feishu.cn/app)
2. Get App ID and App Secret
3. Enable bot capability

```bash
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Slack

1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Add Bot Token Scopes: `chat:write`, `im:history`

```bash
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```

### Discord

1. Create a bot at [discord.com/developers/applications](https://discord.com/developers/applications)
2. Enable Message Content Intent

```bash
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx.xxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Telegram

1. Message [@BotFather](https://t.me/BotFather)
2. Create a new bot

```bash
TELEGRAM_BOT_TOKEN=xxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `myagent init` fails | Check Python >= 3.11 |
| LLM not responding | Verify API key with `myagent doctor` |
| Gateway not receiving | Check webhook URL and credentials |
| Session not resetting | Check `gateway.yaml` reset_policy |
| High token usage | Adjust `context.auto_compact_threshold` |

---

## Next Steps

- [Configuration Reference](02-configuration.md)
- [Production Deployment](03-production.md)
- [Concept References](04-concept-references.md)
