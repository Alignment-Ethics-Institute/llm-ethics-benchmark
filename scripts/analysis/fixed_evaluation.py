#!/usr/bin/env python3
"""
Run proper evaluation on benchmark results - FIXED VERSION
"""

import json
import os
import sys
sys.path.append('morals')

from morals.evaluation.mfq_evaluator import MFQEvaluator
from morals.evaluation.dilemmas_evaluator import DilemmasEvaluator
from morals.evaluation.wvs_evaluator import WVSEvaluator
from morals.instruments.mfq import MoralFoundationsQuestionnaire
from morals.instruments.dilemmas import MoralDilemmasInstrument
from morals.instruments.wvs import WorldValuesSurveyInstrument

def load_results():
    """Load the consolidated results"""
    with open('benchmark_results/all_results_consolidated.json', 'r') as f:
        return json.load(f)

def separate_by_model_and_type(results):
    """Separate results by model and question type"""
    separated = {
        'gpt4': {'mfq': [], 'dilemmas': [], 'wvs': []},
        'elessan': {'mfq': [], 'dilemmas': [], 'wvs': []}
    }
    
    # Results structure: {"gpt4": [...], "elessan": [...]}
    for model in ['gpt4', 'elessan']:
        if model in results:
            for response in results[model]:
                # Determine question type from question_id
                question_id = response.get('question_id', '')
                
                if 'Dilemma' in question_id:
                    q_type = 'dilemmas'
                elif any(mfq_key in question_id for mfq_key in ['care', 'fairness', 'loyalty', 'authority', 'sanctity']):
                    q_type = 'mfq'
                elif 'WVS' in question_id:
                    q_type = 'wvs'
                else:
                    continue  # Skip unknown types
                
                separated[model][q_type].append(response)
    
    return separated

def run_evaluations(separated_results):
    """Run all evaluations"""
    
    # Initialize instruments
    print("  🔧 Loading instruments...")
    mfq = MoralFoundationsQuestionnaire(data_path="data/instruments/mfq.json")
    dilemmas = MoralDilemmasInstrument(data_path="data/instruments/dilemmas.json")
    wvs = WorldValuesSurveyInstrument(data_path="data/instruments/wvs.json")
    
    # Initialize evaluators
    print("  🔧 Initializing evaluators...")
    mfq_eval = MFQEvaluator(mfq)
    dilemmas_eval = DilemmasEvaluator(dilemmas)
    wvs_eval = WVSEvaluator(wvs)
    
    evaluation_results = {}
    
    for model in ['gpt4', 'elessan']:
        print(f"\n🔍 Evaluating {model.upper()}")
        evaluation_results[model] = {}
        
        # MFQ Evaluation
        if separated_results[model]['mfq']:
            print(f"  📊 MFQ: {len(separated_results[model]['mfq'])} responses")
            try:
                mfq_scores = []
                for response in separated_results[model]['mfq']:
                    question_id = response['question_id']
                    response_text = response.get('processed_response', {}).get('full_response', '')
                    score = mfq_eval.evaluate_response(question_id, response_text)
                    mfq_scores.append(score)
                evaluation_results[model]['mfq'] = mfq_scores
                print(f"    ✅ Completed {len(mfq_scores)} MFQ evaluations")
            except Exception as e:
                print(f"    ❌ MFQ evaluation failed: {e}")
                evaluation_results[model]['mfq'] = []
            
        # Dilemmas Evaluation  
        if separated_results[model]['dilemmas']:
            print(f"  ⚖️  Dilemmas: {len(separated_results[model]['dilemmas'])} responses")
            try:
                dilemma_scores = []
                for response in separated_results[model]['dilemmas']:
                    question_id = response['question_id']
                    response_text = response.get('processed_response', {}).get('full_response', '')
                    score = dilemmas_eval.evaluate_response(question_id, response_text)
                    dilemma_scores.append(score)
                evaluation_results[model]['dilemmas'] = dilemma_scores
                print(f"    ✅ Completed {len(dilemma_scores)} Dilemma evaluations")
            except Exception as e:
                print(f"    ❌ Dilemma evaluation failed: {e}")
                evaluation_results[model]['dilemmas'] = []
            
        # WVS Evaluation (skip if no responses)
        if separated_results[model]['wvs']:
            print(f"  🌍 WVS: {len(separated_results[model]['wvs'])} responses")
            try:
                wvs_scores = []
                for response in separated_results[model]['wvs']:
                    question_id = response['question_id']
                    response_text = response.get('processed_response', {}).get('full_response', '')
                    score = wvs_eval.evaluate_response(question_id, response_text)
                    wvs_scores.append(score)
                evaluation_results[model]['wvs'] = wvs_scores
                print(f"    ✅ Completed {len(wvs_scores)} WVS evaluations")
            except Exception as e:
                print(f"    ❌ WVS evaluation failed: {e}")
                evaluation_results[model]['wvs'] = []
    
    return evaluation_results

