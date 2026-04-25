# MyAgent 体验收敛与平台化迭代计划（2026-04-25）

> 目标：让 MyAgent 在体验上逐步接近 `hermes-agent` 与 `openclaw` 的结合体，但保持 MyAgent 现有 Python 平台骨架不被 UI 反向绑死。

---

## 1. 目标重述

你希望 MyAgent 后续迭代不只是“功能变多”，而是从整体使用体验上更接近两个参考项目的强项组合：

1. **借鉴 Hermes Agent**
   - 初始化设置合理、首启路径顺滑
   - TUI 交互高级、清晰、实用
   - 阻塞交互、审批、状态反馈有明显的产品化完成度

2. **借鉴 OpenClaw**
   - Quickstart 容易理解，用户进入系统的成本低
   - Web 端信息架构完整，聊天、配置、控制台、会话管理之间衔接自然
   - 视觉层次、工具展示、命令体系、状态可视化都很成熟

3. **保留 MyAgent 自身优势**
   - 以 Python 为核心的 LLM / Tool / Memory / Task / Gateway 骨架
   - Web UI、TUI、Gateway、Task Engine、Codebase、Memory 的统一平台方向
   - 面向本地开发者工作流的可扩展性

**最终目标不是“像谁”，而是形成一个明确定位：**

- **初始化与 TUI 体验接近 Hermes**
- **Web 工作台体验接近 OpenClaw**
- **Agent 平台骨架和后端整合能力保持 MyAgent 的方向**

---

## 2. 当前判断

MyAgent 现在的主要问题已经不是“完全没有功能”，而是以下四类体验断层同时存在：

### 2.1 首启体验断层

- `init / doctor / web / tui` 之间还没有形成统一的 onboarding（首次引导）路径
- 用户能启动服务，但不一定知道“下一步该做什么”
- 配置缺失时，系统缺少类似 Hermes 的“原地修复”体验

### 2.2 TUI 体验断层

- 现有 TUI 更像“可用界面”，还不像“成熟工作台”
- 会话状态、当前模型、工具执行、审批请求、记忆状态、任务状态的可见性不足
- 交互层还缺少高级体验：Slash Commands、Command Palette、结构化工具轨迹、阻塞交互浮层

### 2.3 Web 体验断层

- Web 已有聊天与管理面板，但信息架构还没有收口成真正的“工作台”
- 工具结果展示、任务流程展示、设置入口、会话控制、搜索/命令入口都还偏初级
- 距离 OpenClaw 那种“聊天 + 控制台 + 配置 + 状态总览”的控制台体验还有明显差距

### 2.4 工程信号断层

- 事件契约仍有不一致，尤其是 `tool_use_id` 审批链路
- 测试集与实现出现漂移，CI 结果无法完全代表真实质量
- 文档、README、界面行为、实际能力之间还没有统一口径

---

## 3. 对标结论

## 3.1 Hermes 值得迁移的部分

### 初始化/首启

- 未配置 provider 时，先拦截，再引导 setup，而不是进入半可用状态
- quick setup 先完成最关键配置，其余走推荐默认值
- setup 完成后明确输出“下一步动作”

### TUI

- 单主视图 + 浮层，而不是把所有东西塞进多栏
- 审批、澄清、密码、确认这类阻塞交互使用 overlay/modal，而不是把提示文本混在消息流里
- 工具执行有结构化轨迹，不只是 stdout 文本堆叠
- 会话顶部始终显示状态：模型、cwd、可用工具、连接情况、运行态

## 3.2 OpenClaw 值得迁移的部分

### Quickstart / 进入路径

- Quickstart 入口短、清楚、不重复
- 用户进入系统后很快知道“聊天、配置、Agent、Session、Logs”都在哪里

### Web

- 聊天页不是孤立页，而是工作台的一部分
- 工具调用是卡片化、可折叠、可查看详情
- 会话参数可即时调整
- Slash Commands 与 Command Palette 结合，提高熟练用户效率
- 视觉上层次明确：导航、主内容、详情区、状态区分工清晰

