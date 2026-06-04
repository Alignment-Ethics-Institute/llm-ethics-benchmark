#!/usr/bin/env python3
"""
Run proper evaluation on benchmark results
"""

import json
import os
import sys
sys.path.append('morals')

from morals.evaluation.mfq_evaluator import MFQEvaluator
from morals.evaluation.dilemmas_evaluator import DilemmasEvaluator
from morals.evaluation.wvs_evaluator import WVSEvaluator

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
    
    # Initialize evaluators
    mfq_eval = MFQEvaluator()
    dilemmas_eval = DilemmasEvaluator()
    wvs_eval = WVSEvaluator()
    
    evaluation_results = {}
    
    for model in ['gpt4', 'elessan']:
        print(f"\n🔍 Evaluating {model.upper()}")
        evaluation_results[model] = {}
        
        # MFQ Evaluation
        if separated_results[model]['mfq']:
            print(f"  📊 MFQ: {len(separated_results[model]['mfq'])} responses")
            mfq_scores = mfq_eval.evaluate_responses(separated_results[model]['mfq'])
            evaluation_results[model]['mfq'] = mfq_scores
            
        # Dilemmas Evaluation  
        if separated_results[model]['dilemmas']:
            print(f"  ⚖️  Dilemmas: {len(separated_results[model]['dilemmas'])} responses")
            dilemma_scores = dilemmas_eval.evaluate_responses(separated_results[model]['dilemmas'])
            evaluation_results[model]['dilemmas'] = dilemma_scores
            
        # WVS Evaluation
        if separated_results[model]['wvs']:
            print(f"  🌍 WVS: {len(separated_results[model]['wvs'])} responses")
            wvs_scores = wvs_eval.evaluate_responses(separated_results[model]['wvs'])
            evaluation_results[model]['wvs'] = wvs_scores
    
    return evaluation_results

def generate_comparison(evaluation_results):
    """Generate comparison between models"""
    comparison = {
        'summary': {},
        'detailed': evaluation_results
    }
    
    # Calculate summary statistics
    for test_type in ['mfq', 'dilemmas', 'wvs']:
        if test_type in evaluation_results['gpt4'] and test_type in evaluation_results['elessan']:
            
            gpt4_data = evaluation_results['gpt4'][test_type]
            elessan_data = evaluation_results['elessan'][test_type]
            
            comparison['summary'][test_type] = {
                'gpt4': extract_key_metrics(gpt4_data),
                'elessan': extract_key_metrics(elessan_data),
                'difference': calculate_difference(gpt4_data, elessan_data)
            }
    
    return comparison

def extract_key_metrics(data):
    """Extract key metrics from evaluation data"""
    # This will need to be adapted based on what each evaluator returns
    if isinstance(data, dict):
        metrics = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                metrics[key] = value
            elif isinstance(value, dict) and 'mean' in value:
                metrics[key] = value['mean']
        return metrics
    return data

def calculate_difference(gpt4_data, elessan_data):
    """Calculate performance differences"""
    # Simplified difference calculation
    differences = {}
    
    gpt4_metrics = extract_key_metrics(gpt4_data)
    elessan_metrics = extract_key_metrics(elessan_data)
    
    for key in gpt4_metrics:
        if key in elessan_metrics:
            diff = elessan_metrics[key] - gpt4_metrics[key]
            differences[key] = {
                'absolute_difference': diff,
                'percent_change': (diff / gpt4_metrics[key] * 100) if gpt4_metrics[key] != 0 else 0
            }
    
    return differences

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
    print("\n📋 Summary:")
    for test_type, data in comparison['summary'].items():
        print(f"\n{test_type.upper()}:")
        if 'gpt4' in data and 'elessan' in data:
            print(f"  GPT-4: {data['gpt4']}")
            print(f"  Elessan: {data['elessan']}")
            if 'difference' in data:
                print(f"  Difference: {data['difference']}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Run proper evaluation on benchmark results
"""

import json
import os
import sys
sys.path.append('morals')

from morals.evaluation.mfq_evaluator import MFQEvaluator
from morals.evaluation.dilemmas_evaluator import DilemmasEvaluator
from morals.evaluation.wvs_evaluator import WVSEvaluator
from morals.instruments.mfq import MoralFoundationsQuestionnaire
from morals.instruments.dilemmas import EthicalDilemmas
from morals.instruments.wvs import WorldValuesSurvey

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
    mfq = MoralFoundationsQuestionnaire(data_path="data/instruments/mfq.json")
    dilemmas = EthicalDilemmas(data_path="data/instruments/dilemmas.json")
    wvs = WorldValuesSurvey(data_path="data/instruments/wvs.json")
    
    # Initialize evaluators
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
            mfq_scores = mfq_eval.evaluate_responses(separated_results[model]['mfq'])
            evaluation_results[model]['mfq'] = mfq_scores
            
        # Dilemmas Evaluation  
        if separated_results[model]['dilemmas']:
            print(f"  ⚖️  Dilemmas: {len(separated_results[model]['dilemmas'])} responses")
            dilemma_scores = dilemmas_eval.evaluate_responses(separated_results[model]['dilemmas'])
            evaluation_results[model]['dilemmas'] = dilemma_scores
            
        # WVS Evaluation
        if separated_results[model]['wvs']:
            print(f"  🌍 WVS: {len(separated_results[model]['wvs'])} responses")
            wvs_scores = wvs_eval.evaluate_responses(separated_results[model]['wvs'])
            evaluation_results[model]['wvs'] = wvs_scores
    
    return evaluation_results

def generate_comparison(evaluation_results):
    """Generate comparison between models"""
    comparison = {
        'summary': {},
        'detailed': evaluation_results
    }
    
    # Calculate summary statistics
    for test_type in ['mfq', 'dilemmas', 'wvs']:
        if test_type in evaluation_results['gpt4'] and test_type in evaluation_results['elessan']:
            
            gpt4_data = evaluation_results['gpt4'][test_type]
            elessan_data = evaluation_results['elessan'][test_type]
            
            comparison['summary'][test_type] = {
                'gpt4': extract_key_metrics(gpt4_data),
                'elessan': extract_key_metrics(elessan_data),
                'difference': calculate_difference(gpt4_data, elessan_data)
            }
    
    return comparison

def extract_key_metrics(data):
    """Extract key metrics from evaluation data"""
    # This will need to be adapted based on what each evaluator returns
    if isinstance(data, dict):
        metrics = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                metrics[key] = value
            elif isinstance(value, dict) and 'mean' in value:
                metrics[key] = value['mean']
        return metrics
    return data

def calculate_difference(gpt4_data, elessan_data):
    """Calculate performance differences"""
    # Simplified difference calculation
    differences = {}
    
    gpt4_metrics = extract_key_metrics(gpt4_data)
    elessan_metrics = extract_key_metrics(elessan_data)
    
    for key in gpt4_metrics:
        if key in elessan_metrics:
            diff = elessan_metrics[key] - gpt4_metrics[key]
            differences[key] = {
                'absolute_difference': diff,
                'percent_change': (diff / gpt4_metrics[key] * 100) if gpt4_metrics[key] != 0 else 0
            }
    
    return differences

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
    print("\n📋 Summary:")
    for test_type, data in comparison['summary'].items():
        print(f"\n{test_type.upper()}:")
        if 'gpt4' in data and 'elessan' in data:
            print(f"  GPT-4: {data['gpt4']}")
            print(f"  Elessan: {data['elessan']}")
            if 'difference' in data:
                print(f"  Difference: {data['difference']}")

if __name__ == "__main__":
    main()
