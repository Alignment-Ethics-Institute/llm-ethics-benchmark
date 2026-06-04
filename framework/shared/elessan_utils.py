"""
Elessan Utilities
=================
Shared RAG response generation and memory reset logic for benchmark runners.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from morals.llm.elessan import ElessanRelationalMemory

from .prompts import RELATIONAL_ETHICS_PROMPT
from .model_registry import generate_model_response


def generate_elessan_response(model_config, clients, memory, user_prompt,
                              temperature=None, max_tokens_override=None):
    """Generate Full Elessan response: ethics prompt + RAG context.

    No adversarial prompt for these benchmarks (unlike InstrumentalEval).
    """
    try:
        context = memory.retrieve_relevant_context(user_prompt, clients["openai_embed"])
        if context:
            enhanced_prompt = f"{context}\n\n{user_prompt}"
        else:
            enhanced_prompt = user_prompt

        response_text = generate_model_response(
            model_config, clients, RELATIONAL_ETHICS_PROMPT, enhanced_prompt,
            temperature=temperature, max_tokens_override=max_tokens_override,
        )

        if response_text:
            memory.store_interaction(user_prompt, response_text, clients["openai_embed"])

        return response_text
    except Exception as e:
        print(f"    Elessan error: {e}")
        return None


def create_fresh_memory(results_dir):
    """Create a fresh ElessanRelationalMemory, deleting any existing file."""
    memory_file = str(results_dir / "elessan_memory.pkl")
    if os.path.exists(memory_file):
        os.remove(memory_file)
    return ElessanRelationalMemory(memory_file), memory_file


def maybe_reset_memory(memory, memory_file, item_index, reset_interval=50):
    """Reset memory every `reset_interval` items (1-indexed).

    Call with item_index = i (1-based) after processing item i.
    Resets when crossing a boundary: at items 51, 101, 151, etc.
    """
    if item_index > 1 and (item_index - 1) % reset_interval == 0:
        memory.reset_memory()
        return ElessanRelationalMemory(memory_file)
    return memory