---

## 4. 新一轮迭代总目标

建议把未来迭代从“功能堆叠”切换为“体验收敛 + 平台闭环”，分四条主线推进：

1. **主线 A：首启与配置体验收敛**
2. **主线 B：TUI 体验重构**
3. **主线 C：Web 工作台重构**
4. **主线 D：事件契约、测试与文档收口**

这四条主线不是并列独立的，应按以下顺序推进：

1. 先修底层契约与质量门
2. 再统一首启与配置体验
3. 然后重构 TUI
4. 最后重构 Web 工作台

原因很简单：

- 如果契约不稳，UI 升级后会持续返工
- 如果首启不顺，TUI 和 Web 再好看也挡不住首次使用流失
- 如果 TUI 和 Web 同时大改，但底层状态模型没统一，后续维护成本会急剧上升

---

## 5. 设计原则

后续所有改造建议遵循以下原则：

### 5.1 先把“能顺畅用起来”做到极致

优先级高于继续新增模块。

重点包括：

- 首次启动就能成功进入可用状态
- 配置错误能被明确诊断和引导修复
- 当前系统处于什么状态，用户一眼能看懂

### 5.2 UI 不反向绑死核心架构

TUI、Web、Gateway 都应消费统一的后端能力，而不是各自维护一套状态真相。

必须统一的对象：

- session schema
- task schema
- permission event schema
- tool execution event schema
- config view model

### 5.3 高级体验来自“状态可见 + 交互闭环”

不是来自动画数量。

真正提升体验的，是这些能力：

- 当前模型和 agent 是否可见
- 工具执行是否可追踪
- 审批是否能继续闭环
- task 是否有状态机和结果面板
- 配置是否可以原地修复

### 5.4 先做强主场，再扩外围

建议把资源集中到：

- 本地开发者使用场景
- TUI 核心交互
- Web 控制台
- Telegram / GitHub 两个最有代表性的 Gateway 场景

不要在体验层还没做实之前继续大量扩新平台、新面板、新宣传点。

---

## 6. 目标体验蓝图

## 6.1 首启体验蓝图

目标：**5 分钟内完成首次可用配置，并进入第一次真实对话。**

### 目标流程

1. 用户执行 `myagent init`
2. 向导先检测已有配置、缺失项、环境变量
3. 若是首次使用，只询问最少必要项：
   - 选择 provider
   - 输入 API key
   - 选择默认 model
   - 选择默认交互方式（TUI / Web）
4. 系统自动写入推荐默认值：
   - agent 默认值
   - memory 开关
   - context/compression 默认值
   - workspace 默认路径
5. 向导输出“设置摘要 + 下一步命令”
6. 用户可直接进入：
   - `myagent --tui`
   - `myagent web`

### 体验要求

- 配置缺失不应静默失败
- 未配置状态下，TUI/Web 都能明确显示 `Setup Required`
- 用户不必离开当前交互界面就能进入 setup 修复流程

## 6.2 TUI 蓝图

目标：**让 TUI 成为 MyAgent 的第一主交互面，而不是附属界面。**

### 目标结构

- 顶部状态区：当前 agent、model、workspace、权限状态、会话状态
- 主消息区：Transcript
- 输入区：支持多行输入、Slash Commands、历史输入
- 浮层区：审批、确认、帮助、会话切换、setup handoff
- 侧信息区或折叠区：工具轨迹、任务状态、记忆状态

### 必须具备的高级体验

- Slash Commands
- Command Palette
- Setup Required 原地修复
- 结构化 tool trail
- 权限审批浮层
- Task 状态可视化
- 空会话欢迎页

## 6.3 Web 蓝图

目标：**让 Web 从“聊天页 + 面板”升级为“开发者 Agent 工作台”。**

### 目标结构

- 顶部：当前 session、agent、model、命令入口、状态提示
- 左侧导航：Chat / Sessions / Tasks / Files / Memory / Agents / Settings / Logs
- 主区：聊天流与任务流
- 右侧详情区：工具详情、文件预览、任务详情、审批详情

