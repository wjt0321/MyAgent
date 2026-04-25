"""Task engine for Plan -> Execute -> Review workflow."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

from myagent.engine.query_engine import QueryEngine
from myagent.engine.stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ErrorEvent,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from myagent.tasks.models import SubTask, Task, TaskResult, TaskStatus
from myagent.web.engine_manager import WebEngineManager


PLAN_PROMPT = """You are a task planning expert. Analyze the user's request and create a detailed execution plan.

Your output must be a JSON object with this structure:
{{
  "title": "Short task title",
  "subtasks": [
    {{
      "description": "What this step does",
      "agent": "worker"  // or "explore" for read-only steps
    }}
  ]
}}

Guidelines:
- Break complex tasks into 3-10 clear, actionable steps
- Each step should be independent and verifiable
- Use "explore" agent for investigation steps (read-only)
- Use "worker" agent for implementation steps
- Consider dependencies between steps
- Include verification/testing steps where appropriate

User request: {request}
"""

REVIEW_PROMPT = """You are a code review and quality assurance expert. Review the execution results and provide feedback.

Your output must be a JSON object:
{{
  "success": true/false,
  "summary": "Brief summary of what was accomplished",
  "deliverables": ["list of files changed or created"],
  "issues": ["any issues found"],
  "suggestions": ["improvement suggestions"]
}}

Review criteria:
- Were all subtasks completed successfully?
- Is the code quality acceptable?
- Are there any bugs or edge cases missed?
- Could the implementation be improved?
- Are tests included where needed?

Task: {task_description}

