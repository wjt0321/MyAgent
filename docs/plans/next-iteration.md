# MyAgent 后续迭代方向

> 基于当前 v0.14.0 状态，梳理可继续迭代的模块与方向。
> 最后更新: 2026-04-24
> v0.14.0 变更：初始化界面中文化、模型列表更新至2026年最新、Web UI 交互修复

---

## 当前完成度概览

| Phase | 模块 | 完成度 | 说明 |
|-------|------|--------|------|
| Phase 1 | 核心引擎 | 95% | QueryEngine、工具、Agent 定义、CLI 就绪 |
| Phase 2 | 扩展能力 | 95% | 插件、MCP、Web 工具、子 Agent、Todo、CodeInterpreter 就绪 |
| Phase 3 | 生产级基础 | 95% | Swarm、轨迹、成本、安全就绪；Gateway 适配器完整 |
| Phase 4 | 高级特性 | 85% | LSP、TTS、图像、远程桥接、定时任务就绪；记忆自动提取完成 |
| Phase 5 | TUI | 98% | 核心框架、对话、工具可视化、权限、配置完成；Ctrl+R 重生成、Token 统计已添加 |
| Phase 6 | Web UI | 95% | 消息编辑、系统提示编辑、会话导入/导出、Token 展示、主题切换、移动端适配已完成 |
| Phase 7 | Gateway | 95% | Telegram/GitHub 适配器完成，Discord 斜杠命令/线程、Slack Block Kit、Feishu WebSocket 已增强 |
| Phase 8 | 生产优化 | 98% | Prometheus 指标、LLM 重试、配置热重载、JSON 日志、Grafana Dashboard、Helm Chart、Prometheus 告警已添加 |
| Phase 9 | 生态扩展 | 100% | 35+ LLM Provider（含国内/国际版），2026年最新模型更新 |

---

## 迭代方向一：Web UI 增强

**优先级**: ✅ 已完成 (v0.13.0)

当前 Web UI 已具备完整聊天功能和用户体验优化：

### 1.1 会话管理
- ✅ 左侧会话列表（类似 ChatGPT）
- ✅ 新建/重命名/删除会话
- ✅ 会话历史持久化到 `~/.myagent/sessions/`

### 1.2 代码高亮
- ✅ 集成 highlight.js
- ✅ 工具结果中的代码块语法高亮
- ✅ 代码块复制按钮

### 1.3 设置面板
- ✅ 模型切换下拉框（按 Provider 分组，35+ 个分组）
- ✅ API Key 配置（本地存储）
- ✅ 主题切换（亮色/暗色/跟随系统）

### 1.4 工具结果可视化
- ✅ Bash 命令执行结果折叠/展开
- ✅ 代码解释器输出展示
- ✅ 文件编辑 diff 视图
- ✅ 图片分析结果展示

### 1.5 已完成的增强
- ✅ 消息编辑和重新发送
- ✅ 系统提示编辑
- ✅ 会话导入/导出（Markdown / JSON）
- ✅ Token 消耗实时展示
- ✅ 消息时间戳
- ✅ 欢迎页快捷操作卡片
- ✅ JWT 认证系统（登录/密码设置）
- ✅ 多用户会话隔离
- ✅ Esc 快捷键关闭设置面板
- ✅ 移动端响应式适配

---

## 迭代方向二：Gateway 多平台接入

**优先级**: ✅ 已完成 (v0.13.0)

### 2.1 已完成的适配器
- **Telegram** — 长轮询接收消息，内联键盘权限审批，消息去重
- **GitHub** — Webhook 事件处理，PR/Issue 自动分析评论，签名验证
- **Discord** — Gateway WebSocket，斜杠命令（`/ask`、`/reset`、`/agent`），消息编辑，线程创建
- **Slack** — Socket Mode，Block Kit 消息格式，权限请求面板
- **Feishu** — Webhook + WebSocket 双模式，签名验证

### 2.2 会话管理优化
- ✅ 用户-会话绑定持久化（`~/.myagent/gateway_sessions.yaml`）
- ✅ 服务重启后会话恢复
- ✅ JWT 认证与多用户隔离
- ✅ LRU 缓存，最大 128 会话
- ✅ 1 小时 TTL 自动驱逐

---

## 迭代方向三：生产级优化

**优先级**: ✅ 已完成 (v0.13.0)

### 3.1 日志和监控
- ✅ 结构化日志（JSON 格式）
- ✅ 关键指标：请求延迟、工具成功率、Token 消耗
- ✅ Prometheus /metrics 端点
- ✅ Grafana Dashboard 模板（10 个面板）
- ✅ Prometheus Alert Rules（8 条告警）

### 3.2 配置热重载
- ✅ 监听配置文件变化
- ✅ 无需重启即可更新模型、系统提示

### 3.3 错误恢复
- ✅ LLM 调用重试（指数退避）
- ✅ 工具失败优雅降级
- ✅ 会话状态自动保存（Web UI + Gateway）

### 3.4 部署优化
- ✅ Docker Compose 多服务编排
- ✅ 环境变量配置
- ✅ 健康检查端点
- ✅ Kubernetes Helm Chart（完整 Chart，含 Deployment、Service、Secrets、PVC、HPA、Ingress、ServiceMonitor、PrometheusRule）

---

## 迭代方向四：Agent 能力增强

**优先级**: ⭐⭐⭐

### 4.1 工具扩展
- ✅ Git 操作工具（status、diff、log、add、commit、push、branch、checkout）
- ✅ 代码解释器（CodeInterpreter）— 安全 Python 沙箱，支持 math/numpy/pandas/matplotlib
- ✅ SSRF 保护（WebFetch）
- 更多工具类型（数据库查询、浏览器自动化）
- 工具组合（链式调用）
- 工具权限分级

