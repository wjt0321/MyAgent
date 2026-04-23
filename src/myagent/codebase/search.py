"""Codebase search for semantic and keyword-based code retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from myagent.codebase.indexer import CodebaseIndexer


@dataclass
class SearchResult:
    """A single search result."""
    path: str
    language: str
    content: str
    line_number: int
    score: float
    context_before: list[str] = None
    context_after: list[str] = None

    def __post_init__(self):
        if self.context_before is None:
            self.context_before = []
        if self.context_after is None:
            self.context_after = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "language": self.language,
            "content": self.content,
            "line_number": self.line_number,
            "score": self.score,
            "context": {
                "before": self.context_before,
                "line": self.content,
                "after": self.context_after,
            },
        }


class CodebaseSearch:
    """Search codebase using keyword and simple semantic matching."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root = Path(root_dir).resolve()
        self.indexer = CodebaseIndexer(self.root)
        self._file_cache: dict[str, list[str]] = {}

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search codebase for matching content.

        Args:
            query: Search query (keywords or natural language)
            limit: Maximum number of results

        Returns:
            List of search results sorted by relevance
        """
        results = []
        keywords = self._extract_keywords(query)

        for file_path in self.indexer._iter_files():
            rel_path = str(file_path.relative_to(self.root))
            lines = self._get_file_lines(file_path)
            language = self.indexer.LANGUAGE_MAP.get(file_path.suffix.lower(), "unknown")

            for i, line in enumerate(lines):
                score = self._score_line(line, keywords)
                if score > 0:
                    context_before = lines[max(0, i - 2):i]
                    context_after = lines[i + 1:min(len(lines), i + 3)]

                    results.append(SearchResult(
                        path=rel_path,
                        language=language,
                        content=line.strip(),
                        line_number=i + 1,
                        score=score,
                        context_before=[l.strip() for l in context_before],
                        context_after=[l.strip() for l in context_after],
                    ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def find_definition(self, symbol: str) -> list[SearchResult]:
        """Find where a symbol (class/function/variable) is defined.

        Args:
            symbol: Name of the symbol to find

        Returns:
            List of definition locations
        """
        results = []
        patterns = [
            rf"^\s*(class|def|function|const|let|var)\s+{re.escape(symbol)}\b",
            rf"^\s*{re.escape(symbol)}\s*[=:]",
        ]

        for file_path in self.indexer._iter_files():
            rel_path = str(file_path.relative_to(self.root))
            lines = self._get_file_lines(file_path)
            language = self.indexer.LANGUAGE_MAP.get(file_path.suffix.lower(), "unknown")

            for i, line in enumerate(lines):
                for pattern in patterns:
                    if re.search(pattern, line):
                        results.append(SearchResult(
                            path=rel_path,
                            language=language,
                            content=line.strip(),
                            line_number=i + 1,
                            score=1.0,
                        ))

        return results

    def get_file_content(self, path: str) -> str | None:
        """Get the full content of a file.

        Args:
            path: Relative path to the file

        Returns:
            File content or None if not found
        """
        file_path = self.root / path
        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

    def get_related_files(self, path: str) -> list[str]:
        """Find files related to a given file (same directory, imports).

        Args:
            path: Relative path to the file

        Returns:
            List of related file paths
        """
        file_path = self.root / path
        if not file_path.exists():
            return []

        related = []
        target_dir = file_path.parent

        # Same directory files
        for sibling in target_dir.iterdir():
            if sibling.is_file() and sibling != file_path:
                rel = str(sibling.relative_to(self.root))
                if rel not in related:
                    related.append(rel)

        # Files that import this file (for Python)
        if file_path.suffix == ".py":
            module_name = file_path.stem
            for other_path in self.indexer._iter_files():
                if other_path.suffix != ".py":
                    continue
                try:
                    content = other_path.read_text(encoding="utf-8", errors="ignore")
                    if re.search(rf"(from\s+\S+\s+import\s+{module_name}|import\s+{module_name})", content):
                        rel = str(other_path.relative_to(self.root))
                        if rel not in related:
                            related.append(rel)
                except Exception:
                    pass

        return related

    def _get_file_lines(self, file_path: Path) -> list[str]:
        """Get lines of a file with caching."""
        cache_key = str(file_path)
        if cache_key not in self._file_cache:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                self._file_cache[cache_key] = content.splitlines()
            except Exception:
                self._file_cache[cache_key] = []
        return self._file_cache[cache_key]

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract keywords from a query."""
        # Remove common stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                      "being", "have", "has", "had", "do", "does", "did", "will",
                      "would", "could", "should", "may", "might", "must", "shall",
                      "can", "need", "dare", "ought", "used", "to", "of", "in",
                      "for", "on", "with", "at", "by", "from", "as", "into",
                      "through", "during", "before", "after", "above", "below",
                      "between", "under", "and", "but", "or", "yet", "so", "if",
                      "because", "although", "though", "while", "where", "when",
                      "that", "which", "who", "whom", "whose", "what", "this",
                      "these", "those", "i", "me", "my", "myself", "we", "our",
                      "you", "your", "he", "him", "his", "she", "her", "it",
                      "its", "they", "them", "their", "how", "find", "search",
                      "look", "get", "show", "display", "code", "file", "function",
                      "class", "method", "variable"}

        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', query.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _score_line(self, line: str, keywords: list[str]) -> float:
        """Score how well a line matches keywords."""
        line_lower = line.lower()
        score = 0.0

        for keyword in keywords:
            if keyword in line_lower:
                # Higher score for definition lines
                if any(line_lower.strip().startswith(prefix) for prefix in
                       ["class ", "def ", "function ", "const ", "let ", "var "]):
                    score += 3.0
                # Higher score for comments/docstrings
                elif any(c in line for c in ["#", "//", "/*", "*", '"""']):
                    score += 2.0
                else:
                    score += 1.0

        # Normalize by keyword count
        if keywords:
            score = score / len(keywords)

        return score
