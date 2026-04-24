# Configuration Reference

> 本文档详细描述 MyAgent 的所有配置项。

---

## 1. 配置文件位置

```
~/.myagent/
├── config.yaml          # Agent 配置
├── gateway.yaml         # Gateway 配置
├── .env                 # 环境变量
├── soul.md              # Agent 灵魂
├── user.md              # 用户画像
└── identity.md          # Agent 身份
```

---

## 2. config.yaml

```yaml
agent:
  default: general        # 默认 Agent
  model: glm-4.7          # 默认模型

context:
  max_messages: 20        # 最大历史消息数
  auto_compact: true      # 自动压缩上下文
  auto_compact_threshold_tokens: 8000  # 压缩阈值

memory:
  enabled: true           # 启用记忆
  scope: global           # 记忆范围 (global|project|session)
  auto_save: true         # 自动保存

permissions:
  default_mode: ask       # 默认权限模式 (ask|auto)
  allowed_tools:          # 允许的工具
    - Read
    - Write
    - Edit
    - Bash
    - Glob
    - Grep
  denied_tools: []        # 拒绝的工具

cost:
  enabled: true           # 启用成本追踪
  display: true           # 显示成本
```

---

## 3. gateway.yaml

```yaml
platforms:
  feishu:
    enabled: false
    app_id: ""
    app_secret: ""
  slack:
    enabled: false
    bot_token: ""
  discord:
    enabled: false
    bot_token: ""
  telegram:
    enabled: false
    bot_token: ""

session:
  reset_mode: per_conversation  # 重置模式
  dm_scope: per_channel_peer    # DM 范围
  max_history: 100              # 最大历史

security:
  pairing_required: true        # 需要配对
  allowed_users: []             # 允许的用户列表
```

---

## 4. .env

```bash
# LLM Providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
GEMINI_API_KEY=
QWEN_API_KEY=
SILICONFLOW_API_KEY=
AZURE_OPENAI_API_KEY=
OPENROUTER_API_KEY=
ZHIPU_API_KEY=
MOONSHOT_API_KEY=
MINIMAX_API_KEY=
XAI_API_KEY=
DASHSCOPE_API_KEY=
HF_API_KEY=
NVIDIA_API_KEY=
ARCEE_API_KEY=
XIAOMI_API_KEY=

# Gateway
FEISHU_APP_ID=
FEISHU_APP_SECRET=
SLACK_BOT_TOKEN=
DISCORD_BOT_TOKEN=
TELEGRAM_BOT_TOKEN=
DINGTALK_CLIENT_ID=
DINGTALK_CLIENT_SECRET=

# MyAgent
MYAGENT_HOME=
MYAGENT_MODEL_DEFAULT=
```

---

## 5. Agent 定义

### 5.1 内置 Agent

| Agent | 用途 |
|-------|------|
| `general` | 通用对话 |
| `plan` | 任务规划 |
| `worker` | 代码实现 |
| `explore` | 代码探索 |
| `reviewer` | 代码审查 |

### 5.2 自定义 Agent

在 `~/.myagent/agents/` 创建 Markdown 文件:

```markdown
---
name: my-custom-agent
system_prompt: |
  You are a specialized agent for...
tools:
  - Read
  - Write
  - Bash
permission_mode: ask
memory_scope: global
---
```

---

## 6. Provider 环境变量

| Provider | API Key 环境变量 | 可选 Base URL 环境变量 | 默认模型 |
|----------|-----------------|----------------------|---------|
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_BASE_URL` | claude-sonnet-4 |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_BASE_URL` | gpt-4o |
| DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_BASE_URL` | deepseek-chat |
| Zhipu | `ZHIPU_API_KEY` | `ZHIPU_BASE_URL` | glm-4 |
| Moonshot | `MOONSHOT_API_KEY` | `MOONSHOT_BASE_URL` | moonshot-v1-8k |
| MiniMax | `MINIMAX_API_KEY` | `MINIMAX_BASE_URL` | abab6.5s-chat |
| OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_BASE_URL` | openai/gpt-4o |
| xAI | `XAI_API_KEY` | `XAI_BASE_URL` | grok-3 |
| Gemini | `GEMINI_API_KEY` | `GEMINI_BASE_URL` | gemini-2.5-pro |
| Alibaba | `DASHSCOPE_API_KEY` | `DASHSCOPE_BASE_URL` | qwen-max |
| HuggingFace | `HF_API_KEY` | `HF_BASE_URL` | meta-llama/Llama-3.3-70B-Instruct |
| NVIDIA | `NVIDIA_API_KEY` | `NVIDIA_BASE_URL` | nvidia/llama-3.3-nemotron-super-49b-v1 |
| Arcee | `ARCEE_API_KEY` | `ARCEE_BASE_URL` | trinity-large-thinking |
| Xiaomi | `XIAOMI_API_KEY` | `XIAOMI_BASE_URL` | mimo-v2-pro |
| Ollama | 无需 Key | `OLLAMA_BASE_URL` | llama3.3 |

### 模型自动检测

MyAgent 支持 `provider/model` 语法自动路由到对应 Provider：

```bash
# 自动使用 Anthropic Provider
MYAGENT_MODEL_DEFAULT=anthropic/claude-sonnet-4

# 自动使用 OpenRouter Provider
MYAGENT_MODEL_DEFAULT=openrouter/anthropic/claude-sonnet-4

# 自动使用 DeepSeek Provider
MYAGENT_MODEL_DEFAULT=deepseek-chat
```

## 7. 环境变量覆盖

所有配置项都可以通过环境变量覆盖:

```bash
MYAGENT_AGENT_DEFAULT=worker
MYAGENT_CONTEXT_MAX_MESSAGES=50
MYAGENT_MEMORY_ENABLED=false
```
