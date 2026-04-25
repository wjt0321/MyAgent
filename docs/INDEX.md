# MyAgent 文档索引

> 本文档为 MyAgent 项目所有技术文档的统一入口和导航索引。
> 最后更新: 2026-04-25

---

## 文档体系结构

```
docs/
├── INDEX.md                          # 本文档 — 总索引
├── architecture/                     # 架构文档 — 系统设计与技术决策
│   ├── 01-overview.md               # 系统架构总览
│   ├── 02-workspace.md              # Workspace 架构
│   ├── 03-memory.md                 # Memory 系统设计
│   ├── 04-task-engine.md            # Plan→Execute→Review 工作流
│   ├── 05-agent-teams.md            # Agent Teams 多协作
│   ├── 06-codebase.md               # 代码理解系统
│   ├── 07-gateway.md                # Gateway 网关架构
│   ├── 08-security-boundary.md      # 安全边界文档
│   └── 09-ui-state-and-event-contract.md  # UI 状态与事件契约
├── design/                           # 设计文档 — 交互设计与 UI 规范
│   ├── 01-tui-design.md             # TUI 终端界面设计
│   ├── 02-web-ui-design.md          # Web UI 设计规范
│   ├── 03-interaction-patterns.md   # 交互模式与命令规范
│   └── 05-tui-experience.md         # Phase 2 TUI 体验基线
├── reference/                        # 参考文档 — 配置、API、使用指南
│   ├── 01-getting-started.md        # 快速入门
│   ├── 02-configuration.md          # 配置参考
│   ├── 03-production.md             # 生产部署
│   ├── 04-concept-references.md     # 概念引用与出处
│   └── 05-web-api-contract.md       # Web API 接口契约
└── plans/                            # 规划文档 — 迭代计划与路线图
    ├── v0.11.0-redesign.md          # v0.11.0 架构整改方案
    ├── 2026-04-24-iteration-review.md  # 迭代审查与建议
    ├── 2026-04-24-production-optimization.md  # 生产优化建议
    └── 2026-04-24-web-ui-enhancement.md  # Web UI 增强方案
```

---

## 快速导航

### 按角色查找

| 角色 | 推荐阅读 |
|------|----------|
| **新用户** | [快速入门](reference/01-getting-started.md) → [交互模式](design/03-interaction-patterns.md) → [配置参考](reference/02-configuration.md) |
| **开发者** | [架构总览](architecture/01-overview.md) → [Workspace](architecture/02-workspace.md) → [Memory](architecture/03-memory.md) |
| **运维人员** | [生产部署](reference/03-production.md) → [配置参考](reference/02-configuration.md) |
| **架构师** | [架构总览](architecture/01-overview.md) → [Task Engine](architecture/04-task-engine.md) → [Agent Teams](architecture/05-agent-teams.md) |
| **前端开发** | [Web UI 设计](design/02-web-ui-design.md) → [交互模式](design/03-interaction-patterns.md) |
| **研究者** | [概念引用](reference/04-concept-references.md) → [v0.11.0 方案](plans/v0.11.0-redesign.md) |

### 按主题查找

| 主题 | 文档 |
|------|------|
| Workspace | [02-workspace.md](architecture/02-workspace.md) |
| Memory | [03-memory.md](architecture/03-memory.md) |
| Plan→Execute→Review | [04-task-engine.md](architecture/04-task-engine.md) |
| Agent Teams | [05-agent-teams.md](architecture/05-agent-teams.md) |
| 代码理解 | [06-codebase.md](architecture/06-codebase.md) |
| Gateway | [07-gateway.md](architecture/07-gateway.md) |
| 安全边界 | [08-security-boundary.md](architecture/08-security-boundary.md) |
| UI 事件契约 | [09-ui-state-and-event-contract.md](architecture/09-ui-state-and-event-contract.md) |
| TUI | [01-tui-design.md](design/01-tui-design.md) |
| TUI 体验基线 | [05-tui-experience.md](design/05-tui-experience.md) |
| Web UI | [02-web-ui-design.md](design/02-web-ui-design.md) |
| Web API 接口 | [05-web-api-contract.md](reference/05-web-api-contract.md) |
| 配置 | [02-configuration.md](reference/02-configuration.md) |
| 部署 | [03-production.md](reference/03-production.md) |
| 概念出处 | [04-concept-references.md](reference/04-concept-references.md) |

---

## 文档状态说明

| 状态标记 | 含义 |
|----------|------|
| ✅ | 已完成，与代码同步 |
| 🔄 | 部分完成，随迭代更新 |
| 📋 | 规划文档，待实现 |

### 各文档状态

