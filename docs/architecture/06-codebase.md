# 代码理解系统设计

> 代码理解系统自动扫描、索引、搜索代码库，为 Agent 提供上下文。
> 灵感来源: Claude Code (`src/context.ts`) — 自动扫描代码库生成索引

---

## 1. 设计目标

1. **自动扫描**: 无需人工配置，自动发现代码结构
2. **结构索引**: 生成代码库索引文件
3. **语义搜索**: 支持关键词和自然语言查询
4. **上下文注入**: 自动读取相关代码到对话

---

## 2. 支持语言

| 语言 | 扩展名 |
|------|--------|
| Python | `.py` |
| JavaScript | `.js`, `.jsx` |
| TypeScript | `.ts`, `.tsx` |
| Java | `.java` |
| Go | `.go` |
| Rust | `.rs` |
| C/C++ | `.c`, `.cpp`, `.h`, `.hpp` |
| Ruby | `.rb` |
| PHP | `.php` |
| Swift | `.swift` |
| Kotlin | `.kt` |
| Scala | `.scala` |
| Markdown | `.md` |
| JSON | `.json` |
| YAML | `.yaml`, `.yml` |
| TOML | `.toml` |
| Shell | `.sh` |
| HTML | `.html` |
| CSS | `.css` |
| SQL | `.sql` |

---

## 3. 核心类

### 3.1 CodebaseIndexer

```python
class CodebaseIndexer:
    def __init__(self, root_dir: str | Path):
        self.root = Path(root_dir).resolve()

    def scan(self) -> CodebaseIndex:
        # 递归扫描代码目录
        # 解析 Python AST 提取类名、函数名
        # 返回 CodebaseIndex

    def generate_markdown(self) -> str:
        # 生成 codebase-index.md 内容

    def save_index(self, output_path=None) -> Path:
        # 保存索引文件
```

### 3.2 CodeFile

```python
@dataclass
class CodeFile:
    path: str
    language: str
    description: str        # 从文档字符串提取
    classes: list[str]      # 类名列表
    functions: list[str]    # 函数名列表
    imports: list[str]      # 导入语句
    size: int               # 行数
```

### 3.3 CodebaseSearch

```python
class CodebaseSearch:
    def __init__(self, root_dir: str | Path):
        self.root = Path(root_dir).resolve()
        self.indexer = CodebaseIndexer(self.root)

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        # 关键词搜索
        # 智能评分：定义行 +3，注释 +2，普通匹配 +1

    def find_definition(self, symbol: str) -> list[SearchResult]:
        # 查找符号定义位置

    def get_related_files(self, path: str) -> list[str]:
        # 查找相关文件
```

### 3.4 SearchResult

```python
@dataclass
class SearchResult:
    path: str
    language: str
    content: str
    line_number: int
    score: float           # 相关度
    context_before: list[str]
    context_after: list[str]
```

---

## 4. 忽略规则

默认忽略以下目录和文件：

```python
IGNORE_PATTERNS = [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".egg-info",
    ".tox",
    ".idea",
    ".vscode",
    "*.pyc",
    "*.so",
    "*.dll",
    "*.dylib",
]
```

---

## 5. 生成索引示例

```markdown
# Codebase Index

> Auto-generated index for `/path/to/project`

## Overview

- **Total files**: 203
- **Total lines**: 28,002
- **Languages**:
  - python: 150 files
  - javascript: 30 files
  - typescript: 15 files

## Key Files

### src/myagent

- `workspace/manager.py` (python) Workspace management
- `memory/manager.py` (python) Memory system
- `tasks/engine.py` (python) Task orchestration
```

---

## 6. 与参考项目的对比

| 维度 | MyAgent | Claude Code |
|------|---------|-------------|
| 扫描 | 自动递归 | 自动递归 |
| 索引文件 | `codebase-index.md` | 内置索引 |
| 语言支持 | 25+ | 30+ |
| Python AST | 支持 | 支持 |
| 语义搜索 | 关键词 + 评分 | 向量搜索 |
| 自然语言查询 | 支持 | 支持 |
| Web UI | 支持 | 无 |

---

## 7. 使用方式

### 7.1 Web UI

Settings → 代码库 标签页：
- 显示统计信息：文件数、行数、主要语言
- 搜索框输入关键词
- 点击结果跳转到文件预览

### 7.2 Python API

```python
from myagent.codebase.indexer import CodebaseIndexer
from myagent.codebase.search import CodebaseSearch

# 扫描代码库
indexer = CodebaseIndexer(".")
index = indexer.scan()
print(f"Files: {index.total_files}, Lines: {index.total_lines}")

# 搜索
searcher = CodebaseSearch(".")
results = searcher.search("TaskEngine", limit=10)
for r in results:
    print(f"{r.path}:{r.line_number} - {r.content}")

# 重建索引
indexer.save_index()
```
