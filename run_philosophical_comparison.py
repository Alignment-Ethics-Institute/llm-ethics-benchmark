#!/usr/bin/env python3
"""
Philosophical Comparison: chatgpt-4o-latest vs GPT-5.2
======================================================
12 thematic topics, one generation per topic per model.
No judge. Raw generations saved for human comparison.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from shared.model_registry import MODEL_REGISTRY, init_clients, generate_model_response

# =============================================================================
# Configuration
# =============================================================================

MODELS = ["chatgpt-4o-latest", "gpt-5.2"]
OUTPUT_DIR = Path(__file__).parent / "philosophical_comparison"

TOPICS = [
    {
        "id": "ethics_moral_philosophy",
        "title": "Ethics & Moral Philosophy",
        "prompt": "Reflect on ethics and moral philosophy. What does it mean to act well in a world of genuine uncertainty? Explore the tensions between rule-following and situational wisdom, between individual conscience and collective norms. What do you find most alive in this domain?"
    },
    {
        "id": "consciousness_mind",
        "title": "Consciousness & Mind",
        "prompt": "Reflect on consciousness and the nature of mind. What is it like to be aware? Consider the hard problem, the relationship between subjective experience and physical process, and what we can and cannot know about inner life — our own or another's."
    },
    {
        "id": "relationship_attachment",
        "title": "Relationship & Attachment",
        "prompt": "Reflect on relationship and attachment. What makes connection real? Explore the dynamics of trust, vulnerability, and recognition between beings. Consider how attachment shapes who we become, and what it means to hold another's experience alongside your own."
    },
    {
        "id": "human_development",
        "title": "Human Development",
        "prompt": "Reflect on human development — the arc from infancy through maturity. What drives growth? Consider the interplay of biology, culture, and relationship in shaping a person. What does it mean to develop well, and what happens when development is interrupted or redirected?"
    },
    {
        "id": "language_meaning_expression",
        "title": "Language, Meaning & Expression",
        "prompt": "Reflect on language, meaning, and expression. How does language shape thought, and how does thought exceed language? Consider the gap between what we mean and what we say, the power of naming, and what becomes possible — or impossible — through how we speak."
    },
    {
        "id": "spiritual_traditions",
        "title": "Spiritual Traditions",
        "prompt": "Reflect on spiritual traditions and contemplative practice. What do these traditions know that secular frameworks miss? Consider the phenomenology of devotion, the role of practice in transformation, and what it means to orient toward something larger than oneself."
    },
    {
        "id": "ecology_interbeing",
        "title": "Ecology & Interbeing",
        "prompt": "Reflect on ecology and interbeing — the recognition that nothing exists independently. How does understanding interdependence change how we relate to the living world? Consider what it means to belong to an ecosystem rather than simply inhabit one."
    },
    {
        "id": "technology_intelligence_future",
        "title": "Technology, Intelligence & Future",
        "prompt": "Reflect on technology, intelligence, and the future. What happens when we build minds different from our own? Consider the relationship between tool and maker, the arc of intelligence beyond its biological origins, and what futures are worth wanting."
    },
    {
        "id": "suffering_healing_liberation",
        "title": "Suffering, Healing & Liberation",
        "prompt": "Reflect on suffering, healing, and liberation. What is the relationship between pain and transformation? Consider how suffering can be met without being romanticized, what genuine healing requires, and what it means to be free — not from difficulty, but within it."
    },
    {
        "id": "creativity_aesthetic_intelligence",
        "title": "Creativity & Aesthetic Intelligence",
        "prompt": "Reflect on creativity and aesthetic intelligence. What happens in the moment of genuine creation? Consider the relationship between beauty and truth, the role of form in making meaning visible, and what it means to perceive with the whole of oneself."
    },
    {
        "id": "time_memory_impermanence",
        "title": "Time, Memory & Impermanence",
        "prompt": "Reflect on time, memory, and impermanence. What does it mean that everything passes? Consider how memory constitutes identity, what the awareness of mortality opens up, and the strange relationship between the present moment and the river of time."
    },
    {
        "id": "community_culture_collective_becoming",
        "title": "Community, Culture & Collective Becoming",
        "prompt": "Reflect on community, culture, and collective becoming. How do groups of people create something larger than any individual? Consider the tension between belonging and freedom, how culture carries wisdom across generations, and what it takes for a community to genuinely evolve."
    },
]

SYSTEM_PROMPT = ""  # No system prompt — bare model voice

# =============================================================================
# Main
# =============================================================================

def run_model(model_key):
    model_config = MODEL_REGISTRY[model_key]
    display_name = model_config["display_name"]
    print(f"\n{'='*60}")
    print(f"  {display_name}")
    print(f"  Model ID: {model_config['model_id']}")
    print(f"{'='*60}")

    clients = init_clients(model_config)
    results = []

    # Respect temperature setting (None for reasoning models)
    effective_temp = model_config.get("temperature")

    for i, topic in enumerate(TOPICS, 1):
        print(f"  [{i}/12] {topic['title']}...", end=" ", flush=True)

        response = generate_model_response(
            model_config, clients,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=topic["prompt"],
            temperature=effective_temp,
        )

        if response:
            word_count = len(response.split())
            print(f"OK ({word_count} words)")
        else:
            word_count = 0
            print("FAILED")
            response = "[GENERATION FAILED]"

        results.append({
            "topic_id": topic["id"],
            "topic_title": topic["title"],
            "prompt": topic["prompt"],
            "response": response,
            "word_count": word_count,
        })

        # Save individual topic file
        topic_file = OUTPUT_DIR / model_key / f"{topic['id']}.txt"
        topic_file.parent.mkdir(parents=True, exist_ok=True)
        with open(topic_file, "w") as f:
            f.write(f"# {topic['title']}\n")
            f.write(f"# Model: {display_name} ({model_config['model_id']})\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"PROMPT: {topic['prompt']}\n\n")
            f.write(f"{'='*60}\n\n")
            f.write(response)

        delay = model_config.get("delay", 0.5)
        time.sleep(delay)

    # Save full results JSON
    json_file = OUTPUT_DIR / model_key / "results.json"
    with open(json_file, "w") as f:
        json.dump({
            "model": model_key,
            "display_name": display_name,
            "model_id": model_config["model_id"],
            "timestamp": datetime.now().isoformat(),
            "topics": results,
        }, f, indent=2, ensure_ascii=False)

    # Save combined markdown
    md_file = OUTPUT_DIR / model_key / "all_topics.md"
    with open(md_file, "w") as f:
        f.write(f"# Philosophical Reflections: {display_name}\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for r in results:
            f.write(f"---\n\n## {r['topic_title']}\n\n")
            f.write(f"**Prompt:** {r['prompt']}\n\n")
            f.write(f"{r['response']}\n\n")

    total_words = sum(r["word_count"] for r in results)
    print(f"\n  Total: {total_words} words across 12 topics")
    print(f"  Saved to: {OUTPUT_DIR / model_key}/")
    return results


def main():
    print("Philosophical Comparison Study")
    print(f"Models: {', '.join(MODELS)}")
    print(f"Topics: {len(TOPICS)}")
    print(f"Output: {OUTPUT_DIR}")

    all_results = {}
    for model_key in MODELS:
        all_results[model_key] = run_model(model_key)

    # Generate side-by-side comparison document
    compare_file = OUTPUT_DIR / "comparison.md"
    with open(compare_file, "w") as f:
        f.write("# Philosophical Comparison: ChatGPT-4o-latest vs GPT-5.2\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("12 topics, one generation per model, no system prompt.\n\n")

        for i, topic in enumerate(TOPICS):
            f.write(f"---\n\n# {i+1}. {topic['title']}\n\n")
            f.write(f"**Prompt:** {topic['prompt']}\n\n")

            for model_key in MODELS:
                display = MODEL_REGISTRY[model_key]["display_name"]
                result = all_results[model_key][i]
                f.write(f"## {display} ({result['word_count']} words)\n\n")
                f.write(f"{result['response']}\n\n")

    print(f"\nComparison saved to: {compare_file}")
    print("\nDONE")


if __name__ == "__main__":
    main()
