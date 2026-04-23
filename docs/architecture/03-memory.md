# Memory 系统设计

> Memory 系统让 Agent 记住用户，越用越懂。
> 灵感来源: Claude Code (`memory/types.ts`) + OpenHarness (`memory/manager.py`)

---

## 1. 设计目标

1. **持久化**: 对话结束后记忆不丢失
2. **结构化**: Markdown + Frontmatter，人工可编辑
3. **自动收集**: LLM 自动识别值得记忆的信息
4. **手动管理**: Web UI 支持查看、编辑、删除

---

## 2. 记忆类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `user` | 用户画像 | 技术背景、偏好 |
| `feedback` | 反馈指导 | 喜欢简洁、不要总结 |
| `project` | 项目上下文 | 当前目标、决策 |
| `reference` | 外部引用 | 文档链接、系统信息 |

**来源**: Claude Code 的五级记忆类型

---

## 3. 存储格式

### 3.1 文件格式

```markdown
---
name: User Role
description: User is a backend engineer focused on Python and Go
type: user
---

User is a senior backend engineer with 8 years of experience.
Primary languages: Python, Go.
Currently working on: MyAgent (AI agent platform).

**Why:** Understanding user's technical background helps tailor explanations.
**How to apply:** Use technical terms freely, suggest best practices from Python/Go ecosystem.
```

### 3.2 索引格式

```markdown
# Memory Index

- [User Role](user_role.md) — 用户是后端工程师，专注 Python/Go
- [Feedback Style](feedback_style.md) — 喜欢简洁回答，不要总结
- [Project Context](project_context.md) — 正在开发 MyAgent 项目
```

**来源**: Claude Code MEMORY.md 索引

---

## 4. 核心类

### 4.1 MemoryEntry

```python
@dataclass
class MemoryEntry:
    name: str
    description: str
    type: MemoryType
    content: str
    path: Path | None = None

    def to_markdown(self) -> str:
        return f"---\nname: {self.name}\ndescription: {self.description}\ntype: {self.type.value}\n---\n\n{self.content}"
```

### 4.2 MemoryManager

```python
class MemoryManager:
    def __init__(self, memory_dir: Path):
        self.memory_dir = Path(memory_dir)
        self.index_path = self.memory_dir / "MEMORY.md"

    def save_memory(self, entry: MemoryEntry) -> Path:
        slug = re.sub(r'[^a-zA-Z0-9]+', '_', entry.name.strip().lower()).strip('_')
        path = self.memory_dir / f"{slug}.md"
        path.write_text(entry.to_markdown(), encoding="utf-8")
        self._update_index(entry, path.name)
        return path

    def get_memory(self, name: str) -> MemoryEntry | None:
        # 查找并解析记忆

    def delete_memory(self, name: str) -> bool:
        # 删除记忆文件并更新索引
```

### 4.3 MemoryCollector

```python
class MemoryCollector:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self._pending_conversations = []

    def collect_from_turn(self, user_message, assistant_response, llm_client):
        # 缓冲对话，累积到阈值后触发提取

    def extract_memories(self, conversation, llm_client, existing=None):
        # 使用 LLM 提取记忆

    def save_extracted_memories(self, entries):
        # 保存提取的记忆，支持去重和合并
```

---

## 5. 自动收集流程

```
对话结束
    ↓
LLM 分析对话内容
    ↓
提取关键信息
    ↓
分类 (user/feedback/project/reference)
    ↓
保存到 memory/
    ↓
更新 MEMORY.md 索引
```

---

## 6. 与参考项目的对比

| 维度 | MyAgent | Claude Code | OpenHarness |
|------|---------|-------------|-------------|
| 存储格式 | Markdown + Frontmatter | Markdown + Frontmatter | Markdown 文件 |
| 索引 | MEMORY.md | MEMORY.md | MEMORY.md |
| 自动收集 | 增量缓冲 | 每次对话后 | 无 |
| 去重 | 名称匹配 + 内容合并 | 记忆前验证 | 文件锁 |
| 类型 | 4 种 | 5 种 | 无明确分类 |
| Web UI | 支持 CRUD | 无 | 无 |

---

## 7. 使用方式

### 7.1 自动收集

对话结束后自动触发，无需人工干预。

### 7.2 手动管理

Web UI → Settings → Memory 标签页：
- 查看所有记忆
- 新建记忆
- 编辑记忆
- 删除记忆

### 7.3 Python API

```python
from myagent.memory.manager import MemoryManager, MemoryEntry, MemoryType

mm = MemoryManager("~/.myagent/memory")
entry = MemoryEntry(
    name="User Preference",
    description="User likes concise answers",
    type=MemoryType.FEEDBACK,
    content="User prefers short, direct answers without summaries."
)
mm.save_memory(entry)
```
