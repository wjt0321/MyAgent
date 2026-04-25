"""Team orchestrator for multi-agent collaboration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, AsyncIterator

from myagent.tasks.engine import TaskEngine
from myagent.tasks.models import SubTask, Task, TaskStatus
from myagent.teams.models import Team, TeamMember, TeamRole


class TeamOrchestrator:
    """Orchestrates multi-agent team collaboration.

    Assigns subtasks to appropriate team members based on their roles,
    tracks execution progress, and coordinates handoffs between agents.
    """

    ROLE_AGENT_MAP: dict[TeamRole, str] = {
        TeamRole.PLANNER: "plan",
        TeamRole.EXPLORER: "explore",
        TeamRole.EXECUTOR: "worker",
        TeamRole.REVIEWER: "reviewer",
        TeamRole.SPECIALIST: "worker",
    }

    def __init__(self, task_engine: TaskEngine) -> None:
        self.task_engine = task_engine
        self.team = Team.create_default_team()

    def assign_subtask(self, subtask: SubTask) -> TeamMember | None:
        """Assign a subtask to the most appropriate team member.

        Args:
            subtask: The subtask to assign

        Returns:
            The assigned team member, or None if no suitable member found
        """
        # Map subtask agent to team role
        role = self._agent_to_role(subtask.agent)

        # Try to find an idle member with matching role
        member = self.team.get_available_member(role)
        if member:
            subtask.agent = member.name
            self.team.update_member_status(
                member.name, "busy", subtask.description[:50]
            )
            return member

        # Fallback: any idle member
        member = self.team.get_available_member()
        if member:
            subtask.agent = member.name
            self.team.update_member_status(
                member.name, "busy", subtask.description[:50]
            )
            return member

        return None

    def release_member(self, member_name: str, success: bool = True) -> None:
        """Release a team member after task completion.

        Args:
            member_name: Name of the member to release
            success: Whether the task was completed successfully
        """
        member = self.team.get_member(member_name)
        if member:
            if success:
                member.completed_tasks += 1
            else:
                member.failed_tasks += 1
            self.team.update_member_status(member_name, "idle", None)

    async def execute_with_team(
        self,
        task: Task,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute a task using the full team.

        Each subtask is assigned to the most appropriate team member.
        Yields progress updates with team member information.

        Args:
            task: The task to execute

        Yields:
            Dicts with progress updates including:
            - type: "team_start" | "member_assigned" | "member_progress" |
                    "member_complete" | "team_complete" | "error"
            - member: TeamMember dict
            - subtask: SubTask dict
        """
        task.update_status(TaskStatus.EXECUTING)

        yield {
            "type": "team_start",
            "team": self.team.to_dict(),
            "task": task.to_dict(),
        }

        for subtask in task.subtasks:
            if task.status == TaskStatus.CANCELLED:
                break

            # Assign to team member
            member = self.assign_subtask(subtask)
            if member is None:
                # Wait for a member to become available
                yield {
                    "type": "waiting",
                    "message": "等待可用团队成员...",
                }
                # Simple retry: try again
                member = self.assign_subtask(subtask)
                if member is None:
                    subtask.status = TaskStatus.FAILED
                    subtask.error = "No available team members"
                    continue

            subtask.status = TaskStatus.EXECUTING
            subtask.started_at = datetime.now()

            yield {
                "type": "member_assigned",
                "member": member.to_dict(),
                "subtask": subtask.to_dict(),
            }

            # Execute using task engine
            engine = self.task_engine.engine_manager.create_engine(member.name)
            if engine is None:
                subtask.status = TaskStatus.FAILED
                subtask.error = "Failed to create engine"
                self.release_member(member.name, success=False)
                yield {
                    "type": "member_complete",
                    "member": member.to_dict(),
                    "subtask": subtask.to_dict(),
                    "success": False,
                }
                continue

            # Execute subtask
            result_text = ""
            try:
                from myagent.engine.stream_events import (
                    AssistantTextDelta,
                    ToolExecutionCompleted,
                    ToolExecutionStarted,
                    ErrorEvent,
                )

                async for event in engine.submit_message(subtask.description):
                    if isinstance(event, AssistantTextDelta):
                        result_text += event.text
                        yield {
                            "type": "member_progress",
                            "member": member.to_dict(),
                            "subtask": subtask.to_dict(),
                            "delta": event.text,
                        }
                    elif isinstance(event, ToolExecutionStarted):
                        yield {
                            "type": "member_progress",
                            "member": member.to_dict(),
                            "subtask": subtask.to_dict(),
                            "message": f"使用工具: {event.tool_name}",
                        }
                    elif isinstance(event, ToolExecutionCompleted):
                        yield {
                            "type": "member_progress",
                            "member": member.to_dict(),
                            "subtask": subtask.to_dict(),
                            "message": f"工具完成: {event.result[:100]}",
                        }
                    elif isinstance(event, ErrorEvent):
                        subtask.error = str(event.error)

                subtask.result = result_text
                success = not subtask.error
                subtask.status = TaskStatus.DONE if success else TaskStatus.FAILED
                subtask.completed_at = datetime.now()

                self.release_member(member.name, success=success)

                yield {
                    "type": "member_complete",
                    "member": member.to_dict(),
                    "subtask": subtask.to_dict(),
                    "success": success,
                }

            except Exception as e:
                subtask.status = TaskStatus.FAILED
                subtask.error = str(e)
                subtask.completed_at = datetime.now()
                self.release_member(member.name, success=False)

                yield {
                    "type": "member_complete",
                    "member": member.to_dict(),
                    "subtask": subtask.to_dict(),
                    "success": False,
                }

        task.update_status(TaskStatus.EXECUTED)

        yield {
            "type": "team_complete",
            "task": task.to_dict(),
            "team": self.team.to_dict(),
        }

    def _agent_to_role(self, agent_name: str) -> TeamRole:
        """Map agent name to team role."""
        role_map = {
            "plan": TeamRole.PLANNER,
            "explore": TeamRole.EXPLORER,
            "worker": TeamRole.EXECUTOR,
            "reviewer": TeamRole.REVIEWER,
        }
        return role_map.get(agent_name, TeamRole.EXECUTOR)

    def get_team_status(self) -> dict[str, Any]:
        """Get current team status overview."""
        return {
            "team": self.team.to_dict(),
            "total_members": len(self.team.members),
            "busy_members": sum(1 for m in self.team.members if m.status == "busy"),
            "idle_members": sum(1 for m in self.team.members if m.status == "idle"),
            "total_completed": sum(m.completed_tasks for m in self.team.members),
            "total_failed": sum(m.failed_tasks for m in self.team.members),
        }
