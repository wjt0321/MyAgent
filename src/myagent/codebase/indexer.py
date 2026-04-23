"""Codebase indexer for auto-scanning and generating codebase-index.md."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CodeFile:
    """Represents a scanned code file."""
    path: str
    language: str
    description: str = ""
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    size: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "language": self.language,
            "description": self.description,
            "classes": self.classes,
            "functions": self.functions,
            "imports": self.imports[:10],  # Limit imports
            "size": self.size,
        }


@dataclass
class CodebaseIndex:
    """Complete codebase index."""
    root: str
    files: list[CodeFile] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)
    total_files: int = 0
    total_lines: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "files": [f.to_dict() for f in self.files],
            "languages": self.languages,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
        }


class CodebaseIndexer:
    """Scans a codebase and generates an index."""

    LANGUAGE_MAP: dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".sh": "shell",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
    }

    IGNORE_PATTERNS: list[str] = [
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

    def __init__(self, root_dir: str | Path) -> None:
        self.root = Path(root_dir).resolve()
        self.index = CodebaseIndex(root=str(self.root))

    def scan(self) -> CodebaseIndex:
        """Scan the codebase and build index."""
        self.index.files = []
        self.index.languages = {}
        self.index.total_files = 0
        self.index.total_lines = 0

        for file_path in self._iter_files():
            code_file = self._analyze_file(file_path)
            if code_file:
                self.index.files.append(code_file)
                self.index.total_files += 1
                self.index.total_lines += code_file.size

                # Count languages
                lang = code_file.language
                self.index.languages[lang] = self.index.languages.get(lang, 0) + 1

        # Sort files by path
        self.index.files.sort(key=lambda f: f.path)
        return self.index

    def generate_markdown(self) -> str:
        """Generate codebase-index.md content."""
        if not self.index.files:
            self.scan()

        lines = [
            "# Codebase Index",
            "",
            f"> Auto-generated index for `{self.index.root}`",
            "",
            "## Overview",
            "",
            f"- **Total files**: {self.index.total_files}",
            f"- **Total lines**: {self.index.total_lines:,}",
            "- **Languages**:",
        ]

        for lang, count in sorted(self.index.languages.items(), key=lambda x: -x[1]):
            lines.append(f"  - {lang}: {count} files")

        lines.extend(["", "## Key Files", ""])

        # Group by directory
        by_dir: dict[str, list[CodeFile]] = {}
        for f in self.index.files:
            dir_name = str(Path(f.path).parent)
            if dir_name == ".":
                dir_name = "root"
            by_dir.setdefault(dir_name, []).append(f)

        for dir_name, files in sorted(by_dir.items()):
            lines.append(f"### {dir_name}")
            lines.append("")
            for f in files:
                desc = f.description[:80] if f.description else ""
                classes = f", classes: {', '.join(f.classes[:3])}" if f.classes else ""
                funcs = f", functions: {', '.join(f.functions[:3])}" if f.functions else ""
                lines.append(f"- `{f.path}` ({f.language}){desc}{classes}{funcs}")
            lines.append("")

        return "\n".join(lines)

    def save_index(self, output_path: str | Path | None = None) -> Path:
        """Save the index to a file."""
        if output_path is None:
            output_path = self.root / "codebase-index.md"
        else:
            output_path = Path(output_path)

        content = self.generate_markdown()
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def _iter_files(self) -> Any:
        """Iterate over relevant files in the codebase."""
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue

            # Check ignore patterns
            rel_path = path.relative_to(self.root)
            if self._should_ignore(rel_path):
                continue

            # Check if it's a known code file
            if path.suffix.lower() in self.LANGUAGE_MAP:
                yield path

    def _should_ignore(self, rel_path: Path) -> bool:
        """Check if a path should be ignored."""
        path_str = str(rel_path)
        for pattern in self.IGNORE_PATTERNS:
            if pattern in path_str:
                return True
            if path_str.endswith(pattern.replace("*", "")):
                return True
        return False

    def _analyze_file(self, file_path: Path) -> CodeFile | None:
        """Analyze a single file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        rel_path = str(file_path.relative_to(self.root))
        language = self.LANGUAGE_MAP.get(file_path.suffix.lower(), "unknown")
        size = len(content.splitlines())

        code_file = CodeFile(
            path=rel_path,
            language=language,
            size=size,
        )

        # Extract description from docstring/comments
        code_file.description = self._extract_description(content, language)

        # Parse Python files for classes and functions
        if language == "python":
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        code_file.classes.append(node.name)
                    elif isinstance(node, ast.FunctionDef):
                        code_file.functions.append(node.name)
            except SyntaxError:
                pass

        # Extract imports for Python
        if language == "python":
            code_file.imports = self._extract_python_imports(content)

        return code_file

    def _extract_description(self, content: str, language: str) -> str:
        """Extract a brief description from file header."""
        lines = content.splitlines()[:20]

        # Look for module docstring (Python)
        if language == "python":
            # Check for triple-quoted docstring
            docstring_match = re.search(r'"""(.*?)"""', content[:500], re.DOTALL)
            if docstring_match:
                desc = docstring_match.group(1).strip().split("\n")[0]
                return desc[:100]

        # Look for comment header
        for line in lines:
            line = line.strip()
            if line.startswith("#") and not line.startswith("#!/"):
                return line.lstrip("# ").strip()[:100]
            if line.startswith("//"):
                return line.lstrip("// ").strip()[:100]
            if line.startswith("/*"):
                return line.lstrip("/* ").strip()[:100]

        return ""

    def _extract_python_imports(self, content: str) -> list[str]:
        """Extract import statements from Python code."""
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    imports.append(module)
        except SyntaxError:
            pass
        return imports
