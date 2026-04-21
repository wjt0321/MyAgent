"""Live integration test for ZhipuAI API.

Run with: ZHIPU_API_KEY=your-key python -m pytest tests/test_zhipu_live.py -v
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from myagent.llm.providers.zhipu import ZhipuProvider
from myagent.llm.types import DoneChunk, TextChunk


@pytest.fixture
def api_key():
    key = os.environ.get("ZHIPU_API_KEY")
    if not key:
        pytest.skip("ZHIPU_API_KEY not set")
    return key


@pytest.fixture
def provider(api_key):
    return ZhipuProvider(
        api_key=api_key,
        model="glm-4.7",
        base_url="https://open.bigmodel.cn/api/anthropic",
    )


class TestZhipuProviderLive:
    @pytest.mark.asyncio
    async def test_stream_messages(self, provider):
        from myagent.engine.messages import ConversationMessage, TextBlock

        messages = [
            ConversationMessage(
                role="user",
                content=[TextBlock(text="Hello, who are you?")],
            )
        ]

        chunks = []
        async for chunk in provider.stream_messages(messages):
            chunks.append(chunk)

        assert len(chunks) > 0
        text_parts = [c.text for c in chunks if isinstance(c, TextChunk)]
        assert len(text_parts) > 0
        full_text = "".join(text_parts)
        assert len(full_text) > 0
        print(f"Response: {full_text[:200]}...")

    @pytest.mark.asyncio
    async def test_complete(self, provider):
        from myagent.engine.messages import ConversationMessage, TextBlock

        messages = [
            ConversationMessage(
                role="user",
                content=[TextBlock(text="Say 'Hello from Zhipu' and nothing else.")],
            )
        ]

        result = await provider.complete(messages)
        assert len(result) > 0
        print(f"Complete response: {result}")


class TestZhipuProviderConfig:
    def test_provider_creation_with_custom_url(self):
        provider = ZhipuProvider(
            api_key="test-key",
            model="glm-4.7",
            base_url="https://open.bigmodel.cn/api/anthropic",
        )
        assert provider.name == "zhipu"
        assert provider.model == "glm-4.7"
        assert provider.base_url == "https://open.bigmodel.cn/api/anthropic"

    def test_provider_default_url(self):
        provider = ZhipuProvider(api_key="test-key")
        assert provider.base_url == "https://open.bigmodel.cn/api/paas/v4"

    def test_provider_new_models(self):
        provider = ZhipuProvider(api_key="test-key", model="glm-5.1")
        assert provider.model == "glm-5.1"

        provider = ZhipuProvider(api_key="test-key", model="glm-5-Turbo")
        assert provider.model == "glm-5-Turbo"