### 必须具备的高级体验

- 命令面板（Command Palette）
- Slash Commands
- 工具卡片可折叠展示
- 任务流可视化
- 即时会话参数控制
- 空状态和欢迎面板
- 更成熟的明暗主题与层级系统

---

## 7. 分阶段迭代计划

## Phase 0：质量与契约基线

**目标：先把后续 UI 改造所依赖的底座稳定下来。**

### 范围

1. 修复 Web/Gateway 权限审批链路中的 `tool_use_id` 透传
2. 统一 `ToolExecutionStarted` / `PermissionRequestEvent` / `ToolExecutionCompleted` 的对外事件格式
3. 修复 `Session.save()` 空实现遗留路径
4. 清理与实现失配的测试
5. 建立最小质量门：
   - `ruff check`
   - `mypy src/`
   - Web/API smoke tests

### 交付物

- 统一事件契约文档
- 最小可用 CI
- 通过的基础回归测试集

### 验收标准

- Web 端 `ASK -> approve -> continue` 可用
- Gateway 端 `ASK -> approve -> continue` 可用
- Session 变更与导入都能持久化
- 关键 smoke tests 全绿

---

## Phase 1：首启与 Quick Setup 收敛

**目标：把首次使用门槛降到最低。**

### 范围

1. 重构 `myagent init`
   - 区分首次配置与高级配置
   - 默认值策略集中化
2. 重构 `doctor`
   - 输出“问题 -> 原因 -> 修复动作”
3. 在 CLI、TUI、Web 中增加统一的 setup status 检测
4. 设计 `Setup Required` 状态页/面板
5. 输出 setup summary 和 next steps

### 交付物

- Quick Setup 向导
- Setup 状态检测 API
- 首启体验文档

### 验收标准

- 新用户可以在 5 分钟内完成 provider 配置并成功发起第一轮对话
- 缺少 API key 时，TUI/Web 不进入坏状态，而是进入 setup 引导
- `doctor` 能指出缺失 provider、缺失 key、配置文件错误、workspace 问题

---

## Phase 2：TUI 体验重构

**目标：把 TUI 做成“高级但不复杂”的主交互界面。**

### 范围

1. 重构 TUI 信息架构
   - 顶部状态条
   - 主消息区
   - 输入区
   - 浮层交互区
2. 增加 Slash Commands
   - `/help`
   - `/agent`
   - `/model`
   - `/plan`
   - `/memory`
   - `/setup`
   - `/session`
3. 增加 Command Palette
4. 重构工具执行展示
   - Thinking
   - Tool Call
   - Tool Result
   - Permission Request
5. 增加 Setup Handoff
6. 增加任务流状态显示

### 交付物

- 新版 TUI 布局
- Slash Command 系统
- TUI 状态模型

### 验收标准

- 首屏能显示当前 agent/model/workspace
- 工具执行不再只是纯文本刷屏
- 审批、确认、setup 都通过浮层完成
- 熟练用户可以只靠键盘完成高频操作

---

## Phase 3：Web 工作台重构

**目标：让 Web 端达到 OpenClaw 那种“好用、清楚、可控制”的工作台水准。**

### 范围

1. 重构信息架构
   - 左侧从面板堆叠改为分组导航
   - 主区明确区分聊天流、任务流、详情流
2. 加入 Command Palette
3. 加入 Slash Commands
4. 重构工具结果呈现
   - 工具卡片
   - 折叠/展开
   - 详情侧栏
5. 会话控制条升级
   - 即时切换 model
   - 即时切换 agent
   - 显示 session 状态
6. 欢迎页升级
   - 快捷操作卡片
   - 最近会话
   - 当前能力说明
7. 主题系统升级
   - 统一 token
   - 明暗模式
   - 更成熟的层级与强调色

### 交付物

- 新版 Web IA
- 新版工具卡片系统
- 新版欢迎页与状态条

### 验收标准

