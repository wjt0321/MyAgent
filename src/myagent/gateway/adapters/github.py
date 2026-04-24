"""GitHub App adapter for MyAgent.

Handles webhook events from GitHub (PR, Issue, Review) and
posts automated analysis comments.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional

from myagent.gateway.adapter_base import BasePlatformAdapter
from myagent.gateway.base import (
    MessageEvent,
    MessageType,
    Platform,
    SendResult,
)
from myagent.gateway.config import PlatformConfig

logger = logging.getLogger(__name__)

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None  # type: ignore[assignment]
    AIOHTTP_AVAILABLE = False

GITHUB_API_BASE = "https://api.github.com"


class GitHubAdapter(BasePlatformAdapter):
    """GitHub App platform adapter for webhook events."""

    name = "GitHub"

    # Events we handle
    SUPPORTED_EVENTS = [
        "pull_request",
        "pull_request_review",
        "issues",
        "issue_comment",
        "push",
    ]

    def __init__(self, config: PlatformConfig) -> None:
        super().__init__(config, Platform.WEBHOOK)
        self.app_id = config.extra.get("app_id") or ""
        self.private_key = config.extra.get("private_key") or ""
        self.webhook_secret = config.extra.get("webhook_secret") or ""
        self.token = config.token or ""  # Personal access token fallback
        self._session: Any = None

    @property
    def _headers(self) -> Dict[str, str]:
        """HTTP headers for GitHub API requests."""
        token = self.token
        if not token and self.app_id:
            # TODO: Implement JWT-based GitHub App authentication
            token = self._get_app_token()
        return {
            "Authorization": f"Bearer {token}" if token else "",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MyAgent-GitHub-Adapter/0.1",
        }

    def _get_app_token(self) -> str:
        """Get installation token for GitHub App (placeholder)."""
        # Full implementation requires PyJWT and private key signing
        logger.warning("GitHub App JWT auth not fully implemented, using token fallback")
        return self.token

    async def connect(self) -> bool:
        """GitHub adapter doesn't maintain a persistent connection."""
        if not AIOHTTP_AVAILABLE:
            logger.error("[%s] aiohttp not installed. Run: pip install aiohttp", self.name)
            return False
        if not self.token and not self.app_id:
            logger.error("[%s] GITHUB_TOKEN or GITHUB_APP_ID required", self.name)
            return False

        self._session = aiohttp.ClientSession()
        self._running = True
        logger.info("[%s] Ready for webhook events", self.name)
        return True

    async def disconnect(self) -> None:
        self._running = False
        if self._session:
            await self._session.close()
        logger.info("[%s] Disconnected", self.name)

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature."""
        if not self.webhook_secret:
            logger.warning("[%s] No webhook secret configured, skipping signature verification", self.name)
            return True

        if not signature.startswith("sha256="):
            return False

        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature[7:], expected)

    async def handle_event(self, event_type: str, payload: Dict[str, Any]) -> Optional[str]:
        """Handle a GitHub webhook event.

        Returns a response message if the event was handled.
        """
        if event_type not in self.SUPPORTED_EVENTS:
            logger.debug("[%s] Ignoring unsupported event: %s", self.name, event_type)
            return None

        action = payload.get("action", "")
        logger.info("[%s] Handling %s.%s", self.name, event_type, action)

        try:
            if event_type == "pull_request" and action in ("opened", "synchronize", "reopened"):
                return await self._handle_pr_event(payload)
            elif event_type == "issues" and action == "opened":
                return await self._handle_issue_opened(payload)
            elif event_type == "pull_request_review" and action == "submitted":
                return await self._handle_pr_review(payload)
            elif event_type == "issue_comment" and action in ("created", "edited"):
                return await self._handle_issue_comment(payload)
        except Exception as e:
            logger.error("[%s] Error handling %s: %s", self.name, event_type, e, exc_info=True)
            return f"Error handling {event_type}: {e}"

        return None

    async def _handle_pr_event(self, payload: Dict[str, Any]) -> Optional[str]:
        """Handle pull request opened/synchronize events."""
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})

        if not pr or not repo:
            return None

        pr_number = pr.get("number")
        repo_full_name = repo.get("full_name")

        if not pr_number or not repo_full_name:
            return None

        # Fetch diff
        diff_url = pr.get("diff_url")
        diff = ""
        if diff_url:
            diff = await self._fetch_diff(diff_url)

        title = pr.get("title", "")
        body = pr.get("body", "")

        analysis = await self._analyze_pr(title, body, diff)

        # Post comment
        comment_body = (
            f"## 🤖 AI Analysis\n\n"
            f"{analysis}\n\n"
            f"---\n"
            f"*This comment was generated by MyAgent*"
        )

        success = await self._post_comment(repo_full_name, pr_number, comment_body)
        if success:
            logger.info("[%s] Posted analysis comment on PR #%d", self.name, pr_number)
            return f"Analyzed PR #{pr_number} in {repo_full_name}"
        else:
            logger.error("[%s] Failed to post comment on PR #%d", self.name, pr_number)
            return None

    async def _handle_issue_opened(self, payload: Dict[str, Any]) -> Optional[str]:
        """Handle new issue creation."""
        issue = payload.get("issue", {})
        repo = payload.get("repository", {})

        if not issue or not repo:
            return None

        issue_number = issue.get("number")
        repo_full_name = repo.get("full_name")
        title = issue.get("title", "")
        body = issue.get("body", "")

        # Simple classification
        labels = self._classify_issue(title, body)

        comment_body = (
            f"## 🤖 Issue Classification\n\n"
            f"Suggested labels: {', '.join(f'`{l}`' for l in labels)}\n\n"
            f"---\n"
            f"*This comment was generated by MyAgent*"
        )

        success = await self._post_comment(repo_full_name, issue_number, comment_body)
        if success:
            logger.info("[%s] Posted classification on Issue #%d", self.name, issue_number)
            return f"Classified Issue #{issue_number} in {repo_full_name}"
        return None

    async def _handle_pr_review(self, payload: Dict[str, Any]) -> Optional[str]:
        """Handle PR review submission."""
        review = payload.get("review", {})
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})

        if not review or not pr:
            return None

        pr_number = pr.get("number")
        repo_full_name = repo.get("full_name")
        state = review.get("state", "")

        if state == "changes_requested":
            comment = (
                "## 🤖 Review Summary\n\n"
                "Changes have been requested. Please address the feedback.\n\n"
                "---\n"
                "*This comment was generated by MyAgent*"
            )
            await self._post_comment(repo_full_name, pr_number, comment)

        return f"Processed review on PR #{pr_number}"

    async def _handle_issue_comment(self, payload: Dict[str, Any]) -> Optional[str]:
        """Handle issue/PR comments mentioning the bot."""
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})

        if not comment or not issue:
            return None

        body = comment.get("body", "")
        # Check if bot is mentioned
        if "@myagent" not in body.lower() and "/myagent" not in body.lower():
            return None

        # Create a message event for processing
        repo = payload.get("repository", {})
        repo_full_name = repo.get("full_name", "")
        issue_number = issue.get("number")

        # Extract command after mention
        text = body.lower().replace("@myagent", "").replace("/myagent", "").strip()

        source = self.build_source(
            chat_id=f"{repo_full_name}#{issue_number}",
            user_id=str(comment.get("user", {}).get("login", "unknown")),
            user_name=comment.get("user", {}).get("login"),
            chat_type="issue",
        )

        event = MessageEvent(
            text=text or "help",
            message_type=MessageType.TEXT,
            source=source,
            raw_message=payload,
        )

        # This would be handled by the message handler if set
        if self._message_handler:
            response = await self._message_handler(event)
            if response:
                await self._post_comment(repo_full_name, issue_number, response)
            return response

        return None

    async def _fetch_diff(self, diff_url: str) -> str:
        """Fetch PR diff from GitHub."""
        if not self._session:
            return ""
        try:
            async with self._session.get(diff_url, headers=self._headers) as resp:
                if resp.status == 200:
                    return await resp.text()
                logger.warning("[%s] Failed to fetch diff: %d", self.name, resp.status)
                return ""
        except Exception as e:
            logger.error("[%s] Error fetching diff: %s", self.name, e)
            return ""

    async def _analyze_pr(self, title: str, body: str, diff: str) -> str:
        """Analyze a PR and return a summary.

        In a full implementation, this would call the QueryEngine.
        For now, returns a basic summary.
        """
        lines_added = diff.count("\n+")
        lines_removed = diff.count("\n-")
        files_changed = len([l for l in diff.split("\n") if l.startswith("diff --git")])

        summary = (
            f"**Title:** {title}\n\n"
            f"**Files changed:** {files_changed}\n"
            f"**Additions:** ~{lines_added}\n"
            f"**Deletions:** ~{lines_removed}\n\n"
        )

        if body:
            summary += f"**Description:**\n{body[:500]}\n\n"

        # Extract changed filenames
        filenames = []
        for line in diff.split("\n")[:50]:
            if line.startswith("diff --git"):
                parts = line.split()
                if len(parts) >= 4:
                    filenames.append(parts[-1].replace("b/", ""))
        if filenames:
            summary += f"**Changed files:**\n" + "\n".join(f"- `{f}`" for f in filenames[:10])
            if len(filenames) > 10:
                summary += f"\n- ... and {len(filenames) - 10} more"

        return summary

    def _classify_issue(self, title: str, body: str) -> list[str]:
        """Classify an issue based on title/body."""
        text = f"{title} {body}".lower()
        labels = []

        if any(k in text for k in ("bug", "error", "crash", "fix", "broken", "fail")):
            labels.append("bug")
        if any(k in text for k in ("feature", "enhancement", "add", "support", "implement")):
            labels.append("enhancement")
        if any(k in text for k in ("documentation", "docs", "readme", "doc")):
            labels.append("documentation")
        if any(k in text for k in ("performance", "slow", "speed", "optimize", "memory")):
            labels.append("performance")
        if not labels:
            labels.append("triage")

        return labels

    async def _post_comment(self, repo: str, issue_number: int, body: str) -> bool:
        """Post a comment to a GitHub issue or PR."""
        if not self._session:
            return False

        url = f"{GITHUB_API_BASE}/repos/{repo}/issues/{issue_number}/comments"
        payload = {"body": body[:65536]}  # GitHub comment limit

        try:
            async with self._session.post(url, headers=self._headers, json=payload) as resp:
                if resp.status in (201, 200):
                    return True
                logger.warning(
                    "[%s] Failed to post comment: %d %s",
                    self.name, resp.status, await resp.text()
                )
                return False
        except Exception as e:
            logger.error("[%s] Error posting comment: %s", self.name, e)
            return False

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        """Send a message as a GitHub comment.

        chat_id format: "owner/repo#issue_number"
        """
        try:
            parts = chat_id.split("#")
            if len(parts) != 2:
                return SendResult(success=False, error=f"Invalid chat_id format: {chat_id}")

            repo = parts[0]
            issue_number = int(parts[1])

            success = await self._post_comment(repo, issue_number, content)
            if success:
                return SendResult(success=True)
            return SendResult(success=False, error="Failed to post comment")
        except Exception as e:
            return SendResult(success=False, error=str(e))

    async def send_typing(self, chat_id: str, metadata: Any = None) -> None:
        pass

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Get repository/issue info."""
        try:
            parts = chat_id.split("#")
            repo = parts[0]
            issue_number = parts[1] if len(parts) > 1 else ""
            return {
                "name": f"{repo}#{issue_number}",
                "type": "issue",
            }
        except Exception:
            return {"name": chat_id, "type": "issue"}
