"""AgentTool for MyAgent - invoke sub-agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from myagent.agents.definitions import AgentDefinition
from myagent.agents.loader import AgentLoader
from myagent.engine.query_engine import QueryEngine
from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult
from myagent.tools.registry import ToolRegistry


class AgentToolInput(BaseModel):
    agent: str = Field(description="Name of the agent to invoke")
    task: str = Field(description="Task description for the sub-agent")
    model: str | None = Field(
        default=None,
        description="Optional override for the LLM model to use",
    )
    max_turns: int | None = Field(
        default=None,
        description="Optional override for max turns",
    )


class AgentTool(BaseTool):
    name = "AgentTool"
    description = (
        "Invoke another specialized agent to complete a sub-task. "
        "The sub-agent will run independently and return its result. "
        "Use this to delegate work to agents with specific expertise."
    )
    input_model = AgentToolInput

    def __init__(self, llm_client: Any | None = None) -> None:
        self.llm_client = llm_client

    async def execute(
        self, arguments: AgentToolInput, context: ToolExecutionContext
    ) -> ToolResult:
        loader = AgentLoader()
        agents = loader.load_builtin_agents()
        agents.update(loader.load_all())

        agent_def = agents.get(arguments.agent)
        if agent_def is None:
            return ToolResult(
                output=f"Error: Agent '{arguments.agent}' not found. "
                f"Available agents: {', '.join(agents.keys()) or 'none'}",
                is_error=True,
            )

        try:
            tool_registry = self._build_tool_registry(agent_def)
            engine = QueryEngine(
                tool_registry=tool_registry,
                system_prompt=agent_def.system_prompt or "You are a helpful assistant.",
                max_turns=arguments.max_turns or agent_def.max_turns or 20,
                llm_client=self.llm_client,
            )

            output_parts: list[str] = []
            async for event in engine.submit_message(arguments.task):
                if hasattr(event, "text"):
                    output_parts.append(event.text)

            result_text = "".join(output_parts) or "Agent completed with no output."
            return ToolResult(output=result_text)

        except Exception as e:
            return ToolResult(
                output=f"Error invoking agent '{arguments.agent}': {e}",
                is_error=True,
            )

    def _build_tool_registry(self, agent_def: AgentDefinition) -> ToolRegistry:
        registry = ToolRegistry()

        from myagent.tools.bash import Bash
        from myagent.tools.edit import Edit
        from myagent.tools.glob import Glob
        from myagent.tools.grep import Grep
        from myagent.tools.read import Read
        from myagent.tools.web_fetch import WebFetch
        from myagent.tools.web_search import WebSearch
        from myagent.tools.write import Write

        all_tools: list[BaseTool] = [
            Read(),
            Write(),
            Edit(),
            Bash(),
            Glob(),
            Grep(),
            WebFetch(),
            WebSearch(),
        ]

        allowed = agent_def.tools
        disallowed = agent_def.disallowed_tools or []

        for tool in all_tools:
            if allowed is not None and tool.name not in allowed:
                continue
            if tool.name in disallowed:
                continue
            registry.register(tool)

        return registry