### 4.2 记忆系统
- ✅ 自动记忆提取（对话中识别关键信息：名字、邮箱、公司、偏好等）
- ✅ 记忆 RAG 检索增强（基于关键词匹配的相关记忆检索）
- 跨会话记忆共享
- LLM-based 记忆提取（替代启发式规则）

### 4.3 多模态支持
- 图片理解（已有基础）
- 语音输入/输出
- 文档解析（PDF、Word）

### 4.4 代码能力
- ✅ 代码解释器（Python 沙箱）
- 代码重构建议
- 测试用例生成

---

## 迭代方向五：更多 LLM 提供商

**优先级**: ✅ 已完成 (v0.13.0 → v0.14.0)

当前支持 35+ 个 Provider：Anthropic (Claude 4.6/4.5)、OpenAI (GPT-5.5/5/4.5)、DeepSeek (V4 Pro/V4 Flash/V3/R1)、Gemini (3.1 Pro/3 Flash/2.5 Pro)、xAI (Grok 4/3)、Qwen 3.6、Zhipu/Zhipu-CN、Moonshot/Moonshot-CN、MiniMax/MiniMax-CN、OpenRouter、Alibaba/Alibaba-CN、HuggingFace、NVIDIA、Arcee、Xiaomi、Ollama、Baidu ERNIE、iFlytek Spark、ByteDance Doubao、Tencent Hunyuan

### 5.1 待添加的 Provider
- Together AI
- Replicate
- Groq（高速推理）
- Perplexity
- Cohere

### 5.2 模型自动检测
- ✅ 支持 `provider/model` 语法 (如 `anthropic/claude-sonnet-4-6`)
- ✅ 支持 bare model name 启发式匹配 (如 `deepseek-chat` → DeepSeek)
- ✅ Web UI 模型选择器按 Provider 分组 (35+ 个分组，80+ 模型)

---

## 迭代方向六：TUI 体验优化

**优先级**: ✅ 已完成 (v0.13.0)

### 6.1 多行输入
- ✅ Shift+Enter 换行
- ✅ TextArea 组件支持多行

### 6.2 Agent 切换真正生效
- ✅ 切换时更新 QueryEngine system prompt
- ✅ 根据 Agent 定义过滤可用工具
- ✅ 调整权限模式（explore = dontAsk）

### 6.3 快捷键增强
- ✅ `Ctrl+R` 重新生成
- ✅ `Ctrl+Shift+C` 复制最后回复
- ✅ `/` 快速唤起命令

### 6.4 Token 统计
- ✅ `/tokens` 命令查看 Token 使用量、峰值、压缩次数、动态阈值

---

## 迭代方向七：上下文压缩深化

**优先级**: ✅ 已完成 (v0.13.0)

- ✅ 动态阈值调整（基于 Token 增长速率）
- ✅ 关键决策点保留（系统提示、错误工具结果、用户命令）
- ✅ Token 使用量统计（total、peak、avg、compression count）
- ✅ Prometheus 指标集成（`query_context_tokens` Gauge、`query_compactions_total` Counter）

---

## 推荐优先级

1. ✅ **Phase 1**（Web UI 修复）— 已完成
2. ✅ **Phase 2**（OpenClaw Core）— 已完成
3. ✅ **Phase 3**（Gateway 完善）— 已完成
4. ✅ **Phase 4**（Web UI 增强）— 已完成
5. ✅ **Phase 5**（LLM Provider 扩展）— 已完成（35+ 个 Provider，2026年最新模型）
6. ✅ **Phase 6**（上下文压缩深化）— 已完成
7. ✅ **Phase 7**（TUI 体验优化）— 已完成
8. ✅ **Phase 8**（生产级监控）— 已完成
9. ✅ **Phase 9**（记忆系统自动提取）— 已完成
10. ✅ **Phase 10**（代码解释器）— 已完成
11. **Phase 11**（多模态支持）— 语音、文档解析
12. **Phase 12**（更多国际 Provider）— Together AI、Replicate、Groq、Perplexity、Cohere
13. **Phase 13**（LLM-based 记忆提取）— 替代启发式规则

---

## 总结

MyAgent 已经具备了**完全生产可用的功能**:
- ✅ 多 LLM 支持（35+ 个提供商，含国内/国际版分离，2026年最新模型）
- ✅ 核心工具集（10 个工具，含 Git、CodeInterpreter）
- ✅ TUI 和 Web UI 双界面
- ✅ Gateway 多平台（Telegram、Discord、Slack、Feishu、GitHub Webhook）
- ✅ 会话持久化（Web UI + Gateway）
- ✅ JWT 认证与多用户隔离
- ✅ 基础安全（权限检查、SSRF 防护、沙箱）
- ✅ 模型自动检测（provider/model 语法 + 启发式匹配）
- ✅ 主题切换与移动端适配
- ✅ 会话导入/导出
- ✅ 动态上下文压缩与 Token 监控
- ✅ TUI Ctrl+R 重生成与 Token 统计
- ✅ Grafana Dashboard + Helm Chart + Prometheus 告警
- ✅ 记忆系统自动提取与 RAG 检索
- ✅ 代码解释器沙箱（安全 Python 执行）

**下一步重点**：
1. 多模态支持（语音输入/输出、PDF/Word 文档解析）
2. 更多国际 Provider（Together AI、Replicate、Groq、Perplexity、Cohere）
3. LLM-based 记忆提取（替代启发式规则，提升准确率）

预计 **1-2 个迭代周期** 可完成全部优化，达到 v0.14.0 发布标准。
