"""
LLM Guard - Input/output safety layer for the WWF chatbot.

Protects against:
- Prompt injection attacks
- Jailbreak attempts
- Toxic / harmful content
- Gender, caste, and ethnicity bias
- Other unsafe or malicious inputs/outputs

Based on the llm-guard library by ProtectAI:
  https://github.com/protectai/llm-guard

Usage:
    from guardrails.llm_guard import get_llm_guard

    guard = get_llm_guard()

    # Scan user input BEFORE sending to the LLM
    sanitized_input, is_safe, reason = guard.scan_input(user_message)
    if not is_safe:
        return "Your message was blocked: " + reason

    # Scan LLM output BEFORE returning to the user
    sanitized_output, is_safe, reason = guard.scan_output(user_message, llm_response)
"""
import logging
import os
from typing import Tuple

# Use the same HuggingFace cache that was populated during build
_hf_cache = os.getenv("HF_HOME", os.path.join(os.path.dirname(__file__), "..", "..", ".hf_cache"))
os.environ.setdefault("HF_HOME", _hf_cache)
os.environ.setdefault("TRANSFORMERS_CACHE", _hf_cache)

logger = logging.getLogger(__name__)


class LLMGuard:
    """
    Wraps llm-guard input and output scanners with graceful degradation.

    If llm-guard is not installed or a scanner fails to load, the guard
    operates in pass-through mode so the chatbot continues to function.
    """

    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._input_scanners = []
        self._output_scanners = []
        self._scan_prompt_fn = None
        self._scan_output_fn = None

        if enabled:
            self._setup_scanners()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_scanners(self) -> None:
        """
        Import llm-guard and initialise all required scanners.
        Any scanner that is unavailable in the installed version is skipped
        with a warning so the rest still work.
        """
        try:
            from llm_guard import scan_prompt, scan_output  # type: ignore
            self._scan_prompt_fn = scan_prompt
            self._scan_output_fn = scan_output
        except ImportError:
            logger.warning(
                "[LLM Guard] llm-guard is not installed. "
                "Run `pip install llm-guard` to enable content safety scanning. "
                "Operating in pass-through mode."
            )
            self._enabled = False
            return

        # ---- Input scanners ----
        self._input_scanners = []

        # Prompt injection (covers many jailbreak patterns as well)
        try:
            from llm_guard.input_scanners import PromptInjection  # type: ignore
            self._input_scanners.append(PromptInjection())
            logger.info("[LLM Guard] PromptInjection scanner loaded")
        except Exception as exc:
            logger.warning(f"[LLM Guard] PromptInjection scanner unavailable: {exc}")

        # Explicit jailbreak scanner (available in newer versions)
        try:
            from llm_guard.input_scanners import Jailbreak  # type: ignore
            self._input_scanners.append(Jailbreak())
            logger.info("[LLM Guard] Jailbreak scanner loaded")
        except (ImportError, Exception) as exc:
            logger.info(
                f"[LLM Guard] Jailbreak scanner not available in this version "
                f"(covered by PromptInjection): {exc}"
            )

        # Toxicity / harmful content on input
        try:
            from llm_guard.input_scanners import Toxicity as InputToxicity  # type: ignore
            self._input_scanners.append(InputToxicity())
            logger.info("[LLM Guard] Input Toxicity scanner loaded")
        except Exception as exc:
            logger.warning(f"[LLM Guard] Input Toxicity scanner unavailable: {exc}")

        # ---- Output scanners ----
        self._output_scanners = []

        # Toxicity / harmful content on output
        try:
            from llm_guard.output_scanners import Toxicity as OutputToxicity  # type: ignore
            self._output_scanners.append(OutputToxicity())
            logger.info("[LLM Guard] Output Toxicity scanner loaded")
        except Exception as exc:
            logger.warning(f"[LLM Guard] Output Toxicity scanner unavailable: {exc}")

        # Bias: gender, caste, ethnicity, etc.
        try:
            from llm_guard.output_scanners import Bias  # type: ignore
            self._output_scanners.append(Bias())
            logger.info("[LLM Guard] Bias scanner loaded")
        except Exception as exc:
            logger.warning(f"[LLM Guard] Bias scanner unavailable: {exc}")

        loaded_in = len(self._input_scanners)
        loaded_out = len(self._output_scanners)

        if loaded_in == 0 and loaded_out == 0:
            logger.warning(
                "[LLM Guard] No scanners could be loaded. "
                "Operating in pass-through mode."
            )
            self._enabled = False
        else:
            logger.info(
                f"[LLM Guard] Initialized — "
                f"{loaded_in} input scanner(s), {loaded_out} output scanner(s)"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_enabled(self) -> bool:
        """Return True when at least one scanner is active."""
        return self._enabled

    def scan_input(self, prompt: str) -> Tuple[str, bool, str]:
        """
        Scan user input for harmful / malicious content before it reaches
        the LLM.

        Args:
            prompt: Raw user message.

        Returns:
            (sanitized_prompt, is_safe, reason)
            - sanitized_prompt: Cleaned text (may be the original if nothing was
              detected).
            - is_safe: False when a scanner has flagged the input.
            - reason: Human-readable explanation when is_safe is False.
        """
        if not self._enabled or not self._input_scanners:
            return prompt, True, ""

        try:
            sanitized, results_valid, _scores = self._scan_prompt_fn(
                self._input_scanners, prompt
            )

            failed = [name for name, ok in results_valid.items() if not ok]
            if failed:
                reason = f"Input blocked by safety scanner(s): {', '.join(failed)}"
                logger.warning(f"[LLM Guard] {reason} | prompt snippet: {prompt[:80]!r}")
                return sanitized, False, reason

            return sanitized, True, ""

        except Exception as exc:
            # Fail open — do not block legitimate traffic due to scanner errors
            logger.error(f"[LLM Guard] Error during input scan: {exc}")
            return prompt, True, ""

    def scan_output(self, prompt: str, response: str) -> Tuple[str, bool, str]:
        """
        Scan LLM output for harmful, biased, or toxic content before it is
        returned to the user.

        Args:
            prompt: The (sanitized) user prompt that triggered the response.
            response: The raw LLM response text.

        Returns:
            (sanitized_response, is_safe, reason)
        """
        if not self._enabled or not self._output_scanners:
            return response, True, ""

        try:
            sanitized, results_valid, _scores = self._scan_output_fn(
                self._output_scanners, prompt, response
            )

            failed = [name for name, ok in results_valid.items() if not ok]
            if failed:
                reason = f"Output flagged by safety scanner(s): {', '.join(failed)}"
                logger.warning(f"[LLM Guard] {reason}")
                return sanitized, False, reason

            return sanitized, True, ""

        except Exception as exc:
            logger.error(f"[LLM Guard] Error during output scan: {exc}")
            return response, True, ""


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_guard_instance: LLMGuard | None = None


def get_llm_guard() -> LLMGuard:
    """Return the module-level LLMGuard singleton, creating it if needed."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = LLMGuard()
    return _guard_instance
