<p align="center">
  <img src="images/logo.svg" alt="MyAgent" width="400">
</p>

<p align="center">
  <strong>支持多渠道网关的自主 AI 智能体</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <a href="README.md">English</a>
</p>

**MyAgent** 是一个自主 AI 智能体平台，可连接到你日常使用的各种消息渠道。它具备强大的多渠道消息网关、面向终端爱好者的 TUI 界面，以及基于浏览器的 Web UI 交互界面。

支持平台：**飞书/Lark、Slack、Discord、Telegram、钉钉、企业微信、微信、QQ、Matrix、Webhook**。

## 功能特性

- **多渠道网关** — 统一管理所有消息平台的收件箱
- **TUI 界面** — 带有 ASCII 艺术 Logo 的富终端界面
- **Web UI** — 基于 WebSocket 的实时聊天，支持设置与重置
- **多 LLM 支持** — OpenAI、Anthropic、DeepSeek、Gemini、通义千问、Ollama、Azure、OpenRouter
- **上下文压缩** — 自动压缩对话历史
- **会话管理** — 支持按用户、按群组、按话题的会话隔离
- **工具调用** — Bash、文件编辑、网页搜索、图像分析
- **生产就绪** — Docker、健康检查、指标监控、结构化日志

## 界面截图

### Web UI

![MyAgent Web UI](images/myagent-web-ui-2026-04-23T07-29-36-702Z.png)

### Web UI - 代码库搜索

![代码库搜索](images/webui-codebase-search-2026-04-23T06-32-00-502Z.png)

### Web UI - 记忆管理

![记忆标签页](images/webui-memory-tab-2026-04-23T04-10-30-994Z.png)

## 快速开始

```bash
# 安装
pip install myagent

# 初始化（交互式向导）
myagent init

# 验证配置
myagent doctor

# 启动服务
myagent gateway --port 18789    # 网关服务
myagent web --port 8000          # Web UI

# 或使用 TUI
myagent --tui
```

在浏览器中打开 http://localhost:8000。

## 文档

- **[入门指南](docs/GETTING_STARTED.md)** — 首次安装配置指引
- **[生产部署](docs/PRODUCTION.md)** — Docker、systemd、SSL、监控
- **[配置参考](docs/CONFIGURATION.md)** — 完整配置选项说明

## CLI 命令

```bash
myagent init              # 交互式配置向导
myagent doctor            # 诊断配置问题
myagent web               # 启动 Web UI 服务
myagent gateway           # 启动网关服务
myagent --tui             # 启动 TUI 界面
myagent --version         # 显示版本
```

## 配置

所有用户配置存储在 `~/.myagent/` 目录下：

```
~/.myagent/
├── config.yaml          # 智能体设置（模型、上下文、记忆）
├── gateway.yaml         # 网关平台、会话配置
├── .env                 # API 密钥和机密信息
├── sessions/            # 会话存储
├── logs/                # 日志文件
└── workspace/           # 智能体工作空间
```

### 环境变量

```bash
# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...

# 网关
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

或使用 `docker-compose up -d`。

## 开发

```bash
git clone https://github.com/wjt0321/MyAgent.git
cd myagent
pip install -e ".[dev]"
pytest
```

## 架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   飞书      │     │   Slack     │     │   Discord   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │   网关      │
                    │ (WebSocket) │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐
       │    TUI      │ │ Web UI │ │  引擎    │
       │  (终端)     │ │(浏览器)│ │ (LLM)   │
       └─────────────┘ └────────┘ └──────────┘
```

## 安全

MyAgent 连接到真实的消息平台。请将入站消息视为**不可信输入**。

- **默认行为**：未知发送者会收到配对请求
- **推荐做法**：使用白名单并启用沙箱工具
- **切勿提交**：`.env` 文件或 API 密钥到版本控制

## 许可证

MIT 许可证 — 详见 [LICENSE](LICENSE)。

## 致谢

灵感来源于 [Hermes Agent](https://github.com/NousResearch/hermes-agent)、[OpenClaw](https://github.com/openclaw/openclaw)、[Claude Code](https://github.com/anthropics/claude-code) 和 [OpenHarness](https://github.com/HKUDS/OpenHarness)。
