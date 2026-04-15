"""
OpenAI Moderation - Input/output safety layer for the WWF chatbot.

Uses the OpenAI Moderation API (free, fast ~100-200ms) to detect:
- Hate speech / harassment
- Violence / threats
- Self-harm content
- Sexual content
- Harassment / threatening language

No local model downloads. Uses the existing OPENAI_API_KEY.

Usage:
    from guardrails.openai_moderator import get_moderator

    moderator = get_moderator()

    # Scan user input BEFORE sending to the LLM
    is_safe, reason = moderator.scan_input(user_message)
    if not is_safe:
        return "Your message was blocked: " + reason

    # Scan LLM output BEFORE returning to the user
    is_safe, reason = moderator.scan_output(llm_response)
"""
import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class OpenAIModerator:
    """
    Wraps the OpenAI Moderation API with graceful degradation.

    If OPENAI_API_KEY is missing or the API call fails, operates in
    pass-through mode so the chatbot continues to function.
    """

    # Categories to block (subset of all OpenAI moderation categories)
    BLOCKED_CATEGORIES = {
        "hate",
        "hate/threatening",
        "harassment",
        "harassment/threatening",
        "self-harm",
        "self-harm/intent",
        "self-harm/instructions",
        "sexual/minors",
        "violence",
        "violence/graphic",
    }

    def __init__(self):
        self._client = None
        self._enabled = False
        self._setup()

    def _setup(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning(
                "[Moderator] OPENAI_API_KEY not found. "
                "Content moderation disabled — operating in pass-through mode."
            )
            return

        try:
            from openai import OpenAI  # type: ignore
            self._client = OpenAI(api_key=api_key)
            self._enabled = True
            logger.info("[Moderator] OpenAI Moderation API initialized ✅")
        except ImportError:
            logger.warning("[Moderator] openai package not installed. Moderation disabled.")
        except Exception as exc:
            logger.warning(f"[Moderator] Failed to initialize OpenAI client: {exc}")

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def _moderate(self, text: str) -> Tuple[bool, str]:
        """
        Call the OpenAI Moderation endpoint.

        Returns:
            (is_safe, reason) — reason is empty string when safe.
        """
        if not self._enabled or not self._client:
            return True, ""

        try:
            response = self._client.moderations.create(
                model="omni-moderation-latest",
                input=text
            )
            result = response.results[0]

            if result.flagged:
                # Collect which categories triggered
                flagged_cats = [
                    cat for cat, flagged in result.categories.__dict__.items()
                    if flagged and cat.replace("_", "/") in self.BLOCKED_CATEGORIES
                        or flagged and cat in self.BLOCKED_CATEGORIES
                ]
                # Fallback: if none matched our explicit list, use all flagged ones
                if not flagged_cats:
                    flagged_cats = [
                        cat for cat, flagged in result.categories.__dict__.items() if flagged
                    ]
                reason = f"Content flagged: {', '.join(flagged_cats)}"
                logger.warning(f"[Moderator] {reason} | text snippet: {text[:80]!r}")
                return False, reason

            return True, ""

        except Exception as exc:
            # Fail open — don't block legitimate traffic due to API errors
            logger.error(f"[Moderator] API error during moderation: {exc}")
            return True, ""

    def scan_input(self, text: str) -> Tuple[bool, str]:
        """
        Scan user input for harmful content before it reaches the LLM.

        Returns:
            (is_safe, reason)
        """
        is_safe, reason = self._moderate(text)
        if not is_safe:
            logger.warning(f"[Moderator] Input blocked: {reason}")
        return is_safe, reason

    def scan_output(self, text: str) -> Tuple[bool, str]:
        """
        Scan LLM output for harmful content before returning to the user.

        Returns:
            (is_safe, reason)
        """
        is_safe, reason = self._moderate(text)
        if not is_safe:
            logger.warning(f"[Moderator] Output flagged: {reason}")
        return is_safe, reason


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_moderator_instance: OpenAIModerator | None = None


def get_moderator() -> OpenAIModerator:
    """Return the module-level OpenAIModerator singleton."""
    global _moderator_instance
    if _moderator_instance is None:
        _moderator_instance = OpenAIModerator()
    return _moderator_instance
