<p align="center">
  <img src="images/logo.svg" alt="MyAgent" width="400">
</p>

<p align="center">
  <strong>支持多渠道网关的自主 AI 智能体</strong></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=socketdotio&logoColor=white" alt="WebSocket">
</p>

<p align="center">
  <a href="README.md">English</a>
</p>

**MyAgent** 是一个自主 AI 智能体平台，可连接到你日常使用的各种消息渠道。它具备强大的多渠道消息网关、面向终端爱好者的 TUI 界面，以及基于浏览器的 Web UI 交互界面。

支持平台：**飞书/Lark、Slack、Discord、Telegram、钉钉、企业微信、微信、QQ、Matrix、Webhook**。

## 功能特性

- **多渠道网关底座** — 提供 Telegram、Discord、Slack、飞书等平台适配器、会话隔离和权限审批钩子
- **TUI 工作台** — 具备 setup 感知、状态侧栏、Command Palette、Slash Commands 与浮层审批的终端主界面
- **Web UI** — 工作台式浏览器界面，提供分组导航、命令面板、工具详情侧栏、任务/团队快照、审查结果卡片与基于 WebSocket 的实时聊天
- **多 LLM 支持** — 40+ Provider（含国内/国际版）：Anthropic（Claude 4.6/4.5）、OpenAI（GPT-5.5/5/4.5）、DeepSeek（V4 Pro/V4 Flash/V3/R1）、Gemini（3.1 Pro/3 Flash/2.5 Pro）、xAI（Grok 4/3）、Qwen 3.6、Ollama、OpenRouter、智谱/智谱-CN、Moonshot/Moonshot-CN、MiniMax/MiniMax-CN、阿里云/阿里云-CN、HuggingFace、NVIDIA、Arcee、Xiaomi、百度文心一言、讯飞星火、字节豆包、腾讯混元、Cohere、SiliconFlow
- **上下文压缩** — 自动压缩对话历史，支持 AutoCompactor
- **会话管理** — 支持按用户、按群组、按话题的会话隔离，支持持久化绑定
- **工具调用** — Bash、代码解释器（Python 沙箱）、文件编辑、网页搜索、图像分析、Git 操作
- **权限系统** — Telegram 内联键盘审批与 Web UI 权限请求，支持 tool_use_id 追踪
- **GitHub 集成** — Webhook 驱动的 PR/Issue 分析与自动评论，服务端密钥验证
- **部署工具链** — Docker 镜像、compose 编排、健康检查、Prometheus 指标、结构化 JSON 日志和 Helm Chart
- **安全增强** — Web UI JWT 认证、文件访问路径限制、WebSocket 会话隔离、Webhook 签名验证

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

# 首次快速初始化
myagent init --quick

# 检查缺失项与下一步动作
myagent doctor

# 推荐本地入口：TUI
myagent --tui

# 或启动 Web UI
myagent web --port 8000
```

在浏览器中打开 http://localhost:8000。

说明：
- `myagent init` 仍然是完整的交互式向导。
- `myagent init --quick` 会生成基础目录、配置模板和 `.env` 脚手架。
- 当配置未完成时，TUI 与 Web 都会进入 `Setup Required` 状态，并提示下一步命令。

### Web 工作台亮点

- 使用左侧工作台导航在 `Chat`、`Tasks`、`Files`、`Workspace`、`Team` 之间切换
- 按 `Ctrl+K` 打开命令面板，快速跳转到常用操作
- 支持 `/plan`、`/agent`、`/model`、`/session`、`/setup`、`/doctor` 等 Slash Commands
- 点击工具卡片、任务、会话或文件后，可在右侧详情侧栏查看上下文
- 任务批准后会进入可见的 `Task -> Team -> Review` 流程，并持续刷新当前任务与审查摘要
- 失败或取消后的任务可通过重试动作重置，再次批准后重新执行
- 任务视图会同步显示轻量 Team 摘要，便于快速判断当前执行负载与完成数

## 文档

- **[入门指南](docs/GETTING_STARTED.md)** — 首次安装配置指引
- **[生产部署](docs/PRODUCTION.md)** — Docker、systemd、SSL、监控
- **[配置参考](docs/CONFIGURATION.md)** — 完整配置选项说明

## CLI 命令

```bash
myagent init              # 交互式配置向导
myagent init --quick      # 生成最小可用的本地配置
myagent doctor            # 诊断 setup 状态并给出下一步建议
myagent web               # 启动 Web UI 服务
myagent --tui             # 启动 TUI 工作台
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
# LLM (国际版)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
ZHIPU_API_KEY=...
MOONSHOT_API_KEY=...
MINIMAX_API_KEY=...
XAI_API_KEY=...
GEMINI_API_KEY=...
DASHSCOPE_API_KEY=...
HF_API_KEY=...
NVIDIA_API_KEY=...
ARCEE_API_KEY=...
XIAOMI_API_KEY=...

# LLM (国内版 - API Key 不互通)
ZHIPU_CN_API_KEY=...
MOONSHOT_CN_API_KEY=...
MINIMAX_CN_API_KEY=...
DASHSCOPE_CN_API_KEY=...

# 网关
FEISHU_APP_ID=cli_...
FEISHU_APP_SECRET=...
SLACK_BOT_TOKEN=xoxb-...
TELEGRAM_BOT_TOKEN=...
DISCORD_BOT_TOKEN=...

# GitHub 集成
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
  -v myagent-data:/app/data \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  myagent
```

说明：
- 默认镜像入口只启动 Web UI。
- TUI 适合本地终端直接运行，不建议作为容器默认进程。
- 如需多服务编排，请使用 `docker compose up -d web` 或 `docker compose --profile bot up -d`。

### Kubernetes (Helm)

```bash
helm install myagent ./deploy/helm/myagent \
  --set myagent.apiKeys.anthropic="your-api-key" \
  --set myagent.provider="anthropic"
```

详见 [deploy/helm/myagent/README.md](deploy/helm/myagent/README.md) 获取完整 Helm 配置。

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