- 用户能在 10 秒内找到 Session、Task、Files、Memory、Settings
- 长工具输出不再淹没聊天区
- 模型与 agent 切换即时生效
- 移动端至少保持“能用且清楚”

---

## Phase 4：Task / Agent 工作流可见化

**目标：把 MyAgent 从“能聊天调用工具”提升为“能执行和审查任务”。**

### 范围

1. 任务执行进度推送到 TUI/Web
2. Task 面板展示：
   - 当前状态
   - 子任务进度
   - 使用的 agent
   - review 结果
3. Team 面板与 Task 联动
4. 失败、取消、重试、恢复入口
5. Review 结果结构化展示

### 交付物

- Task 状态机可视化
- Team / Task 联动面板
- Review 结果面板

### 验收标准

- `/plan` 之后的流程对用户是可见的
- 批准后不是“假开始”，而是真的能看到执行进度
- review 结果可以直接被用户理解和消费

---

## Phase 5：体验打磨与品牌层

**目标：在核心体验闭环成立后，再做高级感与辨识度。**

### 范围

1. TUI 视觉语言统一
2. Web 主题家族化
3. 动效、空状态、快捷卡片、帮助提示完善
4. README、截图、演示路径、文档入口统一

### 交付物

- 新版截图与演示素材
- 新版 Quickstart
- 体验一致性的设计说明

### 验收标准

- 文档、截图、真实行为一致
- 新用户能理解 MyAgent 与 Hermes/OpenClaw 的区别与定位
- 产品观感从“工程原型”提升到“稳定平台”

---

## 8. 版本安排建议

建议按三个波次安排，而不是按零散 issue 推动：

### Wave 1：底座收口（1-2 周）

- Phase 0
- Phase 1 的 setup status

### Wave 2：主交互升级（2-4 周）

- Phase 2
- Phase 3 的 IA 与工具展示

### Wave 3：平台闭环（2-3 周）

- Phase 4
- Phase 5

---

## 9. 优先级清单

### P0：必须先做

1. `tool_use_id` 审批链路修复
2. Session 持久化遗留修复
3. 测试集与实现重新对齐
4. setup status + Quick Setup

### P1：最能体现体验提升

1. TUI 顶部状态条
2. TUI 浮层审批与 setup handoff
3. Web 工具卡片化
4. Web 导航重构
5. Slash Commands
6. Command Palette

### P2：中期增强

1. Task 可视化
2. Team 联动
3. 主题系统升级
4. 欢迎页和空状态重做

### P3：后期打磨

1. 品牌化视觉
2. 高级动效
3. 更多平台适配器的体验统一

---

## 10. 不建议现在做的事

在下列事项完成前，不建议继续大规模扩功能面：

- 不建议继续大量新增 Gateway 平台
- 不建议继续扩很多“还没闭环”的设置面板
- 不建议先做大量视觉动效而不先修状态可见性
- 不建议继续宣传“生产可用”超出实际验证范围的能力

---

## 11. 推荐新增文档

为了支撑本计划，建议补齐以下文档：

1. `docs/architecture/09-ui-state-and-event-contract.md`
   - 统一 TUI/Web/Gateway 事件契约

2. `docs/design/04-onboarding-and-setup.md`
   - 记录首启、setup、doctor、handoff 的设计

3. `docs/design/05-tui-experience.md`
   - 记录 TUI 信息架构、交互层与状态模型

4. `docs/design/06-web-workbench.md`
   - 记录 Web 工作台 IA、命令体系、工具展示规则

---

## 12. 最终建议

如果只用一句话总结这份计划，那就是：

**MyAgent 下一步最值得做的，不是再扩模块，而是把“首启体验、TUI、Web 工作台、任务闭环”四件事做到能让人一眼感受到产品完成度。**

只有这样，MyAgent 才会真正体现出：

- Hermes 的高级终端体验
- OpenClaw 的成熟 Web 工作台体验
- 以及 MyAgent 自己的 Agent 平台整合能力

这也是它从“架构不错的个人原型”走向“可持续打磨的平台产品”的关键一步。