Subtask results:
{subtask_results}
"""


class TaskEngine:
    """Orchestrates Plan -> Execute -> Review workflow."""

    def __init__(self, engine_manager: WebEngineManager) -> None:
        self.engine_manager = engine_manager
        self._current_task: Task | None = None
        self._last_task_snapshot: Task | None = None

    def set_current_task(self, task: Task | None) -> None:
        """Set current task and keep the latest snapshot for restore."""
        self._current_task = task
        if task is not None:
            self._last_task_snapshot = task

    async def create_plan(self, request: str) -> Task:
        """Create a plan for a user request.

        Returns a Task with status PLANNED, containing subtasks.
        """
        task = Task(
            title=request[:80] + "..." if len(request) > 80 else request,
            description=request,
            status=TaskStatus.PLANNING,
        )
        self.set_current_task(task)

        if not self.engine_manager.is_configured():
            task.update_status(TaskStatus.FAILED)
            return task

        engine = self.engine_manager.create_engine("plan")
        if engine is None:
            task.update_status(TaskStatus.FAILED)
            return task

        # Generate plan using LLM
        prompt = PLAN_PROMPT.format(request=request)
        plan_text = ""

        async for event in engine.submit_message(prompt):
            if isinstance(event, AssistantTextDelta):
                plan_text += event.text

        # Parse plan JSON
        try:
            plan_data = self._extract_json(plan_text)
            task.title = plan_data.get("title", task.title)
            for subtask_data in plan_data.get("subtasks", []):
                subtask = SubTask(
                    description=subtask_data["description"],
                    agent=subtask_data.get("agent", "worker"),
                )
                task.subtasks.append(subtask)
            task.update_status(TaskStatus.PLANNED)
        except Exception:
            # Fallback: create a single subtask with the original request
            task.subtasks.append(SubTask(
                description=request,
                agent="worker",
            ))
            task.update_status(TaskStatus.PLANNED)

        return task

    async def execute_task(self, task: Task) -> AsyncIterator[dict[str, Any]]:
        """Execute all subtasks in a task.

        Yields progress updates as dicts with keys:
        - type: "subtask_start" | "subtask_progress" | "subtask_complete" | "error"
        - subtask_id: str
        - message: str
        """
        task.update_status(TaskStatus.EXECUTING)

        for subtask in task.subtasks:
            if task.status == TaskStatus.CANCELLED:
                break

            subtask.status = TaskStatus.EXECUTING
            subtask.started_at = datetime.now()

            yield {
                "type": "subtask_start",
                "subtask_id": subtask.id,
                "message": f"开始执行: {subtask.description}",
            }

            engine = self.engine_manager.create_engine(subtask.agent)
            if engine is None:
                subtask.status = TaskStatus.FAILED
                subtask.error = "Failed to create engine"
                yield {
                    "type": "subtask_complete",
                    "subtask_id": subtask.id,
                    "message": f"失败: {subtask.error}",
                }
                continue

            # Execute subtask
            result_text = ""
            try:
                async for event in engine.submit_message(subtask.description):
                    if isinstance(event, AssistantTextDelta):
                        result_text += event.text
                        yield {
                            "type": "subtask_progress",
                            "subtask_id": subtask.id,
                            "message": event.text,
                        }
                    elif isinstance(event, ToolExecutionStarted):
                        yield {
                            "type": "subtask_progress",
                            "subtask_id": subtask.id,
                            "message": f"使用工具: {event.tool_name}",
                        }
                    elif isinstance(event, ToolExecutionCompleted):
                        yield {
                            "type": "subtask_progress",
                            "subtask_id": subtask.id,
                            "message": f"工具结果: {event.result[:200]}",
                        }
                    elif isinstance(event, ErrorEvent):
                        subtask.error = str(event.error)

                subtask.result = result_text
                subtask.status = TaskStatus.DONE if not subtask.error else TaskStatus.FAILED
                subtask.completed_at = datetime.now()

                yield {
                    "type": "subtask_complete",
                    "subtask_id": subtask.id,
                    "message": "完成" if not subtask.error else f"失败: {subtask.error}",
                }

            except Exception as e:
                subtask.status = TaskStatus.FAILED
                subtask.error = str(e)
                subtask.completed_at = datetime.now()
                yield {
                    "type": "subtask_complete",
                    "subtask_id": subtask.id,
                    "message": f"失败: {e}",
                }

        task.update_status(TaskStatus.EXECUTED)

    async def review_task(self, task: Task) -> TaskResult:
        """Review the execution results of a task.

        Returns a TaskResult with review findings.
        """
        task.update_status(TaskStatus.REVIEWING)
        task.add_event("review_start", "开始审查任务结果", status=task.status.value)

        if not self.engine_manager.is_configured():
            result = TaskResult(
                success=False,
                summary="Review failed: LLM not configured",
            )
            task.result = result
            task.update_status(TaskStatus.FAILED)
            return result

        engine = self.engine_manager.create_engine("plan")
        if engine is None:
            result = TaskResult(
                success=False,
                summary="Review failed: Could not create review engine",
            )
            task.result = result
            task.update_status(TaskStatus.FAILED)
            return result

        # Build subtask results summary
        subtask_results = []
        for subtask in task.subtasks:
            status = "成功" if subtask.status == TaskStatus.DONE else "失败"
            subtask_results.append(
                f"[{status}] {subtask.description}\n结果: {subtask.result[:500]}"
            )

        prompt = REVIEW_PROMPT.format(
            task_description=task.description,
            subtask_results="\n\n".join(subtask_results),
        )

        review_text = ""
        async for event in engine.submit_message(prompt):
            if isinstance(event, AssistantTextDelta):
                review_text += event.text

        # Parse review JSON
        try:
            review_data = self._extract_json(review_text)
            result = TaskResult(
                success=review_data.get("success", False),
                summary=review_data.get("summary", ""),
                deliverables=review_data.get("deliverables", []),
                issues=review_data.get("issues", []),
                suggestions=review_data.get("suggestions", []),
            )
        except Exception:
            result = TaskResult(
                success=all(s.status == TaskStatus.DONE for s in task.subtasks),
                summary="Review completed (parsing fallback)",
                deliverables=[],
                issues=[],
                suggestions=[],
            )

        task.result = result
        task.review_passed = result.success

        if result.success:
            task.update_status(TaskStatus.DONE)
        else:
            task.update_status(TaskStatus.FAILED)
        task.add_event(
            "review_complete",
            result.summary or "审查完成",
            status=task.status.value,
        )

        return result

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from LLM response text."""
        text = text.strip()

        # Try to find JSON block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()

        return json.loads(text)

    def get_current_task(self) -> Task | None:
        """Get the currently active task."""
        return self._current_task

    def get_restore_candidate(self) -> Task | None:
        """Get the latest task snapshot that can be restored into the workbench."""
        return self._current_task or self._last_task_snapshot

    def restore_last_task(self) -> Task | None:
        """Restore the latest known task snapshot as the current task."""
        if self._last_task_snapshot is None:
            return None
        self._current_task = self._last_task_snapshot
        return self._current_task
