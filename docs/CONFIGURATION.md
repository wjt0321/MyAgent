# Configuration Reference

Complete reference for all MyAgent configuration options.

## Config Files

MyAgent uses three main configuration files in `~/.myagent/`:

1. **`config.yaml`** — Agent behavior, LLM, context, memory
2. **`gateway.yaml`** — Gateway platforms, sessions, authentication
3. **`.env`** — API keys and secrets (never commit this!)

---

## config.yaml

### model

```yaml
model:
  default: "anthropic/claude-sonnet-4"    # Default LLM model
  fallback: "openai/gpt-4o"               # Fallback model on failure
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default` | string | `anthropic/claude-sonnet-4` | Primary model identifier |
| `fallback` | string \| null | `null` | Fallback model if primary fails |

Model identifiers use the format `provider/model-name`:
- `anthropic/claude-sonnet-4`
- `anthropic/claude-opus-4`
- `openai/gpt-4o`
- `openai/gpt-4o-mini`
- `deepseek/deepseek-chat`
- `deepseek/deepseek-reasoner`
- `gemini/gemini-1.5-pro`
- `qwen/qwen-max`

### context

```yaml
context:
  auto_compact_threshold: 0.8    # Compact when context is 80% full
  max_turns: 50                  # Maximum conversation turns
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `auto_compact_threshold` | float | `0.8` | Trigger compaction at this ratio |
| `max_turns` | int | `50` | Hard limit on conversation length |

### memory

```yaml
memory:
  enabled: true
  scope: "project"    # "project", "session", or "global"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable persistent memory |
| `scope` | string | `"project"` | Memory scope level |

### logging

```yaml
logging:
  level: "info"           # "debug", "info", "warning", "error"
  trajectory: true        # Log conversation trajectories
  trajectory_path: "~/.myagent/trajectories/"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `level` | string | `"info"` | Log verbosity |
| `trajectory` | bool | `true` | Enable trajectory logging |
| `trajectory_path` | string | `"~/.myagent/trajectories/"` | Trajectory storage path |

### plugins

```yaml
plugins:
  enabled:
    - web_search
    - bash
    - file_edit
```

### mcp

```yaml
mcp:
  servers:
    filesystem:
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
```

---

## gateway.yaml

### platforms

Configure each messaging platform:

```yaml
platforms:
  feishu:
    enabled: true
    extra:
      app_id: "cli_xxxxxxxxxxxxxxxx"
      app_secret: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      domain: "feishu"              # "feishu" or "larksuite"
      connection_mode: "websocket"  # "websocket" or "webhook"
      auth_mode: "tenant"           # "tenant", "app", or "user"
      encrypt_key: ""               # Optional: message encryption
      verification_token: ""        # Optional: webhook verification

  slack:
    enabled: true
    token: "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
    reply_to_mode: "first"          # "off", "first", or "all"

  discord:
    enabled: true
    token: "xxxxxxxxxxxxxxxxxxxxxxxx.xxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxx"
    reply_to_mode: "first"

  telegram:
    enabled: true
    token: "xxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

  dingtalk:
    enabled: true
    extra:
      client_id: "dingxxxxxxxxxxxxxxxx"
      client_secret: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

  wecom:
    enabled: true
    extra:
      bot_id: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      secret: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

  weixin:
    enabled: true
    token: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    extra:
      account_id: "gh_xxxxxxxxxxxx"
      base_url: "https://api.weixin.qq.com"

  qq:
    enabled: true
    extra:
      app_id: "xxxxxxxxxx"
      client_secret: "xxxxxxxxxxxxxxxx"
      allow_from: "user1,user2"      # Comma-separated allowed users

  matrix:
    enabled: true
    token: "syt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    extra:
      homeserver: "https://matrix.org"

  webhook:
    enabled: true
    extra:
      port: 8080
      secret: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### default_reset_policy

Controls when conversation sessions reset:

```yaml
default_reset_policy:
  mode: "both"           # "daily", "idle", "both", or "none"
  at_hour: 4             # Hour for daily reset (0-23)
  idle_minutes: 1440     # Minutes of inactivity before reset
  notify: true           # Notify user on reset
```

| Mode | Behavior |
|------|----------|
| `daily` | Reset at `at_hour` every day |
| `idle` | Reset after `idle_minutes` of inactivity |
| `both` | Reset on either condition |
| `none` | Never auto-reset |

### reset_triggers

Commands that trigger manual session reset:

```yaml
reset_triggers:
  - /new
  - /reset
```

### streaming

Real-time token streaming configuration:

```yaml
streaming:
  enabled: true
  transport: "edit"        # "edit" or "off"
  edit_interval: 1.0       # Seconds between edits
  buffer_threshold: 40     # Characters to buffer before sending
  cursor: " ▉"             # Streaming cursor indicator
```

