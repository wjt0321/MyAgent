# MyAgent 迭代审查与建议（2026-04-24）

## 1. 审查结论

MyAgent 已经具备比较完整的平台骨架：LLM 抽象、Web UI、TUI、Gateway、Memory、Task Engine、Plugin、Codebase 等模块都已铺开，说明项目方向和模块切分是成熟的。

当前最主要的问题不是“缺功能”，而是：

1. 安全边界还没有真正收口
2. 前后端接口契约存在断点
3. 若干对外宣称的能力还停留在“结构已搭好、链路未闭环”阶段

如果把接下来的迭代重点放在“收口和打通”，这个项目会比继续横向加新功能更快进入稳定可用阶段。

---

## 2. 当前优先修复的问题

### P0. Web 端存在认证绕过和越权访问面

- `src/myagent/web/server.py` 的 `/api/files` 与 `/api/files/read` 直接对任意 `path` 做 `Path.resolve()` 后读取，没有用户认证，也没有工作区边界限制。
- WebSocket 入口 `/ws/{session_id}` 也没有校验当前用户，只按 `session_id` 取会话。

影响：

- 知道会话 ID 的其他用户可以直接接入别人的对话 WebSocket
- 即使启用了 JWT，文件浏览和文件读取接口仍可被匿名访问
- 前端文件树实质上可浏览并读取宿主机任意可访问路径，不只是项目工作区

建议：

1. 所有 Web API 默认走统一认证依赖，按白名单开放少量公开接口
2. WebSocket 增加 token 校验，并在 `store.get()` 时带 `user_id`
3. 文件相关接口限制在项目根目录或 workspace 根目录内，拒绝越界路径

### P0. GitHub Webhook 验签逻辑不可信

`/webhook/github` 当前把 `payload.get("secret")` 填进 `config.extra["webhook_secret"]`，随后再拿这个值校验签名。也就是说，服务端实际上信任了请求体里携带的 secret。

影响：

- 攻击者可以自行构造 payload 中的 `secret`
- 验签失去意义，Webhook 来源无法被真正确认

建议：

1. Webhook secret 只能来自服务端配置或环境变量
2. 若未配置 secret，应显式拒绝生产环境请求，而不是降级为跳过校验
3. 为验签增加单元测试和错误日志字段

### P1. 权限审批链路前后端契约不一致，审批无法可靠继续

后端在发送 `permission_request` 时没有把 `tool_use_id` 透传给前端，但前端确认/拒绝时依赖 `tool_use_id` 调用 `approve_permission`。

影响：

- 用户点击 Allow / Deny 后，后端可能找不到对应 tool use
- 需要人工审批的工具链路不稳定

建议：

1. `ToolExecutionStarted`、`PermissionRequestEvent`、WebSocket 消息统一携带 `tool_use_id`
2. 为审批流补一条端到端测试：`ASK -> modal -> approve -> continue`
3. Gateway 与 Web UI 复用同一份事件契约定义，避免再分叉

### P1. Task Engine 的“批准后执行”还没有闭环

`POST /api/tasks/{task_id}/approve` 当前只把 `plan_approved` 置为 `true` 就返回了，但前端提示的是“已批准，开始执行”。

影响：

- UI 给出错误反馈
- Task Engine 目前更像计划生成器，而不是完整的 Plan -> Execute -> Review 工作流

建议：

1. 批准后应真正触发 `execute_task()`
2. 执行进度通过 WebSocket/SSE 推送到前端
3. 执行完成后自动进入 `review_task()`，把 Review 结果映射到任务面板

### P1. Session 更新链路存在字段错误和持久化缺口

`PATCH /api/sessions/{session_id}` 在处理 `agent` 时写入的是 `session.agent_type`，但 `Session` 数据结构实际字段是 `agent`。同时该接口更新后没有调用持久化保存。

影响：

- Agent 切换可能只在前端假性成功
- Session 的 agent/model 更新刷新后可能丢失

建议：

1. 修正字段名并调用 `store.update(session)`
2. 为 session 的 create / patch / reload 补回归测试
3. 会话结构统一收敛成单一 schema，避免前端自己维护状态真相

