"""MyAgent Gateway module for multi-platform integration.

Supports: Telegram, Discord, Slack, Feishu (Lark), Weixin (WeChat), QQ
"""

from myagent.gateway.adapter_base import BasePlatformAdapter
from myagent.gateway.base import (
    GatewayMessage,
    MessageEvent,
    MessageHandler,
    MessageType,
    Platform,
    ProcessingOutcome,
    SendResult,
    SessionSource,
    extract_images,
    is_retryable_error,
    strip_markdown,
    truncate_message,
)
from myagent.gateway.bot import GatewayBot
from myagent.gateway.config import (
    GatewayConfig,
    HomeChannel,
    PlatformConfig,
    SessionResetPolicy,
    StreamingConfig,
    load_gateway_config,
)
from myagent.gateway.helpers import (
    MessageDeduplicator,
    TextBatchAggregator,
    ThreadParticipationTracker,
)
from myagent.gateway.manager import GatewayManager

__all__ = [
    "BasePlatformAdapter",
    "GatewayBot",
    "GatewayConfig",
    "GatewayManager",
    "GatewayMessage",
    "HomeChannel",
    "MessageDeduplicator",
    "MessageEvent",
    "MessageHandler",
    "MessageType",
    "Platform",
    "PlatformConfig",
    "ProcessingOutcome",
    "SendResult",
    "SessionResetPolicy",
    "SessionSource",
    "StreamingConfig",
    "TextBatchAggregator",
    "ThreadParticipationTracker",
    "extract_images",
    "is_retryable_error",
    "load_gateway_config",
    "strip_markdown",
    "truncate_message",
]
