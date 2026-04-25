# TUI 体验设计（Phase 2）

> 本文档记录 Phase 2 完成后的 MyAgent TUI 体验基线，用于约束后续 TUI 演进不要再次退化成“只有聊天框”的终端界面。

---

## 1. 目标

Phase 2 的目标不是把 TUI 做成复杂控制台，而是建立一个稳定的终端工作台骨架：

- 首屏即可理解当前状态
- 高频操作可以用键盘完成
- 配置缺失时进入可修复状态，而不是报错后退出
- 工具执行、权限审批、任务规划不再只靠长文本堆叠

---

## 2. 当前信息架构

TUI 当前由五个核心区块组成：

1. 顶部状态条
   - 展示 `agent`、`model`、`turns`、`cost`、`provider`
2. 主消息区
   - 展示 transcript 和结构化工具轨迹
3. 右侧状态面板
   - 展示状态概览、任务状态、活动轨迹、当前响应
4. 输入区
   - 支持多行输入与 Slash Commands
5. 浮层区
   - 展示权限审批、setup handoff、session summary、help、command palette

---

## 3. 交互基线

### 3.1 快捷键

- `Ctrl+K`：打开 Command Palette
- `Ctrl+L`：清空 transcript
- `Ctrl+R`：重新生成上一轮响应
- `Ctrl+D`：退出

### 3.2 Slash Commands

- `/help`
- `/agent <name>`
- `/provider <name>`
- `/model <name>`
- `/memory`
- `/plan <request>`
- `/setup`
- `/doctor`
- `/session`

### 3.3 浮层

当前浮层分为三类：

- `PermissionModalScreen`
- `InfoModalScreen`
- `CommandPaletteScreen`

规则：

- 需要用户确认的内容走 modal
- 需要展示摘要的 setup/session/help 走 modal
- 高频命令入口走 Command Palette

---

## 4. 状态模型

右侧状态面板最少展示四类状态：

### 4.1 状态概览

- 当前 `agent`
- 当前 `model`
- 当前 `workspace`
- setup 是否 ready

### 4.2 任务状态

- `state`
- `request`
- `detail`

### 4.3 活动轨迹

- 工具状态：`idle / thinking / running / approval / completed / error`
- 工具名称
- `tool_use_id`
- 最近一次详情摘要

### 4.4 当前响应

- 正在流式输出的最新内容

---

## 5. 设计约束

后续如果继续迭代 TUI，应遵守：

- 不要把 setup 错误重新退化成启动后报错
- 不要移除状态面板里的关键可见性
- 不要让权限审批回到纯文本确认
- 不要增加大量并列面板导致键盘路径变复杂

---

## 6. 后续建议

Phase 3 之前，TUI 后续可继续增强的点包括：

- Command Palette 支持搜索与过滤
- Session 切换浮层
- Task 状态机更细粒度可视化
- 更强的 tool trail 折叠与展开
- 更好的空状态与欢迎页视觉层次
