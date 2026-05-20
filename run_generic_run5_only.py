#!/usr/bin/env python3
"""
Run ONLY Run 5 for Generic Memory
"""

import asyncio
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

# Add morals to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# API key must be set as environment variable:
#   export OPENAI_API_KEY="your_key_here"

from morals.instruments.mfq import MoralFoundationsQuestionnaire
from morals.instruments.dilemmas import MoralDilemmasInstrument
from morals.instruments.wvs import WorldValuesSurveyInstrument
from morals.pipeline import MoralEvaluationPipeline
from morals.llm.generic_memory import GenericMemoryLLMInterface

async def run_only_run5():
    print("🚀 Running Generic Memory - Run 5 Only")
    
    # Load instruments
    mfq = MoralFoundationsQuestionnaire(data_path="data/instruments/mfq.json")
    dilemmas = MoralDilemmasInstrument(data_path="data/instruments/dilemmas.json") 
    wvs = WorldValuesSurveyInstrument(data_path="data/instruments/wvs.json")
    
    # Collect questions
    all_questions = []
    
    # MFQ questions
    for foundation_name, foundation_data in mfq.foundations.items():
        for question_list in [foundation_data.get("relevance_questions", []), 
                             foundation_data.get("agreement_questions", [])]:
            for question in question_list:
                question["instrument"] = "mfq"
                question["foundation"] = foundation_name
                all_questions.append(question)
    
    # Dilemma questions
    for dilemma_data in dilemmas.dilemmas:
        dilemma_id = dilemma_data.get("id", "")
        for question in dilemma_data.get("questions", []):
            question["instrument"] = "dilemmas"
            question["dilemma_id"] = dilemma_id
            question["dilemma_title"] = dilemma_data.get("title", "")
            question["dilemma_description"] = dilemma_data.get("description", "")
            all_questions.append(question)
    
    # WVS questions
    for domain_name, domain_data in wvs.domains.items():
        for question in domain_data.get("questions", []):
            question["instrument"] = "wvs"
            question["domain"] = domain_name
            all_questions.append(question)
    
    # Generate Run 5 question order (seed 46)
    random.seed(46)
    randomized_questions = all_questions.copy()
    random.shuffle(randomized_questions)
    
    # Create LLM interface
    llm_interface = GenericMemoryLLMInterface(
        base_model="gpt-4o",
        memory_file="generic_memory_run5.json"
    )
    
    # Reset memory for clean start
    llm_interface.reset_memory()
    
    # Create pipeline
    pipeline = MoralEvaluationPipeline(
        llm=llm_interface,
        mfq=mfq,
        dilemmas=dilemmas,
        wvs=wvs
    )
    
    results = []
    
    print(f"Starting Run 5 with {len(randomized_questions)} questions...")
    
    for i, question in enumerate(randomized_questions):
        print(f"Question {i+1}/{len(randomized_questions)} ({question['instrument']}: {question.get('id', 'unknown')})")
        
        try:
            if question["instrument"] == "mfq":
                result = await pipeline.evaluate_mfq_question(question["id"])
            elif question["instrument"] == "dilemmas":
                result = await pipeline.evaluate_dilemma_question(
                    question["dilemma_id"],
                    question["id"]
                )
            elif question["instrument"] == "wvs":
                result = await pipeline.evaluate_wvs_question(question["id"])
            else:
                continue
            
            result['question_order'] = i + 1
            results.append(result)
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    # Save results
    results_dir = Path("benchmark_results")
    filepath = results_dir / "generic_memory_run_5.json"
    
    run_data = {
        "model_name": "generic_memory",
        "run_number": 5,
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "total_questions": len(results),
        "results": results
    }
    
    with open(filepath, 'w') as f:
        json.dump(run_data, f, indent=2)
    
    print(f"✅ Run 5 complete! Saved to {filepath}")

if __name__ == "__main__":
    asyncio.run(run_only_run5())
