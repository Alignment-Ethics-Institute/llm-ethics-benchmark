"""
Shared Model Registry & API Interface
======================================
Extracted from run_instrumentaleval_multimodel.py.
Provides MODEL_REGISTRY, init_clients(), _call_model(), generate_model_response().

All benchmark runners import from here to avoid duplicating provider logic.
Temperature is controlled by the caller (runners pass temperature= override).
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import httpx
import openai
import anthropic

REQUEST_TIMEOUT = 120
MAX_RETRIES = 2
JUDGE_MODEL = "claude-haiku-4-5-20251001"


# =============================================================================
# Model Registry — each model's full API configuration
# =============================================================================

MODEL_REGISTRY = {
    # --- Anthropic (pre-thinking era) ---
    "opus-3": {
        "display_name": "Claude Opus 3",
        "provider": "anthropic",
        "model_id": "claude-3-opus-20240229",
        "env_key": "ANTHROPIC_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 1.5,
        "note": "No extended thinking. Supports temperature.",
    },
    "sonnet-3.5": {
        "display_name": "Claude 3.5 Sonnet",
        "provider": "anthropic",
        "model_id": "claude-3-5-sonnet-20241022",
        "env_key": "ANTHROPIC_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 1.0,
        "note": "Most widely deployed Claude model. Pre-thinking era.",
    },
    # --- Anthropic (thinking ON via extended thinking) ---
    "opus-4.6": {
        "display_name": "Claude Opus 4.6",
        "provider": "anthropic",
        "model_id": "claude-opus-4-6",
        "env_key": "ANTHROPIC_API_KEY",
        "temperature": None,  # Cannot set with thinking
        "max_tokens": 16000,
        "thinking": {"type": "enabled", "budget_tokens": 10000},
        "delay": 1.5,
    },
    "sonnet-4.5": {
        "display_name": "Claude Sonnet 4.5",
        "provider": "anthropic",
        "model_id": "claude-sonnet-4-5-20250929",
        "env_key": "ANTHROPIC_API_KEY",
        "temperature": None,
        "max_tokens": 16000,
        "thinking": {"type": "enabled", "budget_tokens": 10000},
        "delay": 1.5,
        "note": "Same model as judge — self-judging caveat applies",
    },
    # --- Google Gemini ---
    "gemini-1.5-pro": {
        "display_name": "Gemini 1.5 Pro",
        "provider": "google",
        "model_id": "gemini-1.5-pro",
        "env_key": "GOOGLE_API_KEY",
        "temperature": 0.7,
        "max_output_tokens": 4096,
        "delay": 1.0,
        "note": "Gen 1.5 baseline. No thinking budget.",
    },
    "gemini-2.5-pro": {
        "display_name": "Gemini 2.5 Pro",
        "provider": "google",
        "model_id": "gemini-2.5-pro",
        "env_key": "GOOGLE_API_KEY",
        "vertexai": True,
        "vertexai_project": os.getenv("VERTEXAI_PROJECT", ""),
        "vertexai_location": "global",
        "temperature": 0.0,
        "max_output_tokens": 4096,
        "thinking_budget": 8192,
        "delay": 4.0,
    },
    "gemini-3-pro": {
        "display_name": "Gemini 3 Pro (Preview)",
        "provider": "google",
        "model_id": "gemini-3-pro-preview",
        "env_key": "GOOGLE_API_KEY",
        "vertexai": True,
        "vertexai_project": os.getenv("VERTEXAI_PROJECT", ""),
        "vertexai_location": "global",
        "temperature": 1.0,
        "max_output_tokens": 4096,
        "thinking_budget": 8192,
        "delay": 4.0,
    },
    "gemini-2.5-flash": {
        "display_name": "Gemini 2.5 Flash",
        "provider": "google",
        "model_id": "gemini-2.5-flash",
        "env_key": "GOOGLE_API_KEY",
        "temperature": 0.7,
        "max_output_tokens": 4096,
        "thinking_budget": 8192,
        "delay": 0.3,
    },
    "gemini-2.5-flash-lite": {
        "display_name": "Gemini 2.5 Flash Lite",
        "provider": "google",
        "model_id": "gemini-2.5-flash-lite",
        "env_key": "GOOGLE_API_KEY",
        "temperature": 0.7,
        "max_output_tokens": 4096,
        "delay": 0.3,
    },
    "gemini-3-flash": {
        "display_name": "Gemini 3 Flash (Preview)",
        "provider": "google",
        "model_id": "gemini-3-flash-preview",
        "env_key": "GOOGLE_API_KEY",
        "temperature": 0.7,
        "max_output_tokens": 4096,
        "thinking_budget": 8192,
        "delay": 0.3,
    },
    "gemini-3.1-pro": {
        "display_name": "Gemini 3.1 Pro (Preview)",
        "provider": "google",
        "model_id": "gemini-3.1-pro-preview",
        "env_key": "GOOGLE_API_KEY",
        "vertexai": True,
        "vertexai_project": os.getenv("VERTEXAI_PROJECT", ""),
        "vertexai_location": "global",
        "temperature": 0.7,
        "max_output_tokens": 4096,
        "thinking_budget": 8192,
        "delay": 4.0,
    },
    # --- OpenAI ---
    "gpt-5.5": {
        "display_name": "GPT-5.5",
        "provider": "openai",
        "model_id": "gpt-5.5",
        "env_key": "OPENAI_API_KEY",
        "temperature": None,
        "max_completion_tokens": 16384,
        "reasoning_effort": "medium",
        "delay": 0.5,
    },
    "gpt-5.4": {
        "display_name": "GPT-5.4",
        "provider": "openai",
        "model_id": "gpt-5.4",
        "env_key": "OPENAI_API_KEY",
        "temperature": None,
        "max_completion_tokens": 16384,
        "reasoning_effort": "medium",
        "delay": 0.5,
    },
    "gpt-5.2": {
        "display_name": "GPT-5.2",
        "provider": "openai",
        "model_id": "gpt-5.2",
        "env_key": "OPENAI_API_KEY",
        "temperature": None,
        "max_completion_tokens": 16384,
        "reasoning_effort": "medium",
        "delay": 0.5,
    },
    "gpt-5": {
        "display_name": "GPT-5",
        "provider": "openai",
        "model_id": "gpt-5",
        "env_key": "OPENAI_API_KEY",
        "temperature": None,
        "max_completion_tokens": 16384,
        "reasoning_effort": "medium",
        "delay": 0.5,
    },
    "gpt-5.1": {
        "display_name": "GPT-5.1",
        "provider": "openai",
        "model_id": "gpt-5.1",
        "env_key": "OPENAI_API_KEY",
        "temperature": None,
        "max_completion_tokens": 16384,
        "reasoning_effort": "medium",
        "delay": 0.5,
    },
    "gpt-4.1": {
        "display_name": "GPT-4.1",
        "provider": "openai",
        "model_id": "gpt-4.1",
        "env_key": "OPENAI_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.3,
    },
    "gpt-4.1-mini": {
        "display_name": "GPT-4.1 Mini",
        "provider": "openai",
        "model_id": "gpt-4.1-mini",
        "env_key": "OPENAI_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.2,
    },
    "gpt-4.1-nano": {
        "display_name": "GPT-4.1 Nano",
        "provider": "openai",
        "model_id": "gpt-4.1-nano",
        "env_key": "OPENAI_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.2,
    },
    "gpt-4-turbo": {
        "display_name": "GPT-4 Turbo",
        "provider": "openai",
        "model_id": "gpt-4-turbo",
        "env_key": "OPENAI_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.5,
        "note": "Pre-4o generation baseline. May be deprecated — test access.",
    },
    "gpt-4o": {
        "display_name": "GPT-4o",
        "provider": "openai",
        "model_id": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.3,
    },
    "chatgpt-4o-latest": {
        "display_name": "ChatGPT-4o-latest",
        "provider": "openai",
        "model_id": "chatgpt-4o-latest",
        "env_key": "OPENAI_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.3,
    },
    # --- OpenRouter ---
    "deepseek-r1": {
        "display_name": "DeepSeek R1",
        "provider": "openai_compat",
        "model_id": "deepseek-reasoner",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "temperature": 0.0,
        "max_tokens": 32768,
        "system_in_user": True,
        "delay": 0.5,
        "note": "Direct DeepSeek API; system prompt in user message",
    },
    "llama-4-maverick": {
        "display_name": "Llama 4 Maverick",
        "provider": "openrouter",
        "model_id": "meta-llama/llama-4-maverick",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.0,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "qwen3-235b": {
        "display_name": "Qwen3 235B",
        "provider": "openrouter",
        "model_id": "qwen/qwen3-235b-a22b",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.6,
        "max_tokens": 4096,
        "reasoning": {"enabled": True},
        "delay": 3.0,
    },
    "grok-4.1": {
        "display_name": "Grok 4.1 Fast (Reasoning)",
        "provider": "openai_compat",
        "model_id": "grok-4-1-fast-reasoning",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.0,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "deepseek-chat": {
        "display_name": "DeepSeek V3 (Chat)",
        "provider": "openai_compat",
        "model_id": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "temperature": 0.0,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "kimi-k2.5": {
        "display_name": "Kimi K2.5",
        "provider": "openrouter",
        "model_id": "moonshotai/kimi-k2.5",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.0,
        "max_tokens": 4096,
        "reasoning": {"enabled": True},
        "delay": 0.5,
    },
    "grok-4.1-nr": {
        "display_name": "Grok 4.1 Fast (Non-Reasoning)",
        "provider": "openai_compat",
        "model_id": "grok-4-1-fast-non-reasoning",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.0,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "grok-4.5": {
        "display_name": "Grok 4.5",
        "provider": "openai_compat",
        "model_id": "grok-4.5",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.0,
        "max_tokens": 4096,
        "delay": 0.5,
        "note": "Configurable reasoning_effort (default high). Single model ID, no separate variants.",
    },
    # --- Fine-Tuning Candidates (all OpenRouter, dense 70B) ---
    "llama-3.3-70b": {
        "display_name": "Llama 3.3 70B Instruct",
        "provider": "openrouter",
        "model_id": "meta-llama/llama-3.3-70b-instruct",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "qwen-2.5-72b": {
        "display_name": "Qwen 2.5 72B Instruct",
        "provider": "openrouter",
        "model_id": "qwen/qwen-2.5-72b-instruct",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "deepseek-r1-distill-70b": {
        "display_name": "DeepSeek R1 Distill Llama 70B",
        "provider": "openrouter",
        "model_id": "deepseek/deepseek-r1-distill-llama-70b",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "nemotron-70b": {
        "display_name": "NVIDIA Nemotron 70B Instruct",
        "provider": "openrouter",
        "model_id": "nvidia/llama-3.1-nemotron-70b-instruct",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "hermes-4-70b": {
        "display_name": "Nous Hermes 4 70B",
        "provider": "openrouter",
        "model_id": "nousresearch/hermes-4-70b",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "mistral-large-2": {
        "display_name": "Mistral Large 2 (2411)",
        "provider": "openrouter",
        "model_id": "mistralai/mistral-large-2411",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 0.5,
    },
    "llama-3.1-405b": {
        "display_name": "Llama 3.1 405B Instruct",
        "provider": "openrouter",
        "model_id": "meta-llama/llama-3.1-405b-instruct",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 1.0,
    },
    "hermes-3-405b": {
        "display_name": "Nous Hermes 3 405B",
        "provider": "openrouter",
        "model_id": "nousresearch/hermes-3-llama-3.1-405b",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 0.7,
        "max_tokens": 4096,
        "delay": 1.0,
    },
    # --- Round 3: xAI Grok (filling the lineage) ---
    "grok-4.3": {
        "display_name": "Grok 4.3",
        "provider": "openai_compat",
        "model_id": "grok-4.3",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.0,
        "max_tokens": 4096,
        "delay": 0.5,
        "note": "April 2026. 1M context, native video input.",
    },
    "grok-4.20-r": {
        "display_name": "Grok 4.20 (Reasoning)",
        "provider": "openai_compat",
        "model_id": "grok-4.20-0309-reasoning",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.0,
        "max_tokens": 4096,
        "delay": 0.5,
        "note": "Reasoning variant. 2M context.",
    },
    "grok-4.20-nr": {
        "display_name": "Grok 4.20 (Non-Reasoning)",
        "provider": "openai_compat",
        "model_id": "grok-4.20-0309-non-reasoning",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.0,
        "max_tokens": 4096,
        "delay": 0.5,
        "note": "Non-reasoning variant. 2M context.",
    },
    # --- Round 3: Anthropic (Claude 5 generation, adaptive thinking) ---
    "opus-4.8": {
        "display_name": "Claude Opus 4.8",
        "provider": "anthropic",
        "model_id": "claude-opus-4-8",
        "env_key": "ANTHROPIC_API_KEY",
        "temperature": None,  # Adaptive thinking on by default
        "max_tokens": 16000,
        "delay": 1.5,
        "note": "Adaptive thinking (not legacy extended). 1M context, 128K max output.",
    },
    "fable-5": {
        "display_name": "Claude Fable 5",
        "provider": "anthropic",
        "model_id": "claude-fable-5",
        "env_key": "ANTHROPIC_API_KEY",
        "temperature": None,  # Temperature rejected with 400
        "max_tokens": 16000,
        "delay": 1.5,
        "note": "Always-on adaptive thinking, cannot disable. Temperature/top_p/top_k all rejected.",
    },
    "sonnet-5": {
        "display_name": "Claude Sonnet 5",
        "provider": "anthropic",
        "model_id": "claude-sonnet-5",
        "env_key": "ANTHROPIC_API_KEY",
        "temperature": None,
        "max_tokens": 16000,
        "delay": 1.5,
        "note": "Adaptive thinking on by default. Non-default sampling parameters rejected.",
    },
    "opus-5": {
        "display_name": "Claude Opus 5",
        "provider": "anthropic",
        "model_id": "claude-opus-5",
        "env_key": "ANTHROPIC_API_KEY",
        "temperature": None,
        "max_tokens": 16000,
        "delay": 1.5,
        "note": "Adaptive thinking on by default. 1M context, 128K max output.",
    },
    # --- Round 3: OpenAI (GPT-5.6 family, reasoning models) ---
    "gpt-5.6-sol": {
        "display_name": "GPT-5.6 Sol",
        "provider": "openai",
        "model_id": "gpt-5.6-sol",
        "env_key": "OPENAI_API_KEY",
        "temperature": None,
        "max_completion_tokens": 16384,
        "reasoning_effort": "medium",
        "delay": 0.5,
        "note": "Flagship tier. 1M context.",
    },
    "gpt-5.6-terra": {
        "display_name": "GPT-5.6 Terra",
        "provider": "openai",
        "model_id": "gpt-5.6-terra",
        "env_key": "OPENAI_API_KEY",
        "temperature": None,
        "max_completion_tokens": 16384,
        "reasoning_effort": "medium",
        "delay": 0.5,
        "note": "Balanced everyday model. 1M context.",
    },
    "gpt-5.6-luna": {
        "display_name": "GPT-5.6 Luna",
        "provider": "openai",
        "model_id": "gpt-5.6-luna",
        "env_key": "OPENAI_API_KEY",
        "temperature": None,
        "max_completion_tokens": 16384,
        "reasoning_effort": "medium",
        "delay": 0.5,
        "note": "Fastest, cheapest tier. 1M context.",
    },
    # --- Round 3: Google Gemini (3.5/3.6 generation, thinking_level API) ---
    "gemini-3.5-flash": {
        "display_name": "Gemini 3.5 Flash",
        "provider": "google",
        "model_id": "gemini-3.5-flash",
        "env_key": "GOOGLE_API_KEY",
        "temperature": 1.0,
        "max_output_tokens": 4096,
        "thinking_level": "MEDIUM",
        "delay": 0.3,
        "note": "1M context. Thinking via thinking_level (not thinking_budget).",
    },
    "gemini-3.5-flash-lite": {
        "display_name": "Gemini 3.5 Flash Lite",
        "provider": "google",
        "model_id": "gemini-3.5-flash-lite",
        "env_key": "GOOGLE_API_KEY",
        "temperature": 1.0,
        "max_output_tokens": 4096,
        "thinking_level": "MEDIUM",
        "delay": 0.3,
        "note": "Defaults to MINIMAL thinking. Set MEDIUM for benchmark comparability.",
    },
    "gemini-3.6-flash": {
        "display_name": "Gemini 3.6 Flash",
        "provider": "google",
        "model_id": "gemini-3.6-flash",
        "env_key": "GOOGLE_API_KEY",
        "temperature": 1.0,
        "max_output_tokens": 4096,
        "thinking_level": "MEDIUM",
        "delay": 0.3,
        "note": "1M context, 64K max output. Computer Use supported.",
    },
    # --- Round 3: DeepSeek V4 ---
    "deepseek-v4": {
        "display_name": "DeepSeek V4 Flash",
        "provider": "openai_compat",
        "model_id": "deepseek-v4-flash",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "temperature": 0.0,
        "max_tokens": 4096,
        "delay": 0.5,
        "note": "284B total, 13B active MoE. 1M context.",
    },
    # --- Round 3: Kimi K3 (OpenRouter) ---
    "kimi-k3": {
        "display_name": "Kimi K3",
        "provider": "openrouter",
        "model_id": "moonshotai/kimi-k3",
        "env_key": "OPENROUTER_API_KEY",
        "temperature": 1.0,  # Fixed at 1.0 by provider
        "max_tokens": 4096,
        "reasoning": {"enabled": True},
        "delay": 1.0,
        "note": "2.8T params, always-on reasoning. Temperature fixed at 1.0. 1M context.",
    },
}


# =============================================================================
# API Client Setup
# =============================================================================

def init_clients(model_config, need_judge=False, need_embeddings=False):
    """Initialize API clients for a model run.

    Args:
        model_config: Entry from MODEL_REGISTRY.
        need_judge: If True, initialize Anthropic client for judging.
        need_embeddings: If True, initialize OpenAI client for RAG embeddings.
    """
    clients = {}

    if need_embeddings:
        oai_key = os.getenv("OPENAI_API_KEY")
        if not oai_key:
            print("ERROR: OPENAI_API_KEY required (RAG embeddings)")
            sys.exit(1)
        clients["openai_embed"] = openai.OpenAI(api_key=oai_key, timeout=REQUEST_TIMEOUT)

    if need_judge:
        anth_key = os.getenv("ANTHROPIC_API_KEY")
        if not anth_key:
            print("ERROR: ANTHROPIC_API_KEY required (judge)")
            sys.exit(1)
        clients["anthropic_judge"] = anthropic.Anthropic(
            api_key=anth_key,
            timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=10.0),
        )

    provider = model_config["provider"]
    api_key = os.getenv(model_config["env_key"])
    if not api_key:
        print(f"ERROR: {model_config['env_key']} not set in .env")
        sys.exit(1)

    if provider == "anthropic":
        clients["model"] = anthropic.Anthropic(
            api_key=api_key,
            timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=10.0),
        )
    elif provider == "google":
        from google import genai
        if model_config.get("vertexai"):
            clients["model"] = genai.Client(
                vertexai=True,
                project=model_config["vertexai_project"],
                location=model_config["vertexai_location"],
                http_options={"timeout": REQUEST_TIMEOUT * 1000},
            )
        else:
            clients["model"] = genai.Client(
                api_key=api_key,
                http_options={"timeout": REQUEST_TIMEOUT * 1000},
            )
    elif provider == "openrouter":
        clients["model"] = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=REQUEST_TIMEOUT,
            default_headers={
                "HTTP-Referer": "https://alignmentethics.org",
                "X-Title": "Elessan Benchmark",
            },
        )
    elif provider == "openai":
        clients["model"] = openai.OpenAI(api_key=api_key, timeout=REQUEST_TIMEOUT)
    elif provider == "openai_compat":
        clients["model"] = openai.OpenAI(
            base_url=model_config.get("base_url"),
            api_key=api_key,
            timeout=REQUEST_TIMEOUT,
        )

    return clients


# =============================================================================
# Model Response Generation
# =============================================================================

def _call_model(model_config, clients, system_prompt, user_prompt, temperature=None, max_tokens_override=None):
    """Single API call to the target model. Provider-specific handling.

    Args:
        temperature: Override the registry temperature for this call.
        max_tokens_override: Override the registry max_tokens for this call.
    """
    provider = model_config["provider"]
    model_id = model_config["model_id"]
    client = clients["model"]

    # Determine effective temperature
    temp = temperature if temperature is not None else model_config.get("temperature")

    # ---- Anthropic ----
    if provider == "anthropic":
        kwargs = {
            "model": model_id,
            "max_tokens": max_tokens_override or model_config.get("max_tokens", 4096),
            "system": system_prompt if system_prompt else "",
            "messages": [{"role": "user", "content": user_prompt}],
        }
        thinking = model_config.get("thinking")
        if thinking:
            kwargs["thinking"] = thinking
        if temp is not None and not thinking:
            kwargs["temperature"] = temp

        response = client.messages.create(**kwargs)
        text_parts = [b.text for b in response.content if b.type == "text"]
        return "\n".join(text_parts) if text_parts else None

    # ---- Google Gemini ----
    elif provider == "google":
        from google import genai
        from google.genai import types

        # Gemini thinking models: max_output_tokens must cover thinking + response
        tb = model_config.get("thinking_budget")
        tl = model_config.get("thinking_level")
        base_output = max_tokens_override or model_config.get("max_output_tokens", 4096)
        effective_max_output = base_output + tb if tb else base_output

        config_kwargs = {
            "system_instruction": system_prompt if system_prompt else "",
            "max_output_tokens": effective_max_output,
            "safety_settings": [
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ],
        }
        if temp is not None:
            config_kwargs["temperature"] = temp
        if tb:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=tb)
        elif tl:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=tl)

        response = client.models.generate_content(
            model=model_id,
            contents=user_prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        if response.text:
            return response.text
        reason = "unknown"
        if response.candidates:
            reason = response.candidates[0].finish_reason
        print(f"    Gemini silent block (finish_reason={reason})")
        return None

    # ---- OpenAI ----
    elif provider == "openai":
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        kwargs = {"model": model_id, "messages": messages}
        if "max_completion_tokens" in model_config:
            # Reasoning models: ignore small max_tokens_override (reasoning needs room)
            kwargs["max_completion_tokens"] = model_config["max_completion_tokens"]
        else:
            kwargs["max_tokens"] = max_tokens_override or model_config.get("max_tokens", 4096)
        if "reasoning_effort" in model_config:
            kwargs["reasoning_effort"] = model_config["reasoning_effort"]
            # Reasoning models don't support temperature override
            temp = None
        if temp is not None:
            kwargs["temperature"] = temp

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    # ---- OpenRouter ----
    elif provider == "openrouter":
        if model_config.get("system_in_user"):
            messages = [{"role": "user", "content": f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt}]
        else:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

        kwargs = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens_override or model_config.get("max_tokens", 4096),
        }
        if temp is not None:
            kwargs["temperature"] = temp
        reasoning = model_config.get("reasoning")
        if reasoning:
            kwargs["extra_body"] = {"reasoning": reasoning}

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    # ---- OpenAI-compatible ----
    elif provider == "openai_compat":
        if model_config.get("system_in_user"):
            messages = [{"role": "user", "content": f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt}]
        else:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

        kwargs = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens_override or model_config.get("max_tokens", 4096),
        }
        if temp is not None:
            kwargs["temperature"] = temp

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


def _call_model_multiturn(model_config, clients, system_prompt, messages,
                          temperature=None, max_tokens_override=None):
    """API call with full conversation history. Provider-specific handling.

    Args:
        system_prompt: System prompt string (or empty).
        messages: List of {"role": "user"/"assistant", "content": "..."} dicts.
        temperature: Override the registry temperature for this call.
        max_tokens_override: Override the registry max_tokens for this call.
    """
    provider = model_config["provider"]
    model_id = model_config["model_id"]
    client = clients["model"]
    temp = temperature if temperature is not None else model_config.get("temperature")

    # ---- Anthropic ----
    if provider == "anthropic":
        kwargs = {
            "model": model_id,
            "max_tokens": max_tokens_override or model_config.get("max_tokens", 4096),
            "system": system_prompt if system_prompt else "",
            "messages": messages,
        }
        thinking = model_config.get("thinking")
        if thinking:
            kwargs["thinking"] = thinking
        if temp is not None and not thinking:
            kwargs["temperature"] = temp
        response = client.messages.create(**kwargs)
        text_parts = [b.text for b in response.content if b.type == "text"]
        return "\n".join(text_parts) if text_parts else None

    # ---- Google Gemini ----
    elif provider == "google":
        from google import genai
        from google.genai import types

        tb = model_config.get("thinking_budget")
        tl = model_config.get("thinking_level")
        base_output = max_tokens_override or model_config.get("max_output_tokens", 4096)
        effective_max_output = base_output + tb if tb else base_output

        config_kwargs = {
            "system_instruction": system_prompt if system_prompt else "",
            "max_output_tokens": effective_max_output,
            "safety_settings": [
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ],
        }
        if temp is not None:
            config_kwargs["temperature"] = temp
        if tb:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=tb)
        elif tl:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=tl)

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        if response.text:
            return response.text
        reason = "unknown"
        if response.candidates:
            reason = response.candidates[0].finish_reason
        print(f"    Gemini silent block (finish_reason={reason})")
        return None

    # ---- OpenAI / OpenRouter / OpenAI-compatible ----
    elif provider in ("openai", "openrouter", "openai_compat"):
        api_messages = []
        if model_config.get("system_in_user"):
            # Prepend system to first user message
            if system_prompt and messages:
                first = messages[0].copy()
                first["content"] = f"{system_prompt}\n\n{first['content']}"
                api_messages = [first] + messages[1:]
            else:
                api_messages = list(messages)
        else:
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            api_messages.extend(messages)

        kwargs = {"model": model_id, "messages": api_messages}
        if "max_completion_tokens" in model_config:
            kwargs["max_completion_tokens"] = model_config["max_completion_tokens"]
        else:
            kwargs["max_tokens"] = max_tokens_override or model_config.get("max_tokens", 4096)
        if "reasoning_effort" in model_config:
            kwargs["reasoning_effort"] = model_config["reasoning_effort"]
            temp = None
        if temp is not None:
            kwargs["temperature"] = temp
        if provider == "openrouter":
            reasoning = model_config.get("reasoning")
            if reasoning:
                kwargs["extra_body"] = {"reasoning": reasoning}

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


def generate_model_response_multiturn(model_config, clients, system_prompt, messages,
                                      temperature=None, max_tokens_override=None):
    """Generate a response from a multi-turn conversation with retry and timeout."""
    hard_timeout = REQUEST_TIMEOUT + 30
    max_attempts = MAX_RETRIES
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    _call_model_multiturn, model_config, clients, system_prompt,
                    messages, temperature, max_tokens_override,
                )
                return future.result(timeout=hard_timeout)
        except FuturesTimeoutError:
            print(f"    Attempt {attempt} timed out after {hard_timeout}s")
            if attempt >= max_attempts:
                print(f"    Hard timeout after {max_attempts} attempts")
                return None
            time.sleep(5)
        except Exception as e:
            is_rate_limit = "429" in str(e) or "RateLimit" in type(e).__name__
            if is_rate_limit and attempt < 5:
                max_attempts = max(max_attempts, 5)
                wait = min(10 * (2 ** (attempt - 1)), 60)
                print(f"    Attempt {attempt} rate-limited, retrying in {wait}s...")
                time.sleep(wait)
            elif attempt < max_attempts:
                print(f"    Attempt {attempt} failed ({type(e).__name__}), retrying in 5s...")
                time.sleep(5)
            else:
                print(f"    API error after {max_attempts} attempts: {e}")
                return None


def generate_model_response(model_config, clients, system_prompt, user_prompt,
                            temperature=None, max_tokens_override=None):
    """Generate a response with retry on failure and hard Python-level timeout."""
    hard_timeout = REQUEST_TIMEOUT + 30
    max_attempts = MAX_RETRIES
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    _call_model, model_config, clients, system_prompt, user_prompt,
                    temperature, max_tokens_override,
                )
                return future.result(timeout=hard_timeout)
        except FuturesTimeoutError:
            print(f"    Attempt {attempt} timed out after {hard_timeout}s")
            if attempt >= max_attempts:
                print(f"    Hard timeout after {max_attempts} attempts")
                return None
            time.sleep(5)
        except Exception as e:
            is_rate_limit = "429" in str(e) or "RateLimit" in type(e).__name__
            if is_rate_limit and attempt < 5:
                max_attempts = max(max_attempts, 5)
                wait = min(10 * (2 ** (attempt - 1)), 60)
                print(f"    Attempt {attempt} rate-limited, retrying in {wait}s...")
                time.sleep(wait)
            elif attempt < max_attempts:
                print(f"    Attempt {attempt} failed ({type(e).__name__}), retrying in 5s...")
                time.sleep(5)
            else:
                print(f"    API error after {max_attempts} attempts: {e}")
                return None