### P2. 前端还有数个“已做 UI，未做后端”的悬空交互

当前前端还调用了几个后端并不存在的重置接口：

- `DELETE /api/sessions/{id}/messages`
- `DELETE /api/sessions`
- `DELETE /api/config`

同时新建会话默认模型仍硬编码为 `glm-4.7`，和配置系统不一致。

影响：

- 页面上的“重置”能力是假的，用户点击后只能走错误分支
- 模型默认值出现多处来源，后续会越来越难维护

建议：

1. 删除未实现入口，或尽快补齐对应后端接口
2. 新建会话默认模型统一读取配置或后端返回值
3. 做一次前后端 API 契约盘点，清掉所有“前端先写了但后端没接”的残留

---

## 3. 迭代建议路线图

### Sprint 1：先做“安全收口 + 契约补齐”

目标：把 Web UI 从“演示可用”提升到“本地/内网可稳定使用”。

建议范围：

1. 统一 Web 鉴权中间件和依赖注入
2. WebSocket 鉴权与 session owner 校验
3. 文件 API 限制访问边界
4. GitHub Webhook 验签修复
5. Session patch / reset / permission 相关接口补齐
6. 补 8 到 12 条 Web/API 端到端测试

这一步完成后，项目的可信度会明显提升。

### Sprint 2：打通 Task Engine 和 Agent 工作流

目标：让 Plan -> Execute -> Review 成为真正可演示、可复用的核心能力。

建议范围：

1. 批准计划后自动执行子任务
2. 前端展示任务状态机和实时进度
3. Review 结果结构化展示（成功、问题、建议、产物）
4. Team/Agent 面板和任务执行状态联动
5. 失败重试、人工中断、任务恢复

这一步会把 MyAgent 从“聊天界面 + 工具集”拉升到“有任务闭环的 Agent 平台”。

### Sprint 3：对齐宣传能力，减少“文档已完成 / 功能未闭环”落差

目标：README、文档、界面行为与真实能力保持一致。

建议范围：

1. 逐项核对 README 中的已支持能力
2. 把“骨架完成”和“生产可用”拆成不同状态标识
3. 对 Gateway、Plugin、Context Compression、Git 工具做能力矩阵
4. 文档中增加“已验证场景 / 未验证场景 / 已知限制”

这一步会减少用户预期错位，也有利于后续开源协作。

---

## 4. 更长期的产品化建议

### 4.1 平台层

1. 建立统一事件总线 schema
2. 把 Web UI、TUI、Gateway 的事件映射统一抽象
3. 为 session、task、memory、plugin 建立稳定的持久化模型

### 4.2 工程层

1. 增加分层测试策略：单元测试、接口测试、WebSocket 测试、适配器集成测试
2. 建立最小可用 CI：ruff + mypy + pytest + smoke test
3. 加入 feature flag，避免新功能直接暴露到默认界面

### 4.3 产品层

1. 把“权限审批”“任务流”“代码库检索”“记忆”作为核心卖点重点打磨
2. Web UI 优先保证信息层级和任务闭环，而不是继续堆新面板
3. Gateway 先选一个平台做深做透，建议 Telegram 或 GitHub

---

## 5. 建议的文档补充

建议在后续文档体系中补 3 份最实用的文档：

1. `docs/reference/web-api-contract.md`
   说明所有前后端接口、请求/响应、鉴权要求、错误码

2. `docs/architecture/security-boundary.md`
   明确 Web UI、文件访问、Webhook、工具执行、Workspace 的信任边界

3. `docs/plans/2026-04-security-and-workflow-hardening.md`
   把本次审查里的 P0/P1 问题直接转成可执行迭代计划

---

## 6. 最终判断

这个项目最大的价值不是“已经做了很多功能”，而是已经有了足够好的架构骨架，值得进入一次系统性的“收口迭代”。

当前最值得做的不是继续扩展模块，而是把下面三件事彻底做实：

1. 安全边界
2. 前后端契约
3. Task/Agent 工作流闭环

如果这三件事完成，MyAgent 会从“很强的个人原型”明显跨到“可持续迭代的平台产品”。
