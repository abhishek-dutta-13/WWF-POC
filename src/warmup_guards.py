"""
Warmup script - pre-downloads LLM Guard models during build phase.
Run as part of Render's buildCommand so models are cached at startup.
"""
import os

# Cache models inside the project directory so they survive the build
os.environ.setdefault("TRANSFORMERS_CACHE", "/opt/render/project/src/.hf_cache")
os.environ.setdefault("HF_HOME", "/opt/render/project/src/.hf_cache")

print("[Warmup] Pre-loading LLM Guard scanners...")

try:
    from llm_guard.input_scanners import PromptInjection, Toxicity as InputToxicity
    from llm_guard.output_scanners import Toxicity as OutputToxicity, Bias

    print("[Warmup] Loading PromptInjection scanner...")
    _ = PromptInjection()

    print("[Warmup] Loading Input Toxicity scanner...")
    _ = InputToxicity()

    print("[Warmup] Loading Output Toxicity scanner...")
    _ = OutputToxicity()

    print("[Warmup] Loading Bias scanner...")
    _ = Bias()

    print("[Warmup] All LLM Guard models downloaded and cached successfully.")

except Exception as e:
    print(f"[Warmup] Warning: Could not pre-load some scanners: {e}")
    print("[Warmup] Models will be downloaded on first request instead.")
