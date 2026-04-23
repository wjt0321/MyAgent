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
| Phase 7 | Gateway | 20% | 抽象基类和 Manager 就绪，适配器待完善 |
| Phase 8 | 生产优化 | 10% | 基础 CostTracker 就绪，日志/监控待完善 |
| Phase 9 | 生态扩展 | 30% | 7 个 LLM 提供商、6 个核心工具 |

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

Gateway 骨架已就绪，需完善具体平台适配器：

### 2.1 Discord 适配器
- discord.py 集成
- 斜杠命令注册（/ask /reset /status）
- 线程对话支持

### 2.2 Slack 适配器
- slack-sdk 集成
- Block Kit 消息格式
- 提及触发（@myagent）

### 2.3 Telegram 适配器
- python-telegram-bot 集成
- 命令菜单（/start /help /reset）
- 内联查询支持

### 2.4 会话池优化
- LRU 缓存，最大 128 会话
- 1 小时 TTL 自动驱逐
- 每个会话独立 QueryEngine

---

## 迭代方向三：工具扩展

**优先级**: ⭐⭐

当前工具集：Read、Write、Edit、Bash、Glob、Grep、WebSearch、WebFetch

### 3.1 Git 操作工具
- `git_diff` — 查看变更
- `git_log` — 查看提交历史
- `git_blame` — 查看代码归属

### 3.2 数据库查询工具
- `sql_query` — 执行 SQL 并返回结果
- `db_schema` — 查看表结构

### 3.3 浏览器自动化
- `browser_open` — 打开网页
- `browser_screenshot` — 页面截图
- `browser_click` — 模拟点击

### 3.4 文件分析工具
- `csv_read` — 读取并分析 CSV
- `json_query` — 使用 jq 语法查询 JSON

---

## 迭代方向四：上下文压缩

**优先级**: ⭐⭐

已有 `context_compression.py` 模块，可深化集成：

### 4.1 Token 监控
- 实时监控对话 token 使用量
- 接近阈值时预警

### 4.2 自动摘要
- 达到阈值时自动摘要早期对话
- 保留系统提示词和最近 N 轮对话
- 摘要内容注入上下文

### 4.3 智能截断
- 优先截断工具执行详情
- 保留用户核心意图

---

## 迭代方向五：生产级优化

**优先级**: ⭐⭐

### 5.1 结构化日志
- JSON 格式日志输出
- 按模块分类（engine、tools、llm、security）
- 日志轮转与清理

### 5.2 指标收集
- Prometheus 指标暴露
- 请求延迟、token 消耗、错误率
- Grafana 仪表盘模板

### 5.3 配置热重载
- 监听 `~/.myagent/config.yaml` 变更
- 无需重启生效

### 5.4 健康检查
- `/health` 端点
- LLM 连接状态检测
- 磁盘空间检查

---

## 迭代方向六：更多 LLM 提供商

**优先级**: ⭐

当前支持：OpenAI、Anthropic、DeepSeek、Gemini、Qwen、Ollama、Azure、OpenRouter、Zhipu

### 6.1 国内模型
- 百度文心一言
- 讯飞星火
- 字节豆包
- 腾讯混元

### 6.2 开源模型托管
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

## 推荐迭代顺序

### 第一优先级（近期 1-2 周）
1. **Web UI 增强** — 会话管理、代码高亮、设置面板
2. **TUI 多行输入** — 替换 Input 为 TextArea

### 第二优先级（中期 2-4 周）
3. **Gateway 适配器** — Discord / Slack / Telegram
4. **工具扩展** — Git 操作、数据库查询

### 第三优先级（长期 1-2 月）
5. **上下文压缩** — 自动摘要、智能截断
6. **生产优化** — 结构化日志、指标收集
7. **更多 LLM** — 国内模型接入

---

## 决策建议

| 场景 | 推荐方向 |
|------|----------|
| 想快速看到效果 | Web UI 增强 |
| 需要多平台接入 | Gateway 适配器 |
| 处理长对话频繁 | 上下文压缩 |
| 准备生产部署 | 生产优化 |
| 团队协作场景 | Agent Teams 完善 |

---

## 相关文档

- [v0.11.0 整改方案](v0.11.0-redesign.md) — 架构整改详细方案
- [Web UI 设计规范](../design/02-web-ui-design.md) — Web UI 设计细节
- [Gateway 架构](../architecture/07-gateway.md) — Gateway 技术架构
- [概念引用](../reference/04-concept-references.md) — 参考项目概念映射