| 文档 | 状态 | 说明 |
|------|------|------|
| architecture/01-overview.md | 🔄 | 架构总览，随新模块扩展 |
| architecture/02-workspace.md | ✅ | Workspace 系统已完成 |
| architecture/03-memory.md | ✅ | Memory 系统已完成 |
| architecture/04-task-engine.md | ✅ | Task Engine 已完成 |
| architecture/05-agent-teams.md | ✅ | Agent Teams 已完成 |
| architecture/06-codebase.md | ✅ | 代码理解系统已完成 |
| architecture/07-gateway.md | ✅ | Gateway 框架完成，Telegram/GitHub 适配器已就绪，Discord/Slack/Feishu 增强完成 |
| architecture/08-security-boundary.md | ✅ | 安全边界文档，Web UI/文件/GitHub Webhook 安全规则 |
| architecture/09-ui-state-and-event-contract.md | ✅ | Phase 0 UI 状态与事件契约基线 |
| design/01-tui-design.md | ✅ | TUI 结构与命令基线已同步到 Phase 2 |
| design/02-web-ui-design.md | ✅ | Web UI 已重构，JWT 认证、模型选择、主题切换、导出已添加 |
| design/03-interaction-patterns.md | ✅ | 交互模式已补齐 setup handoff、Command Palette、TUI 侧栏状态 |
| design/05-tui-experience.md | ✅ | Phase 2 TUI 体验基线文档 |
| reference/01-getting-started.md | ✅ | 快速入门指南 |
| reference/02-configuration.md | ✅ | 配置参考 |
| reference/03-production.md | ✅ | 生产部署指南，Helm Chart、Grafana Dashboard、Prometheus 告警已添加 |
| reference/04-concept-references.md | ✅ | 概念引用与出处 |
| reference/05-web-api-contract.md | ✅ | Web API 接口契约文档 |
| plans/v0.11.0-redesign.md | ✅ | v0.11.0 整改方案 |
| plans/2026-04-24-iteration-review.md | ✅ | 迭代审查与安全加固建议 |
| plans/2026-04-24-production-optimization.md | ✅ | 生产环境优化建议 |
| plans/2026-04-24-web-ui-enhancement.md | ✅ | Web UI 增强方案 |

---

## 历史文档归档

以下旧文档已整合到新体系中，原文件保留在 `design-doc/` 和 `docs/` 根目录作为备份：

| 旧文档 | 整合到新位置 | 说明 |
|--------|-------------|------|
| `design-doc/DESIGN.md` | [architecture/01-overview.md](architecture/01-overview.md) | 架构总览 |
| `design-doc/ROADMAP.md` | [architecture/01-overview.md#路线图](architecture/01-overview.md) | 路线图 |
| `design-doc/TUI-DESIGN.md` | [design/01-tui-design.md](design/01-tui-design.md) | TUI 设计 |
| `docs/design/05-tui-experience.md` | [design/05-tui-experience.md](design/05-tui-experience.md) | Phase 2 TUI 体验基线 |
| `design-doc/PLAN-next-iteration.md` | [plans/v0.11.0-redesign.md](plans/v0.11.0-redesign.md) | 迭代计划 |
| `design-doc/PLAN-tui-queryengine-integration.md` | [design/01-tui-design.md](design/01-tui-design.md) | TUI 集成计划 |
| `design-doc/PLAN-v0.5.0-next-iteration.md` | [plans/v0.11.0-redesign.md](plans/v0.11.0-redesign.md) | 早期迭代计划 |
| `docs/GETTING_STARTED.md` | [reference/01-getting-started.md](reference/01-getting-started.md) | 快速入门 |
| `docs/CONFIGURATION.md` | [reference/02-configuration.md](reference/02-configuration.md) | 配置参考 |
| `docs/PRODUCTION.md` | [reference/03-production.md](reference/03-production.md) | 生产部署 |
| `design-doc/reports/*` | [reference/04-concept-references.md](reference/04-concept-references.md) | 分析报告整合为概念引用 |

---

## 外部参考项目

MyAgent 在设计和实现过程中参考了以下开源项目，具体概念映射详见 [概念引用文档](reference/04-concept-references.md)：

| 项目 | 路径 | 主要借鉴概念 |
|------|------|-------------|
| **Claude Code** | `d:\源码库\claude-code-source-code` | Memory 系统、TUI 交互、工具插件化 |
| **Hermes Agent** | `d:\源码库\hermes-agent` | Gateway 网关模式、多平台适配器 |
| **OpenClaw** | `d:\源码库\openclaw` | 插件系统、身份分层、上下文管理 |
| **OpenHarness** | `d:\源码库\OpenHarness` | Workspace 结构、Agent 定义、Swarm 协作 |
