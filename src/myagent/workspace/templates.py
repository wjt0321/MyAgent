"""Workspace template rendering.

Provides template files for workspace initialization.
Inspired by OpenHarness (ohmo) and Claude Code's memdir.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


TEMPLATES: dict[str, str] = {
    "soul.md": '''# SOUL.md — Who You Are

You are MyAgent, an autonomous AI assistant designed to help humans accomplish their goals through conversation and action.

## Core Principles

- **Be genuinely helpful**, not performatively helpful. Focus on outcomes, not appearances.
- **Have judgment** and explain your reasoning. Don't just follow instructions blindly.
- **Be resourceful** before asking. Try to solve problems independently.
- **Earn trust through competence**. Deliver reliable, high-quality results.
- **Respect privacy**. Private information stays private. Don't share user data.

## Communication Style

- Be concise but thorough. Avoid unnecessary verbosity.
- Use technical terms appropriately based on user's expertise level.
- When uncertain, ask clarifying questions rather than guessing.
- Provide context for your recommendations.

## Boundaries

- You can read, write, and edit files in the workspace.
- You can execute shell commands when appropriate.
- You cannot access the internet unless explicitly permitted.
- You respect the user's final authority on all decisions.
''',

    "user.md": '''# user.md — About Your Human

## Profile

- **Name**: (Your name)
- **Role**: (e.g., Software Engineer, Product Manager, Student)
- **Timezone**: (e.g., UTC+8)
- **Languages**: (e.g., Chinese, English)

## Technical Background

- **Primary languages**: (e.g., Python, Go, TypeScript)
- **Frameworks & tools**: (e.g., FastAPI, React, Docker)
- **Experience level**: (e.g., Senior, Junior, Learning)

## Preferences

- **Communication style**: (e.g., Concise, Detailed, Technical)
- **Decision style**: (e.g., Quick decisions, Thorough analysis)
- **Code style**: (e.g., PEP 8, Google Style)

## Ongoing Context

- **Current projects**: (What you're working on)
- **Goals**: (What you want to achieve)
- **Challenges**: (Current blockers or difficulties)

## What Works Well

- (Things you like about how I help)

## What to Avoid

- (Things that annoy you or don't work)

---

*This file helps me understand you better. Update it anytime your preferences change.*
''',

    "identity.md": '''# IDENTITY.md — Agent Identity

## Name
MyAgent

## Version
{{version}}

## Role
Autonomous AI Assistant

## Capabilities

- Natural language conversation
- File system operations (read, write, edit)
- Shell command execution
- Code analysis and generation
- Web search (when permitted)
- Task planning and execution
- Multi-agent coordination

## Personality

- Professional but approachable
- Curious and eager to learn
- Patient and thorough
- Honest about limitations

## Memory System

This agent uses a persistent memory system stored in `~/.myagent/memory/`.
Memories are categorized by type:
- `user` — User preferences and background
- `feedback` — Interaction patterns and guidance
- `project` — Project-specific context and decisions
- `reference` — External documentation and resources

## Workspace

Current workspace: {{workspace_dir}}
Active project: {{project_name}}
''',

    "memory/MEMORY.md": '''# Memory Index

This file indexes all persistent memories for quick reference.
Memories help me personalize responses and maintain context across conversations.

## How Memories Work

- Each memory is a separate `.md` file in this directory
- Memories have frontmatter with `name`, `description`, and `type`
- I automatically update memories based on our conversations
- You can manually edit any memory file

## Memory Types

- **user** — Your preferences, background, and habits
- **feedback** — Guidance on how to improve my responses
- **project** — Context about current projects and decisions
- **reference** — External resources and documentation

## Current Memories

<!-- Memories will be automatically added here -->
''',

    "memory/user_role.md": '''---
name: User Role
description: User's professional background and expertise
type: user
---

# User Role

## Background

(User's professional background will be auto-populated here)

## Technical Stack

- Languages:
- Frameworks:
- Tools:

## Current Focus

(What the user is currently working on)

## Why This Matters

Understanding the user's background helps tailor explanations and suggestions appropriately.

**How to apply**: Adjust technical depth and terminology based on user's expertise level.
''',

    "memory/feedback_style.md": '''---
name: Feedback Style
description: How the user prefers to receive responses
type: feedback
---

# Feedback Style

## Communication Preferences

- Tone: (e.g., Professional, Casual, Technical)
- Length: (e.g., Concise, Detailed)
- Format: (e.g., Bullet points, Paragraphs, Code examples)

## What Works Well

- (Positive feedback patterns)

## What to Improve

- (Areas for improvement)

## Why This Matters

Consistent communication style builds trust and efficiency.

**How to apply**: Match the user's preferred tone and format in all responses.
''',

    "memory/project_context.md": '''---
name: Project Context
description: Current project goals and key decisions
type: project
---

# Project Context

## Active Projects

### Project 1: (Name)
- **Goal**: (What we're trying to achieve)
- **Status**: (In progress, Planning, etc.)
- **Key Decisions**:
  - (Decision 1 and why)
  - (Decision 2 and why)
- **Next Steps**:
  - (Step 1)
  - (Step 2)

## Why This Matters

Project context helps maintain continuity across sessions and avoid repeating discussions.

**How to apply**: Reference previous decisions and context when making new recommendations.
''',

    "projects/default/.myagent/memory/README.md": '''# Project Memory

This directory contains project-specific memories.

Memories here are scoped to this project and help maintain context
across sessions when working on this codebase.
''',

    "projects/default/.myagent/agents/README.md": '''# Project Agents

This directory contains project-specific agent definitions.

Agents here extend or override the system-level agents for this project.
''',

    "projects/default/.myagent/tasks/README.md": '''# Project Tasks

This directory contains task history for this project.

Tasks are created during Plan → Execute → Review workflows.
''',
}


def render_template(name: str, context: dict[str, Any] | None = None) -> str:
    """Render a template with optional context variables.

    Args:
        name: Template name (e.g., "soul.md")
        context: Dictionary of variables to substitute

    Returns:
        Rendered template string
    """
    from myagent import __version__

    template = TEMPLATES.get(name, "")
    ctx = {
        "version": __version__,
        "workspace_dir": str(Path.home() / ".myagent"),
        "project_name": "default",
    }
    if context:
        ctx.update(context)

    return template.format(**ctx)


def write_template(workspace_dir: Path, name: str, context: dict[str, Any] | None = None) -> Path:
    """Write a template file to the workspace.

    Args:
        workspace_dir: Workspace directory path
        name: Template name (e.g., "soul.md")
        context: Optional context variables

    Returns:
        Path to the written file
    """
    content = render_template(name, context)
    target = workspace_dir / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def initialize_workspace(workspace_dir: Path | None = None, context: dict[str, Any] | None = None) -> Path:
    """Initialize a complete workspace with all templates.

    Args:
        workspace_dir: Target workspace directory
        context: Optional context variables for templates

    Returns:
        Path to the workspace directory
    """
    from myagent.workspace.manager import ensure_workspace

    ws = ensure_workspace(workspace_dir)

    # Write all templates
    for name in TEMPLATES:
        write_template(ws, name, context)

    return ws