### Other Gateway Settings

```yaml
sessions_dir: "~/.myagent/sessions"    # Session storage path
always_log_local: true                  # Always log to local storage
stt_enabled: true                       # Speech-to-text enabled
group_sessions_per_user: true           # Separate sessions per user in groups
thread_sessions_per_user: false         # Separate sessions per user in threads
unauthorized_dm_behavior: "pair"        # "pair", "open", or "ignore"
session_store_max_age_days: 90          # Auto-delete sessions after N days
```

---

## Environment Variables

### LLM Providers

| Variable | Provider | Required |
|----------|----------|----------|
| `OPENAI_API_KEY` | OpenAI | Yes |
| `ANTHROPIC_API_KEY` | Anthropic | Yes |
| `DEEPSEEK_API_KEY` | DeepSeek | Yes |
| `GEMINI_API_KEY` | Google Gemini | Yes |
| `QWEN_API_KEY` | Alibaba Qwen | Yes |
| `SILICONFLOW_API_KEY` | SiliconFlow | Yes |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI | Yes |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI | Yes |
| `OPENROUTER_API_KEY` | OpenRouter | Yes |
| `OLLAMA_BASE_URL` | Ollama | No (default: `http://localhost:11434`) |

### Gateway Platforms

| Variable | Platform | Required |
|----------|----------|----------|
| `FEISHU_APP_ID` | Feishu/Lark | Yes |
| `FEISHU_APP_SECRET` | Feishu/Lark | Yes |
| `SLACK_BOT_TOKEN` | Slack | Yes |
| `DISCORD_BOT_TOKEN` | Discord | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram | Yes |
| `DINGTALK_CLIENT_ID` | DingTalk | Yes |
| `DINGTALK_CLIENT_SECRET` | DingTalk | Yes |
| `WECOM_BOT_ID` | WeCom | Yes |
| `WECOM_SECRET` | WeCom | Yes |
| `WEIXIN_TOKEN` | Weixin | Yes |
| `WEIXIN_ACCOUNT_ID` | Weixin | Yes |
| `QQ_APP_ID` | QQ | Yes |
| `QQ_CLIENT_SECRET` | QQ | Yes |
| `MATRIX_ACCESS_TOKEN` | Matrix | Yes |
| `MATRIX_HOMESERVER` | Matrix | No |

### MyAgent Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MYAGENT_HOME` | Config directory | `~/.myagent` |
| `MYAGENT_MODEL_DEFAULT` | Override default model | From config |
| `MYAGENT_CONTEXT_MAX_TURNS` | Override max turns | From config |
| `WEBHOOK_ENABLED` | Enable webhook platform | `false` |
| `WEBHOOK_PORT` | Webhook listen port | `8080` |
| `WEBHOOK_SECRET` | Webhook signature secret | Auto-generated |
| `SESSION_IDLE_MINUTES` | Override idle timeout | From config |
| `SESSION_RESET_HOUR` | Override reset hour | From config |

---

## Config Hot Reload

MyAgent supports hot-reloading of configuration files. Changes to `gateway.yaml` are picked up within 5 seconds without restarting.

To force a reload:

```bash
kill -HUP <myagent_pid>
```

Or use the systemd service:

```bash
sudo systemctl reload myagent
```

---

## Validation

Validate your configuration:

```bash
myagent doctor
```

This checks:
- All required directories exist
- Config files are valid YAML
- At least one LLM API key is set
- Gateway platform configs are valid
- No conflicting settings

---

## Examples

### Minimal Config (Local Only)

```yaml
# config.yaml
model:
  default: "ollama/llama3.2"

# .env
OLLAMA_BASE_URL=http://localhost:11434
```

### Full Production Config

```yaml
# config.yaml
model:
  default: "anthropic/claude-sonnet-4"
  fallback: "openai/gpt-4o"

context:
  auto_compact_threshold: 0.75
  max_turns: 100

memory:
  enabled: true
  scope: "project"

logging:
  level: "warning"
  trajectory: true
  trajectory_path: "/var/log/myagent/trajectories"

# gateway.yaml
platforms:
  feishu:
    enabled: true
    extra:
      app_id: "${FEISHU_APP_ID}"
      app_secret: "${FEISHU_APP_SECRET}"
      domain: "feishu"
      connection_mode: "websocket"
      auth_mode: "tenant"

  slack:
    enabled: true
    token: "${SLACK_BOT_TOKEN}"

default_reset_policy:
  mode: "both"
  at_hour: 4
  idle_minutes: 1440
  notify: true

sessions_dir: "/var/lib/myagent/sessions"
always_log_local: true
session_store_max_age_days: 30
```
