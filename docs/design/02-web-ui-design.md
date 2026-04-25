# Web UI 设计规范

> MyAgent Web UI 基于 FastAPI + 原生 HTML/JS/CSS 构建，提供浏览器内的 AI Agent 交互体验。

---

## 1. 设计目标

1. **现代美观**: 暗色主题，玻璃拟态效果
2. **响应式**: 适配桌面和移动端
3. **实时通信**: WebSocket 流式消息
4. **功能丰富**: 文件浏览、会话管理、设置面板

---

## 2. 技术栈

- **后端**: FastAPI + WebSocket
- **前端**: 原生 HTML5 + CSS3 + JavaScript (ES6+)
- **样式**: CSS Variables + Glassmorphism
- **图标**: SVG 内联
- **Markdown**: marked.js
- **代码高亮**: Prism.js

---

## 3. 布局

```
+----------------+--------------------------------+--------+
| Sessions / Nav | Header + Session Status Chip   | Detail |
+----------------+--------------------------------+ Sidebar+
|                | Chat / Tasks / Files /         |        |
| Grouped        | Workspace / Team Workbench     | File   |
| Navigation     |                                | Tool   |
|                |                                | Task   |
+----------------+--------------------------------+--------+
|                | Composer + Slash Commands / Ctrl+K      |
+----------------+-----------------------------------------+
```

---

## 4. 主题系统

### 4.1 CSS Variables

```css
:root {
  --bg-primary: #0f0f1a;
  --bg-secondary: #16162a;
  --bg-tertiary: #1e1e3a;
  --bg-hover: rgba(99, 102, 241, 0.1);
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent: #6366f1;
  --accent-hover: #818cf8;
  --accent-soft: rgba(99, 102, 241, 0.15);
  --border-default: rgba(148, 163, 184, 0.15);
  --border-subtle: rgba(148, 163, 184, 0.08);
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
}
```

### 4.2 Glassmorphism

```css
.glass {
  background: rgba(22, 22, 42, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border-default);
}
```

---

## 5. 组件规范

### 5.1 消息气泡

- **用户**: 右侧对齐，渐变背景，圆角
- **助手**: 左侧对齐，深色背景，圆角
- **工具**: 中间对齐，可折叠卡片

### 5.2 侧边栏

- **Workbench Nav**: Chat、Tasks、Files、Workspace、Team 五个主入口
- **会话列表**: 独立保留在导航下方，支持导入、导出、重命名、删除
- **辅助面板**: 任务、团队、Workspace、文件树继续放在左侧，以便快速概览

### 5.3 详情侧栏

- **统一详情入口**: 会话、任务、工具卡片、文件预览都进入同一个右侧区域
- **文件预览模式**: 代码与 Markdown 预览复用同一侧栏
- **上下文模式**: 未打开文件时，显示当前会话、任务或工具详情

### 5.4 命令面板

- **快捷键**: `Ctrl+K`
- **能力**: 新建会话、切换视图、打开设置、聚焦输入框、查看帮助
- **目标**: 减少用户在高频操作中的鼠标移动成本

### 5.5 设置面板

- **Agent**: 选择 Agent、系统提示词
- **Memory**: 记忆列表、新建/编辑/删除
- **代码库**: 搜索、重建索引
- **重置**: 重置会话/配置
- **外观**: 主题切换
- **关于**: 版本信息、统计

---

## 6. 交互模式

### 6.1 流式输出

WebSocket 接收 `assistant_delta` 事件，实时追加到消息内容。

### 6.2 Markdown 渲染

使用 marked.js 解析 Markdown，支持：
- 标题、列表、代码块
- 表格、引用
- 任务列表

### 6.3 文件预览

点击文件树中的文件，右侧详情侧栏显示代码或 Markdown 预览。

### 6.4 Slash Commands

Web 工作台输入框支持以下命令：

- `/plan <请求>`: 创建任务计划
- `/agent <name>`: 切换 agent
- `/model <name>`: 切换 model
- `/session`: 查看当前会话摘要
- `/setup`: 打开设置面板
- `/doctor`: 显示当前 Web 工作台状态

### 6.5 任务工作流

输入 `/plan <请求>` 触发：
1. 显示计划步骤列表
2. 用户批准
3. 实时显示执行进度

### 6.6 工具卡片

- 工具调用与工具结果统一渲染为可折叠卡片
- 点击卡片后，详情侧栏显示结构化参数或输出
- 长输出不再直接淹没聊天流

---

## 7. API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/ws` | WebSocket | 实时对话 |
| `/api/sessions` | GET/POST | 会话管理 |
| `/api/memories` | GET/POST/DELETE | 记忆管理 |
| `/api/workspace` | GET | Workspace 信息 |
| `/api/team` | GET | 团队状态 |
| `/api/tasks/plan` | POST | 创建任务计划 |
| `/api/codebase/index` | GET | 代码库索引 |
| `/api/codebase/search` | GET | 代码搜索 |
| `/api/files/tree` | GET | 文件树 |
| `/api/files/read` | GET | 读取文件 |

---

## 8. 与参考项目的对比

| 维度 | MyAgent | OpenClaw | Hermes Agent |
|------|---------|----------|--------------|
| 框架 | FastAPI + 原生 JS | 自研网关 | aiohttp |
| 前端 | 原生 HTML/CSS/JS | 无内置前端 | 无 |
| 主题 | 暗色 + Glassmorphism | 终端主题 | 无 |
| 流式 | WebSocket | WebSocket | 无 |
| 文件浏览 | 侧边栏树 | 无 | 无 |
| 会话管理 | 支持 | 无 | 支持 |
| 代码高亮 | Prism.js | 无 | 无 |