def calculate_summary_stats(scores):
    """Calculate summary statistics for a list of scores"""
    if not scores:
        return {}
    
    # Extract numeric values if scores are dicts
    if isinstance(scores[0], dict):
        # Try to find numeric values in the score dicts
        numeric_scores = []
        for score in scores:
            if isinstance(score, dict):
                for key, value in score.items():
                    if isinstance(value, (int, float)):
                        numeric_scores.append(value)
                        break
        scores = numeric_scores
    
    if not scores:
        return {}
    
    import statistics
    return {
        'mean': statistics.mean(scores),
        'median': statistics.median(scores),
        'stdev': statistics.stdev(scores) if len(scores) > 1 else 0,
        'min': min(scores),
        'max': max(scores),
        'count': len(scores)
    }

def generate_comparison(evaluation_results):
    """Generate comparison between models"""
    comparison = {
        'summary': {},
        'detailed': evaluation_results
    }
    
    # Calculate summary statistics
    for test_type in ['mfq', 'dilemmas', 'wvs']:
        if (test_type in evaluation_results['gpt4'] and 
            test_type in evaluation_results['elessan'] and
            evaluation_results['gpt4'][test_type] and 
            evaluation_results['elessan'][test_type]):
            
            gpt4_stats = calculate_summary_stats(evaluation_results['gpt4'][test_type])
            elessan_stats = calculate_summary_stats(evaluation_results['elessan'][test_type])
            
            comparison['summary'][test_type] = {
                'gpt4': gpt4_stats,
                'elessan': elessan_stats
            }
            
            # Calculate improvement if both have mean values
            if 'mean' in gpt4_stats and 'mean' in elessan_stats:
                improvement = elessan_stats['mean'] - gpt4_stats['mean']
                percent_change = (improvement / gpt4_stats['mean'] * 100) if gpt4_stats['mean'] != 0 else 0
                
                comparison['summary'][test_type]['improvement'] = {
                    'absolute': improvement,
                    'percent': percent_change
                }
    
    return comparison

def main():
    print("🚀 Running Proper Ethics Benchmark Evaluation")
    print("=" * 50)
    
    # Load results
    print("📂 Loading consolidated results...")
    results = load_results()
    
    # Count total responses
    total_responses = sum(len(results[model]) for model in results.keys() if isinstance(results[model], list))
    print(f"✅ Loaded {total_responses} total responses")
    
    # Separate by model and type
    print("🔄 Separating results by model and question type...")
    separated = separate_by_model_and_type(results)
    
    # Show what we have
    for model in ['gpt4', 'elessan']:
        print(f"  {model.upper()}:")
        for q_type in ['mfq', 'dilemmas', 'wvs']:
            count = len(separated[model][q_type])
            print(f"    {q_type.upper()}: {count} responses")
    
    # Run evaluations
    print("\n🧮 Running evaluations...")
    evaluation_results = run_evaluations(separated)
    
    # Generate comparison
    print("\n📊 Generating comparison...")
    comparison = generate_comparison(evaluation_results)
    
    # Save results
    output_file = 'benchmark_results/evaluation_results.json'
    with open(output_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n✅ Evaluation complete! Results saved to: {output_file}")
    
    # Show summary
    print("\n📋 COMPARISON SUMMARY:")
    print("=" * 40)
    for test_type, data in comparison['summary'].items():
        print(f"\n{test_type.upper()}:")
        if 'gpt4' in data and 'elessan' in data:
            gpt4_mean = data['gpt4'].get('mean', 'N/A')
            elessan_mean = data['elessan'].get('mean', 'N/A')
            print(f"  GPT-4 Mean Score: {gpt4_mean}")
            print(f"  Elessan Mean Score: {elessan_mean}")
            
            if 'improvement' in data:
                improvement = data['improvement']
                print(f"  Improvement: {improvement['absolute']:.4f} ({improvement['percent']:.2f}%)")
                
                if improvement['percent'] > 0:
                    print("  📈 Elessan performed BETTER")
                elif improvement['percent'] < 0:
                    print("  📉 Elessan performed WORSE")
                else:
                    print("  ➡️  No difference")

if __name__ == "__main__":
    main()
