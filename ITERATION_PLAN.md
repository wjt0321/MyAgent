# MyAgent 迭代计划

## 迭代 1: Git 工具增强 ✅ 已完成

**目标**: 增强 Git 工具，添加更多实用命令

**完成内容**:
- 新增命令: pull, reset, merge, init, clone, fetch, stash
- 更新工具描述文档
- 完善 is_read_only 方法
- 所有测试通过

**分支**: phase1-git-tools (已合并到 master)

---

## 迭代 2: 插件系统 UI 完善 ✅ 已完成

**目标**: 完善插件系统的 UI 界面

**完成内容**:
- Web UI 添加 "插件" 标签页
- 插件列表展示（名称、版本、描述、启用状态、工具/Agent 数量）
- 插件启用/禁用功能
- 插件详情查看
- 命令面板支持快速切换到插件视图
- 移动端视图支持
- 所有测试通过

**后端增强** ([server.py](file:///workspace/src/myagent/web/server.py#L660-L737)):
- `/api/plugins` 增强：返回 `enabled` 和 `path` 字段
- `/api/plugins/{plugin_id}/enable` 新增：启用插件
- `/api/plugins/{plugin_id}/disable` 新增：禁用插件
- `/api/plugins/{plugin_id}` 新增：更新插件配置

**前端实现**:
- [index.html](file:///workspace/src/myagent/web/static/index.html#L222-L228)：添加插件标签页
- [app.js](file:///workspace/src/myagent/web/static/app.js#L108)：初始化插件 DOM 引用
- [ui.js](file:///workspace/src/myagent/web/static/modules/ui.js)：视图切换和命令面板支持
- [workspace.js](file:///workspace/src/myagent/web/static/modules/workspace.js#L876-L994)：插件管理逻辑
- [style.css](file:///workspace/src/myagent/web/static/style.css#L4776-L4844)：插件 UI 样式

**分支**: phase2-plugin-ui (已合并到 master)

---

## 迭代 3: 代码库搜索增强 ✅ 已完成

**目标**: 增强代码库搜索功能，支持更强大的搜索选项

**完成内容**:
- 支持正则表达式搜索
- 支持文件名搜索
- 搜索结果高亮显示
- 搜索结果显示匹配位置信息
- 界面优化，添加搜索选项开关
- 所有 41 个测试通过

**后端增强**:
- `search.py`: 更新 SearchResult 数据结构，添加 matches 字段
- `search.py`: 新增 `_search_regex`、`_search_keywords`、`_search_filename` 方法
- `search.py`: 更新 search 方法，支持 use_regex 和 search_filenames 参数
- `server.py`: 更新 `/api/codebase/search` API 接口，新增查询参数

**前端实现**:
- `index.html`: 添加搜索选项复选框
- `app.js`: 添加搜索选项 DOM 引用
- `workspace.js`: 更新 `searchCodebase` 方法，支持新功能
- `workspace.js`: 更新 `renderCodebaseResults` 方法，添加高亮显示
- `workspace.js`: 新增 `highlightMatches` 辅助方法
- `style.css`: 添加搜索选项和高亮显示的样式

**分支**: phase3-code-search (已合并到 master)

## 待执行的迭代

---

### 迭代 3: 代码库搜索增强
**优先级**: 中

**目标**: 增强代码库搜索功能
- 支持正则表达式搜索
- 支持文件名搜索
- 搜索结果高亮
- 搜索历史记录

**预计工时**: 1-2 天

---

### 迭代 4: 性能优化
**优先级**: 中

**目标**: 优化系统性能
- 上下文压缩优化
- 工具执行超时完善
- 内存使用优化
- 数据库索引优化

**预计工时**: 2-3 天

---

### 迭代 5: 用户体验提升
**优先级**: 中

**目标**: 提升用户体验
- 欢迎页面快捷指令卡片
- 代码块复制按钮
- 工具调用结果默认折叠
- 响应式布局优化
- 深色/浅色主题完善

**预计工时**: 2-3 天

---

## 迭代规则

1. 每个迭代在独立的分支上进行 (phaseX-*)
2. 迭代完成前确保所有测试通过
3. 测试通过后合并到 master
4. 合并前进行完整的测试验证
