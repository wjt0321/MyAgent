# MyAgent 后续迭代方向

> 基于当前 v0.11.0+ 状态，梳理可继续迭代的模块与方向。
> 最后更新: 2026-04-23

---

## 当前完成度概览

| Phase | 模块 | 完成度 | 说明 |
|-------|------|--------|------|
| Phase 1 | 核心引擎 | 95% | QueryEngine、工具、Agent 定义、CLI 就绪 |
| Phase 2 | 扩展能力 | 90% | 插件、MCP、Web 工具、子 Agent、Todo 就绪 |
| Phase 3 | 生产级基础 | 60% | Swarm、轨迹、成本、安全就绪；Gateway 只有骨架 |
| Phase 4 | 高级特性 | 80% | LSP、TTS、图像、远程桥接、定时任务就绪 |
| Phase 5 | TUI | 95% | 核心框架、对话、工具可视化、权限、配置完成 |
| Phase 6 | Web UI | 70% | 基础界面可用，可继续增强 |
| Phase 7 | Gateway | 80% | Telegram/GitHub 适配器完成，会话持久化，JWT 认证 |
| Phase 8 | 生产优化 | 80% | Prometheus 指标、LLM 重试、配置热重载、JSON 日志已添加 |
| Phase 9 | 生态扩展 | 90% | 19 个 LLM 提供商（含国内/国际版）、7 个核心工具 |

---

## 迭代方向一：Web UI 增强

**优先级**: ⭐⭐⭐ 推荐

当前 Web UI 已具备基础聊天功能，可继续完善以下方面：

### 1.1 会话管理
- 左侧会话列表（类似 ChatGPT）
- 新建/重命名/删除会话
- 会话历史持久化到 `~/.myagent/sessions/`

### 1.2 代码高亮
- 集成 Monaco Editor 或 Prism.js
- 工具结果中的代码块语法高亮
- 支持代码折叠

### 1.3 文件浏览器
- 左侧显示项目文件树
- 点击文件可预览内容
- 与 Codebase 搜索联动

### 1.4 设置面板
- 模型切换下拉框
- API Key 配置（本地存储）
- 主题切换（亮色/暗色）

### 1.5 工具结果可视化
- Bash 命令执行结果折叠/展开
- 文件编辑 diff 视图
- 图片分析结果展示

---

## 迭代方向二：Gateway 多平台接入

**优先级**: ⭐⭐⭐

Gateway 核心框架已完成，Telegram 和 GitHub 适配器已就绪：

### 2.1 已完成的适配器
- **Telegram** — 长轮询接收消息，内联键盘权限审批，消息去重
- **GitHub** — Webhook 事件处理，PR/Issue 自动分析评论，签名验证

### 2.2 待完成的适配器
- **Discord** — discord.py 集成，斜杠命令注册，线程对话支持
- **Slack** — slack-sdk 集成，Block Kit 消息格式，提及触发（@myagent）

### 2.3 会话管理优化
- ✅ 用户-会话绑定持久化（`~/.myagent/gateway_sessions.yaml`）
- ✅ 服务重启后会话恢复
- LRU 缓存，最大 128 会话（待实现）
- 1 小时 TTL 自动驱逐（待实现）

---

## 迭代方向三：生产级优化

**优先级**: ⭐⭐⭐

### 3.1 日志和监控
- 结构化日志（JSON 格式）
- 关键指标：请求延迟、工具成功率、Token 消耗
- Prometheus /metrics 端点

### 3.2 配置热重载
- 监听配置文件变化
- 无需重启即可更新模型、系统提示

### 3.3 错误恢复
- LLM 调用重试（指数退避）
- 工具失败优雅降级
- ✅ 会话状态自动保存（Web UI + Gateway）

### 3.4 部署优化
- ✅ Docker Compose 多服务编排
- ✅ 环境变量配置
- ✅ 健康检查端点
- GitHub Webhook 路由配置文档

---

## 迭代方向四：Web UI 增强

**优先级**: ⭐⭐

### 4.1 已完成的增强
- ✅ 代码块复制按钮
- ✅ 消息时间戳
- ✅ 工具面板可折叠
- ✅ 欢迎页快捷操作卡片
- ✅ JWT 认证系统（登录/密码设置）
- ✅ 多用户会话隔离
- ✅ Esc 快捷键关闭设置面板
- ✅ 会话侧边栏增强（重命名、导出、显示模型）
- ✅ 模型选择器（header 下拉框，实时切换）
- ✅ 主题切换（暗色/亮色/跟随系统）
- ✅ 会话导出（Markdown / JSON）
- ✅ 移动端响应式适配

