"""Azure OpenAI provider for MyAgent.

Uses Azure OpenAI Service API.
"""

from __future__ import annotations

from typing import Any

from myagent.llm.providers.openai import OpenAIProvider


class AzureProvider(OpenAIProvider):
    """Provider for Azure OpenAI Service.

    Supports models deployed on Azure:
    - gpt-4o
    - gpt-4
    - gpt-35-turbo
    """

    name = "azure"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        # Azure requires the full deployment URL
        # e.g., https://your-resource.openai.azure.com/openai/deployments/your-deployment
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            **kwargs,
        )
