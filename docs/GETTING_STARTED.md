# Getting Started with MyAgent

Welcome to MyAgent — an autonomous AI agent platform with multi-channel Gateway support.

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

Run the interactive setup wizard:

```bash
myagent init
```

This will:
- Create `~/.myagent/` directory structure
- Configure your LLM provider (OpenAI, Anthropic, DeepSeek, etc.)
- Set up Gateway platforms (Feishu, Slack, Discord, etc.)
- Generate `config.yaml`, `gateway.yaml`, and `.env` files

### 3. Verify

```bash
myagent doctor
```

Checks that all configs, API keys, and directories are in place.

### 4. Start

```bash
# Terminal 1: Start the Gateway
myagent gateway --port 18789

# Terminal 2: Start the Web UI
myagent web --port 8000

# Or use the TUI
myagent --tui
```

Open http://localhost:8000 in your browser.

---

## Configuration Files

All user configuration lives in `~/.myagent/`:

| File | Purpose |
|------|---------|
| `~/.myagent/config.yaml` | Agent settings (model, context, memory) |
| `~/.myagent/gateway.yaml` | Gateway platforms, sessions, reset policy |
| `~/.myagent/.env` | API keys and secrets |
| `~/.myagent/sessions/` | Session storage |
| `~/.myagent/logs/` | Log files |
| `~/.myagent/workspace/` | Agent workspace files |

### Environment Variables

You can override any config with environment variables:

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

MyAgent supports 19 LLM providers out of the box:

### International Providers

| Provider | Env Var | Default Model |
|----------|---------|---------------|
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4` |
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| Google Gemini | `GEMINI_API_KEY` | `gemini-2.5-pro` |
| xAI | `XAI_API_KEY` | `grok-3` |
| OpenRouter | `OPENROUTER_API_KEY` | `openai/gpt-4o` |
| HuggingFace | `HF_API_KEY` | `meta-llama/Llama-3.3-70B-Instruct` |
| NVIDIA | `NVIDIA_API_KEY` | `nvidia/llama-3.3-nemotron-super-49b-v1` |
| Arcee | `ARCEE_API_KEY` | `trinity-large-thinking` |
| Xiaomi | `XIAOMI_API_KEY` | `mimo-v2-pro` |
| Ollama (local) | None | `llama3.3` |

### China Domestic Providers (API Key NOT interchangeable with international versions)

| Provider | Env Var | Default Model |
|----------|---------|---------------|
| Zhipu (智谱) | `ZHIPU_API_KEY` / `ZHIPU_CN_API_KEY` | `glm-4` |
| Moonshot (Kimi) | `MOONSHOT_API_KEY` / `MOONSHOT_CN_API_KEY` | `moonshot-v1-8k` |
| MiniMax | `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` | `abab6.5s-chat` |
| Alibaba (DashScope) | `DASHSCOPE_API_KEY` / `DASHSCOPE_CN_API_KEY` | `qwen-max` |

### Ollama (Local Models)

1. Install Ollama: https://ollama.com
2. Pull a model: `ollama pull llama3.2`
3. Run `myagent init` and select Ollama
4. Default base URL: `http://localhost:11434`

---

## Gateway Platforms

MyAgent can receive and respond to messages from multiple platforms:

### Feishu / Lark (飞书)

1. Create a Feishu app at [open.feishu.cn/app](https://open.feishu.cn/app)
2. Get App ID and App Secret from the app credentials page
3. Enable bot capability and subscribe to message events
4. Run `myagent init` and enter your credentials

Required env vars:
```bash
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Slack

1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Add Bot Token Scopes: `chat:write`, `im:history`, `channels:history`
3. Install to workspace and copy Bot User OAuth Token
4. Run `myagent init` and enter your token

Required env vars:
```bash
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```

### Discord

1. Create a bot at [discord.com/developers/applications](https://discord.com/developers/applications)
2. Copy the bot token from the Bot section
3. Enable Message Content Intent
4. Run `myagent init` and enter your token

Required env vars:
```bash
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx.xxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Telegram

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot and copy the token
3. Run `myagent init` and enter your token

Required env vars:
```bash
TELEGRAM_BOT_TOKEN=xxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### DingTalk (钉钉)

1. Create an app at [open.dingtalk.com](https://open.dingtalk.com)
2. Get Client ID and Client Secret
3. Run `myagent init` and enter your credentials

Required env vars:
```bash
DINGTALK_CLIENT_ID=dingxxxxxxxxxxxxxxxx
DINGTALK_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Security

MyAgent connects to real messaging platforms. Treat inbound messages as **untrusted input**.

### Recommended Security Baseline

- **Pairing/allowlists**: Only respond to known users
- **DM isolation**: Use `session.dmScope: per-channel-peer` for shared inboxes
- **Sandbox tools**: Run with least-privilege permissions
- **Keep secrets safe**: Never commit `.env` files to version control
- **Use strong models**: For any bot with tool access, use the best available model

### Default DM Behavior

Unknown senders receive a pairing request. Approve with:

```bash
myagent pairing approve <platform> <user_id>
```

Or configure open DMs in `gateway.yaml` (not recommended for production).

---

## Docker Deployment

```bash
docker build -t myagent .
docker run -d \
  -p 8000:8000 \
  -p 18789:18789 \
  -v ~/.myagent:/app/.myagent \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  myagent
```

Or use docker-compose:

```bash
docker-compose up -d
```

---

## Updating

```bash
pip install -U myagent
myagent doctor
```

Keep `~/.myagent/` as "your stuff" — don't put personal configs into the repo.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `myagent init` fails | Check Python >= 3.11, `pip install -e ".[dev]"` |
| LLM not responding | Verify API key with `myagent doctor` |
| Gateway not receiving messages | Check platform webhook URL and credentials |
| Session not resetting | Check `gateway.yaml` reset_policy settings |
| High token usage | Adjust `context.auto_compact_threshold` in config |

---

## Next Steps

- Read the full [Configuration Reference](CONFIGURATION.md)
- Learn about [Custom Agents](AGENTS.md)
- Explore [Tool Development](TOOLS.md)
- Check [Docker Deployment](DOCKER.md)