### 4.2 待完成的增强
- 消息编辑和重新发送
- 系统提示编辑
- 会话导入功能

---

## 迭代方向五：Agent 能力增强

**优先级**: ⭐⭐

### 5.1 工具扩展
- ✅ Git 操作工具（status、diff、log、add、commit、push、branch、checkout）
- ✅ SSRF 保护（WebFetch）
- 更多工具类型（数据库、浏览器）
- 工具组合（链式调用）
- 工具权限分级

### 5.2 记忆系统
- 自动记忆提取（对话中识别关键信息）
- 记忆检索增强（RAG）
- 跨会话记忆共享

### 5.3 多模态支持
- 图片理解（已有基础）
- 语音输入/输出
- 文档解析（PDF、Word）

### 5.4 代码能力
- 代码解释器（Python 沙箱）
- 代码重构建议
- 测试用例生成

---

## 迭代方向六：更多 LLM 提供商

**优先级**: ✅ 已完成 (v0.12.0)

当前支持 15 个 Provider：Anthropic、OpenAI、DeepSeek、Zhipu、Moonshot、MiniMax、OpenRouter、xAI、Gemini、Alibaba、HuggingFace、NVIDIA、Arcee、Xiaomi、Ollama

### 6.1 已完成的 Provider
- ✅ **xAI** — Grok 系列模型
- ✅ **Gemini** — Google AI Studio (Gemini 2.5/2.0/1.5)
- ✅ **Alibaba** — 阿里云 DashScope (Qwen 系列)
- ✅ **HuggingFace** — HF Inference API
- ✅ **NVIDIA** — NVIDIA NIM
- ✅ **Arcee** — Trinity 系列
- ✅ **Xiaomi** — MiMo V2 系列
- ✅ **Ollama** — 本地模型 (自动检测 localhost:11434)

### 6.2 模型自动检测
- 支持 `provider/model` 语法 (如 `anthropic/claude-sonnet-4`)
- 支持 bare model name 启发式匹配 (如 `deepseek-chat` → DeepSeek)
- Web UI 模型选择器按 Provider 分组 (15 个分组，50+ 模型)

### 6.3 待添加的 Provider
- 百度文心一言
- 讯飞星火
- 字节豆包
- 腾讯混元
- Together AI
- Replicate
- Groq（高速推理）

---

## 迭代方向七：TUI 体验优化

**优先级**: ⭐⭐

### 7.1 多行输入
- Shift+Enter 换行
- 当前 Input 组件替换为 TextArea

### 7.2 Agent 切换真正生效
- 切换时更新 QueryEngine system prompt
- 根据 Agent 定义过滤可用工具
- 调整权限模式（explore = dontAsk）

### 7.3 快捷键增强
- `Ctrl+R` 重新生成
- `Ctrl+Shift+C` 复制最后回复
- `/` 快速唤起命令

### 7.4 主题系统
- 暗色/亮色/高对比度主题
- 自定义配色

---

## 推荐优先级

1. ✅ **Phase 1**（Web UI 修复）— 已完成
2. ✅ **Phase 2**（OpenClaw Core）— 已完成
3. ✅ **Phase 3**（Gateway 完善）— 已完成
4. **Phase 4**（上下文压缩深化）— 提升长对话体验
5. **Phase 5**（生产优化）— 部署稳定性

---

## 总结

MyAgent 已经具备了**生产可用的核心功能**:
- ✅ 多 LLM 支持（19 个提供商，含国内/国际版分离）
- ✅ 核心工具集（9 个工具，含 Git）
- ✅ TUI 和 Web UI 双界面
- ✅ Gateway 多平台（Telegram + GitHub Webhook）
- ✅ 会话持久化（Web UI + Gateway）
- ✅ JWT 认证与多用户隔离
- ✅ 基础安全（权限检查、SSRF 防护、沙箱）
- ✅ 模型自动检测（provider/model 语法 + 启发式匹配）

**下一步重点**：
1. 上下文压缩自动触发与 Token 监控
2. Discord / Slack 适配器完善
3. 百度文心一言 / 讯飞星火 / 字节豆包 等国内 Provider
4. Web UI 消息编辑、系统提示编辑

预计 **1 个迭代周期** 可完成全部优化，达到完全生产可用状态。
