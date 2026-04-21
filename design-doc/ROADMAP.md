# MyAgent 迭代路线图

## 当前状态（MVP 完成）

- Phase 1-4 全部完成
- 348 个测试全部通过
- CLI 基础功能可用
- 缺少：TUI、Web UI、Gateway 完整实现

---

## Phase 5: TUI 终端界面（当前重点）

### 5.1 TUI 核心框架
- [ ] Textual App 主框架
- [ ] 三栏/单栏布局（对话区 + 状态栏）
- [ ] Header（版本、Agent、成本）
- [ ] Footer（快捷键提示）

### 5.2 对话交互
- [ ] RichLog 对话历史
- [ ] 流式输出实时显示
- [ ] 用户输入 Composer
- [ ] /commands 支持（/exit, /clear, /agent, /provider）

### 5.3 工具可视化
- [ ] 工具调用显示（可折叠）
- [ ] 代码差异高亮
- [ ] 文件读写状态

### 5.4 权限与配置
- [ ] 权限审批弹窗（ModalScreen）
- [ ] Provider 切换界面
- [ ] API Key 配置

---

## Phase 6: Web 界面

### 6.1 后端 API
- [ ] FastAPI 服务
- [ ] WebSocket 实时通信
- [ ] Session 管理 REST API
- [ ] 文件上传/下载

### 6.2 前端界面
- [ ] React/Vue 聊天界面
- [ ] 代码高亮（Monaco Editor）
- [ ] 工具执行结果展示
- [ ] Markdown 渲染

### 6.3 多用户支持
- [ ] 用户认证
- [ ] 会话隔离
- [ ] 历史记录持久化

---

## Phase 7: Gateway 完整实现

### 7.1 Discord 适配器
- [ ] discord.py 集成
- [ ] 斜杠命令支持
- [ ] 线程对话

### 7.2 Slack 适配器
- [ ] slack-sdk 集成
- [ ] Block Kit 消息格式
- [ ] 提及触发

### 7.3 Telegram 适配器
- [ ] python-telegram-bot 集成
- [ ] 命令菜单
- [ ] 内联查询

### 7.4 Webhook 完善
- [ ] HTTP API 端点
- [ ] 消息签名验证
- [ ] 速率限制

---

## Phase 8: 生产级优化

### 8.1 性能
- [ ] 异步工具并行执行
- [ ] 连接池（LLM / 数据库）
- [ ] 缓存层（Redis）

### 8.2 可观测性
- [ ] 结构化日志（JSON）
- [ ] 指标收集（Prometheus）
- [ ] 分布式追踪

### 8.3 部署
- [ ] Docker 镜像
- [ ] Docker Compose 编排
- [ ] Helm Chart（K8s）

---

## Phase 9: 生态扩展

### 9.1 更多 LLM 提供商
- [ ] 百度文心一言
- [ ] 阿里通义千问
- [ ] 讯飞星火
- [ ] 字节豆包
- [ ] 腾讯混元

### 9.2 更多工具
- [ ] 数据库查询工具
- [ ] Git 操作工具
- [ ] Docker 管理工具
- [ ] 浏览器自动化（Playwright）

### 9.3 集成
- [ ] VS Code 插件
- [ ] JetBrains 插件
- [ ] GitHub App
- [ ] CI/CD 集成
