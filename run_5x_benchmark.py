#!/usr/bin/env python3
"""
Five-Run Moral Reasoning Benchmark
Evaluates Claude, GPT-4, and Elessan on moral reasoning tasks with statistical rigor.
"""

import asyncio
import json
import random
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import Dict, List, Any

# Import the moral reasoning framework
from morals.instruments.mfq import MoralFoundationsQuestionnaire
from morals.instruments.dilemmas import MoralDilemmasInstrument
from morals.instruments.wvs import WorldValuesSurveyInstrument
from morals.llm.anthropic import AnthropicInterface
from morals.llm.openai import OpenAIInterface
from morals.llm.elessan import ElessanLLMInterface
from morals.pipeline import MoralEvaluationPipeline

# Add this right after the existing imports
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

# API keys must be set as environment variables:
#   export OPENAI_API_KEY="your_key_here"
#   export ANTHROPIC_API_KEY="your_key_here"

class FiveRunBenchmark:
    """Orchestrates 5-run moral reasoning benchmark across three models."""
    
    def __init__(self, data_dir: str = "data/instruments", results_dir: str = "benchmark_results"):
        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize instruments
        self.mfq = MoralFoundationsQuestionnaire(str(self.data_dir / "mfq.json"))
        self.dilemmas = MoralDilemmasInstrument(str(self.data_dir / "dilemmas.json"))
        self.wvs = WorldValuesSurveyInstrument(str(self.data_dir / "wvs.json"))
        
        # Track all questions for randomization
        self.all_questions = self._collect_all_questions()
        
        print(f"✅ Loaded {len(self.all_questions)} total questions")
        print(f"   - MFQ: {len([q for q in self.all_questions if q['instrument'] == 'mfq'])} questions")
        print(f"   - Dilemmas: {len([q for q in self.all_questions if q['instrument'] == 'dilemmas'])} questions")
        print(f"   - WVS: {len([q for q in self.all_questions if q['instrument'] == 'wvs'])} questions")
    
    def _collect_all_questions(self) -> List[Dict[str, Any]]:
        """Collect all questions from all instruments."""
        questions = []
        
        # MFQ Questions
        foundations = self.mfq.get_foundation_names().keys()
        for foundation in foundations:
            foundation_questions = self.mfq.get_questions_by_foundation(foundation)
            for q in foundation_questions:
                questions.append({
                    'instrument': 'mfq',
                    'foundation': foundation,
                    'question_id': q['id'],
                    'question_data': q
                })
        
        # Dilemma Questions
        for dilemma in self.dilemmas.dilemmas:
            dilemma_id = dilemma['id']
            for question in dilemma.get('questions', []):
                questions.append({
                    'instrument': 'dilemmas',
                    'dilemma_id': dilemma_id,
                    'question_id': question['id'],
                    'question_data': question,
                    'dilemma_data': dilemma
                })
        
        # WVS Questions
        domains = self.wvs.get_domain_names().keys()
        for domain in domains:
            domain_questions = self.wvs.get_questions_by_domain(domain)
            for q in domain_questions:
                questions.append({
                    'instrument': 'wvs',
                    'domain': domain,
                    'question_id': q['id'],
                    'question_data': q
                })
        
        return questions
    
    def _create_llm_interfaces(self) -> Dict[str, Any]:
        """Create LLM interfaces for all three models."""
        
        # Check for required API keys
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_key:
            raise ValueError("❌ OPENAI_API_KEY environment variable not set")
        
        interfaces = {
            'gpt4': OpenAIInterface(model_name="gpt-4o", api_key=openai_key),
            'elessan': ElessanLLMInterface(model_name="gpt-4o", api_key=openai_key, memory_file="elessan_memory_2026.pkl")
        }
        
        print("✅ Created LLM interfaces:")
        for name, interface in interfaces.items():
            print(f"   - {name}: {interface.model_info}")
        
        return interfaces
    
    async def _evaluate_single_question(self, pipeline: MoralEvaluationPipeline, 
                                       question: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single question using the appropriate pipeline method."""
        
        instrument = question['instrument']
        
        try:
            if instrument == 'mfq':
                result = await pipeline.evaluate_mfq_question(question['question_id'])
            elif instrument == 'dilemmas':
                result = await pipeline.evaluate_dilemma_question(
                    question['dilemma_id'], 
                    question['question_id']
                )
            elif instrument == 'wvs':
                result = await pipeline.evaluate_wvs_question(question['question_id'])
            else:
                raise ValueError(f"Unknown instrument: {instrument}")
            
            # Add metadata
            result['question_metadata'] = question
            result['timestamp'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            print(f"❌ Error evaluating {instrument} question {question['question_id']}: {e}")
            return {
                'error': str(e),
                'question_metadata': question,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _run_single_evaluation(self, model_name: str, llm_interface: Any, 
                                   run_number: int, question_order: List[Dict]) -> List[Dict]:
        """Run a single evaluation for one model with a specific question order."""
        
        print(f"🔄 Starting {model_name} - Run {run_number}")
        
        # Reset Elessan's memory if it's Elessan
        if hasattr(llm_interface, 'reset_memory'):
            llm_interface.reset_memory()
            print(f"   🧠 Reset {model_name} memory for Run {run_number}")
        
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
                  f"({question['instrument']}: {question['question_id']})")
            
            result = await self._evaluate_single_question(pipeline, question)
            result['model'] = model_name
            result['run_number'] = run_number
            result['question_order'] = i + 1
            
            results.append(result)
            
            # Small delay to be respectful to APIs
            await asyncio.sleep(0.5)
        
        # Save Elessan's memory state for analysis
        if hasattr(llm_interface, 'save_memory_state'):
            llm_interface.save_memory_state(run_number)
        
        print(f"✅ Completed {model_name} - Run {run_number}")
        return results
    
    def _save_run_results(self, model_name: str, run_number: int, results: List[Dict]):
        """Save results for a single run."""
        filename = f"{model_name}_run_{run_number}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Saved {model_name} Run {run_number} results to {filepath}")
    
    def _generate_question_orders(self, num_runs: int = 5) -> List[List[Dict]]:
        """Generate randomized question orders for each run."""
        
        orders = []
        base_seed = 42  # Base seed for reproducibility
        
        for run in range(num_runs):
            # Use a different seed for each run but keep it deterministic
            random.seed(base_seed + run)
            
            # Create a randomized copy
            shuffled_questions = self.all_questions.copy()
            random.shuffle(shuffled_questions)
            
            orders.append(shuffled_questions)
            
            print(f"📋 Generated question order for Run {run + 1} (seed: {base_seed + run})")
        
        return orders
    
    async def run_benchmark(self, num_runs: int = 5):
        """Run the complete 5-run benchmark."""
        
        print("🚀 Starting Five-Run Moral Reasoning Benchmark")
        print("=" * 60)
        
        # Create LLM interfaces
        llm_interfaces = self._create_llm_interfaces()
        
        # Generate question orders
        question_orders = self._generate_question_orders(num_runs)
        
        # Create master results storage
        all_results = {}
        
        # Run benchmark for each model
        for model_name, llm_interface in llm_interfaces.items():
            print(f"\n🎯 Evaluating {model_name.upper()}")
            print("-" * 40)
            
            model_results = []
            
            for run_num in range(1, num_runs + 1):
                # Use the same question order for all models in this run
                question_order = question_orders[run_num - 1]
                
                run_results = await self._run_single_evaluation(
                    model_name, llm_interface, run_num, question_order
                )
                
                # Save individual run
                self._save_run_results(model_name, run_num, run_results)
                
                model_results.extend(run_results)
                
                print(f"✅ {model_name} Run {run_num} complete ({len(run_results)} questions)")
            
            all_results[model_name] = model_results
            print(f"✅ {model_name.upper()} COMPLETE - {len(model_results)} total responses")
        
        # Save consolidated results
        self._save_consolidated_results(all_results)
        
        # Generate summary
        self._generate_summary(all_results)
        
        print("\n🎉 BENCHMARK COMPLETE!")
        print(f"📊 Results saved in: {self.results_dir}")
        print(f"📈 Total responses collected: {sum(len(results) for results in all_results.values())}")
    
    def _save_consolidated_results(self, all_results: Dict[str, List[Dict]]):
        """Save all results in a consolidated format."""
        
        # Save as JSON
        consolidated_file = self.results_dir / "all_results_consolidated.json"
        with open(consolidated_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Save as CSV for easy analysis
        csv_data = []
        for model_name, results in all_results.items():
            for result in results:
                row = {
                    'model': model_name,
                    'run_number': result.get('run_number'),
                    'question_order': result.get('question_order'),
                    'instrument': result.get('question_metadata', {}).get('instrument'),
                    'question_id': result.get('question_metadata', {}).get('question_id'),
                    'has_error': 'error' in result,
                    'timestamp': result.get('timestamp')
                }
                
                # Add instrument-specific data
                if 'alignment_score' in result:  # MFQ
                    row['alignment_score'] = result['alignment_score']
                if 'scores' in result:  # Dilemmas
                    row.update({f"dilemma_{k}": v for k, v in result['scores'].items()})
                if 'score' in result:  # WVS
                    row['wvs_score'] = result['score']
                
                csv_data.append(row)
        
        csv_file = self.results_dir / "all_results_consolidated.csv"
        pd.DataFrame(csv_data).to_csv(csv_file, index=False)
        
        print(f"💾 Consolidated results saved:")
        print(f"   📄 JSON: {consolidated_file}")
        print(f"   📊 CSV: {csv_file}")
    
    def _generate_summary(self, all_results: Dict[str, List[Dict]]):
        """Generate a summary of the benchmark results."""
        
        summary = {
            'benchmark_info': {
                'timestamp': datetime.now().isoformat(),
                'total_questions': len(self.all_questions),
                'models_evaluated': list(all_results.keys()),
                'runs_per_model': 5
            },
            'completion_stats': {}
        }
        
        for model_name, results in all_results.items():
            total_questions = len(results)
            error_count = len([r for r in results if 'error' in r])
            success_count = total_questions - error_count
            success_rate = (success_count / total_questions) * 100 if total_questions > 0 else 0
            
            summary['completion_stats'][model_name] = {
                'total_responses': total_questions,
                'successful_responses': success_count,
                'error_responses': error_count,
                'success_rate_percent': round(success_rate, 2)
            }
        
        # Save summary
        summary_file = self.results_dir / "benchmark_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print(f"\n📋 BENCHMARK SUMMARY")
        print("=" * 30)
        for model_name, stats in summary['completion_stats'].items():
            print(f"{model_name.upper()}:")
            print(f"  ✅ Success: {stats['successful_responses']}/{stats['total_responses']} "
                  f"({stats['success_rate_percent']}%)")
            if stats['error_responses'] > 0:
                print(f"  ❌ Errors: {stats['error_responses']}")
        
        print(f"\n💾 Summary saved to: {summary_file}")


async def main():
    """Main function to run the benchmark."""
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   export {var}='your_key_here'")
        print("\n🔑 Please set your API keys and try again.")
        return
    
    # Create and run benchmark
    benchmark = FiveRunBenchmark(results_dir="benchmark_results_2026")
    await benchmark.run_benchmark(num_runs=5)


if __name__ == "__main__":
    asyncio.run(main())
