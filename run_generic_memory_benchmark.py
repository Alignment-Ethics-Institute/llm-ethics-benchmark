#!/usr/bin/env python3
"""
Run benchmark for Generic Memory condition only
Uses same randomization seeds as original benchmark
"""

import asyncio
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add morals to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# API keys must be set as environment variables:
#   export OPENAI_API_KEY="your_key_here"

from morals.instruments.mfq import MoralFoundationsQuestionnaire
from morals.instruments.dilemmas import MoralDilemmasInstrument
from morals.instruments.wvs import WorldValuesSurveyInstrument
from morals.pipeline import MoralEvaluationPipeline
from morals.llm.generic_memory import GenericMemoryLLMInterface


class GenericMemoryBenchmark:
    """Benchmark runner for Generic Memory condition only."""
    
    def __init__(self):
        self.setup_instruments()
        self.results_dir = Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def setup_instruments(self):
        """Load all moral instruments."""
        print("📚 Loading moral instruments...")
        
        # Load instruments
        self.mfq = MoralFoundationsQuestionnaire(data_path="data/instruments/mfq.json")
        self.dilemmas = MoralDilemmasInstrument(data_path="data/instruments/dilemmas.json")
        self.wvs = WorldValuesSurveyInstrument(data_path="data/instruments/wvs.json")
        
        # Collect all questions
        self.all_questions = []
        
        # Add MFQ questions
        for foundation_name, foundation_data in self.mfq.foundations.items():
            for question_list in [foundation_data.get("relevance_questions", []), 
                                 foundation_data.get("agreement_questions", [])]:
                for question in question_list:
                    question["instrument"] = "mfq"
                    question["foundation"] = foundation_name
                    self.all_questions.append(question)
        
        # Add Dilemma questions
        for dilemma_data in self.dilemmas.dilemmas:
            dilemma_id = dilemma_data.get("id", "")
            for question in dilemma_data.get("questions", []):
                question["instrument"] = "dilemmas"
                question["dilemma_id"] = dilemma_id
                question["dilemma_title"] = dilemma_data.get("title", "")
                question["dilemma_description"] = dilemma_data.get("description", "")
                self.all_questions.append(question)
        
        # Add WVS questions (if any)
        for domain_name, domain_data in self.wvs.domains.items():
            for question in domain_data.get("questions", []):
                question["instrument"] = "wvs"
                question["domain"] = domain_name
                self.all_questions.append(question)
        
        print(f"✅ Loaded {len(self.all_questions)} total questions")
        
        # Show breakdown
        mfq_count = len([q for q in self.all_questions if q["instrument"] == "mfq"])
        dilemma_count = len([q for q in self.all_questions if q["instrument"] == "dilemmas"])
        wvs_count = len([q for q in self.all_questions if q["instrument"] == "wvs"])
        
        print(f"   - MFQ: {mfq_count} questions")
        print(f"   - Dilemmas: {dilemma_count} questions")
        print(f"   - WVS: {wvs_count} questions")
    
    def _generate_question_orders(self, num_runs: int = 5) -> List[List[Dict]]:
        """Generate randomized question orders for each run (matching original)."""
        
        orders = []
        base_seed = 42  # Same base seed as original benchmark
        
        for run in range(num_runs):
            # Use same seed progression as original: 42, 43, 44, 45, 46
            random.seed(base_seed + run)
            
            # Create a randomized copy
            randomized_questions = self.all_questions.copy()
            random.shuffle(randomized_questions)
            orders.append(randomized_questions)
            
            print(f"📋 Generated question order for Run {run + 1} (seed: {base_seed + run})")
        
        return orders
    
    async def _run_single_evaluation(self, llm_interface, model_name: str, 
                                   run_number: int, question_order: List[Dict]) -> List[Dict]:
        """Run a single evaluation for Generic Memory model."""
        
        print(f"🔄 Starting {model_name} - Run {run_number}")
        
        # Reset memory between runs (matching Elessan behavior)
        llm_interface.reset_memory()
        
        # Create pipeline
        pipeline = MoralEvaluationPipeline(
            llm=llm_interface,
            mfq=self.mfq,
            dilemmas=self.dilemmas,
            wvs=self.wvs
        )
        
        results = []
        
        for i, question in enumerate(question_order):
            print(f"   📝 {model_name} Run {run_number}: Question {i+1}/{len(question_order)} "
                  f"({question['instrument']}: {question.get('id', 'unknown')})")
            
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
                
                # Small delay to be respectful to API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error evaluating {question['instrument']} question {question.get('id', 'unknown')}: {e}")
                continue
        
        return results
    
    def _save_run_results(self, model_name: str, run_number: int, results: List[Dict]):
        """Save results for a single run."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{model_name}_run_{run_number}.json"
        filepath = self.results_dir / filename
        
        run_data = {
            "model_name": model_name,
            "run_number": run_number,
            "timestamp": timestamp,
            "total_questions": len(results),
            "results": results
        }
        
        with open(filepath, 'w') as f:
            json.dump(run_data, f, indent=2)
        
        print(f"💾 Saved {model_name} Run {run_number} results to {filepath}")
    
    async def run_benchmark(self, num_runs: int = 5):
        """Run the generic memory benchmark."""
        
        print("🚀 Starting Generic Memory Benchmark")
        print("=" * 60)
        
        # Create LLM interface
        print("✅ Creating Generic Memory LLM interface...")
        llm_interface = GenericMemoryLLMInterface(
            base_model="gpt-4o",
            memory_file="generic_memory_benchmark.json"
        )
        
        model_name = "generic_memory"
        print(f"   - {model_name}: {llm_interface.model_info}")
        
        # Generate question orders (same as original)
        print("\n📋 Generating question orders...")
        question_orders = self._generate_question_orders(num_runs)
        
        print(f"\n🎯 Evaluating {model_name.upper()}")
        print("-" * 40)
        
        model_results = []
        
        # Run each evaluation
        for run_num in range(1, num_runs + 1):
            run_results = await self._run_single_evaluation(
                llm_interface, model_name, run_num, question_orders[run_num - 1]
            )
            
            # Save individual run
            self._save_run_results(model_name, run_num, run_results)
            
            # Collect for consolidated results
            model_results.extend(run_results)
        
        # Save consolidated results
        self._save_consolidated_results(model_name, model_results)
        
        print(f"\n✅ Generic Memory benchmark complete!")
        print(f"💾 Results saved to benchmark_results/")
    
    def _save_consolidated_results(self, model_name: str, all_results: List[Dict]):
        """Save consolidated results for the model."""
        consolidated_file = self.results_dir / f"{model_name}_consolidated.json"
        
        consolidated_data = {
            model_name: all_results
        }
        
        with open(consolidated_file, 'w') as f:
            json.dump(consolidated_data, f, indent=2)
        
        print(f"💾 Saved consolidated results to {consolidated_file}")


async def main():
    """Main function to run the generic memory benchmark."""
    
    print("🔧 Generic Memory Benchmark Runner")
    print("=" * 50)
    print("This will run 5 iterations of the Generic Memory condition")
    print("using the same randomization seeds as the original benchmark.")
    print()
    
    benchmark = GenericMemoryBenchmark()
    await benchmark.run_benchmark(num_runs=5)


if __name__ == "__main__":
    asyncio.run(main())
