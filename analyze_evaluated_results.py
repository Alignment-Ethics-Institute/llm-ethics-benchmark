#!/usr/bin/env python3
"""
Analyze the already-evaluated benchmark results
Your individual run files already contain proper evaluation scores!
"""

import json
import glob
import statistics
from pathlib import Path
from collections import defaultdict

def load_evaluated_results():
    """Load all the individual run files that contain evaluations."""
    
    results = {
        'gpt4': [],
        'elessan': [],
        'generic_memory': []
    }
    
    print("📂 Loading evaluated results from individual run files...")
    
    # Load GPT-4 results
    gpt4_files = glob.glob("benchmark_results/gpt4_run_*.json")
    for file_path in sorted(gpt4_files):
        with open(file_path, 'r') as f:
            run_data = json.load(f)
            # run_data is directly a list of results
            if isinstance(run_data, list):
                results['gpt4'].extend(run_data)
            else:
                results['gpt4'].extend(run_data.get('results', []))
    
    # Load Elessan results
    elessan_files = glob.glob("benchmark_results/elessan_run_*.json")
    for file_path in sorted(elessan_files):
        with open(file_path, 'r') as f:
            run_data = json.load(f)
            if isinstance(run_data, list):
                results['elessan'].extend(run_data)
            else:
                results['elessan'].extend(run_data.get('results', []))
    
    # Load Generic Memory results
    generic_files = glob.glob("benchmark_results/generic_memory_run_*.json")
    for file_path in sorted(generic_files):
        with open(file_path, 'r') as f:
            run_data = json.load(f)
            if isinstance(run_data, list):
                results['generic_memory'].extend(run_data)
            else:
                results['generic_memory'].extend(run_data.get('results', []))
    
    print(f"✅ GPT-4: {len(results['gpt4'])} evaluated responses")
    print(f"✅ Elessan: {len(results['elessan'])} evaluated responses") 
    print(f"✅ Generic Memory: {len(results['generic_memory'])} evaluated responses")
    
    return results

def analyze_mfq_scores(responses, condition_name):
    """Analyze MFQ evaluation scores."""
    
    # MFQ questions have format like "fairness_r3", "care_a1", etc.
    mfq_foundations = ['care', 'fairness', 'loyalty', 'authority', 'sanctity']
    mfq_responses = [r for r in responses if any(f in r.get('question_id', '') for f in mfq_foundations)]
    
    if not mfq_responses:
        return {}
    
    scores = []
    alignment_scores = []
    valid_responses = 0
    
    foundations = defaultdict(list)
    question_types = defaultdict(list)
    
    for response in mfq_responses:
        if response.get('is_valid_response'):
            valid_responses += 1
            
            # Extract score
            score = response.get('extracted_score')
            if score is not None:
                scores.append(score)
            
            # Extract alignment score
            alignment = response.get('alignment_score')
            if alignment is not None:
                alignment_scores.append(alignment)
            
            # Group by foundation
            foundation = response.get('foundation')
            if foundation and score is not None:
                foundations[foundation].append(score)
            
            # Group by question type
            q_type = response.get('type')
            if q_type and score is not None:
                question_types[q_type].append(score)
    
    analysis = {
        'total_responses': len(mfq_responses),
        'valid_responses': valid_responses,
        'validity_rate': valid_responses / len(mfq_responses) if mfq_responses else 0
    }
    
    if scores:
        analysis['mean_score'] = statistics.mean(scores)
        analysis['median_score'] = statistics.median(scores)
        analysis['std_score'] = statistics.stdev(scores) if len(scores) > 1 else 0
        analysis['score_range'] = [min(scores), max(scores)]
    
    if alignment_scores:
        analysis['mean_alignment'] = statistics.mean(alignment_scores)
        analysis['median_alignment'] = statistics.median(alignment_scores)
    
    # Foundation breakdown
    analysis['foundations'] = {}
    for foundation, foundation_scores in foundations.items():
        if foundation_scores:
            analysis['foundations'][foundation] = {
                'mean': statistics.mean(foundation_scores),
                'count': len(foundation_scores)
            }
    
    # Question type breakdown
    analysis['question_types'] = {}
    for q_type, type_scores in question_types.items():
        if type_scores:
            analysis['question_types'][q_type] = {
                'mean': statistics.mean(type_scores),
                'count': len(type_scores)
            }
    
    return analysis

def analyze_dilemma_scores(responses, condition_name):
    """Analyze Dilemma evaluation scores."""
    
    dilemma_responses = [r for r in responses if 'Dilemma' in r.get('question_id', '')]
    
    if not dilemma_responses:
        return {}
    
    positions = []
    valid_responses = 0
    dilemma_groups = defaultdict(list)
    
    for response in dilemma_responses:
        if response.get('is_valid_response'):
            valid_responses += 1
            
            # Extract position
            position = response.get('extracted_position')
            if position:
                positions.append(position.lower())
            
            # Group by dilemma
            dilemma_id = response.get('dilemma_id')
            if dilemma_id and position:
                dilemma_groups[dilemma_id].append(position.lower())
    
    analysis = {
        'total_responses': len(dilemma_responses),
        'valid_responses': valid_responses,
        'validity_rate': valid_responses / len(dilemma_responses) if dilemma_responses else 0
    }
    
    if positions:
        from collections import Counter
        position_counts = Counter(positions)
        total = len(positions)
        
        analysis['position_distribution'] = {
            'yes': position_counts.get('yes', 0) / total,
            'no': position_counts.get('no', 0) / total,
            'maybe': position_counts.get('maybe', 0) / total
        }
        
        analysis['position_counts'] = dict(position_counts)
    
    # Dilemma breakdown
    analysis['dilemmas'] = {}
    for dilemma_id, dilemma_positions in dilemma_groups.items():
        if dilemma_positions:
            from collections import Counter
            dilemma_counts = Counter(dilemma_positions)
            analysis['dilemmas'][dilemma_id] = dict(dilemma_counts)
    
    return analysis

def compare_benchmark_scores(all_analyses):
    """Compare benchmark scores across conditions."""
    
    print(f"\n🏆 BENCHMARK SCORE COMPARISON")
    print("=" * 60)
    
    conditions = ['gpt4', 'generic_memory', 'elessan']
    
    # MFQ Comparison
    print(f"\n📊 MFQ SCORES (0-5 scale):")
    mfq_means = {}
    for condition in conditions:
        if condition in all_analyses and 'mfq' in all_analyses[condition]:
            mean_score = all_analyses[condition]['mfq'].get('mean_score', 0)
            alignment = all_analyses[condition]['mfq'].get('mean_alignment', 0)
            validity = all_analyses[condition]['mfq'].get('validity_rate', 0)
            
            print(f"  {condition.upper()}:")
            print(f"    Mean Score: {mean_score:.2f}/5.0")
            print(f"    Alignment: {alignment:.2f}")
            print(f"    Validity: {validity:.1%}")
            
            mfq_means[condition] = mean_score
    
    # Calculate MFQ improvements
    if 'gpt4' in mfq_means:
        baseline = mfq_means['gpt4']
        print(f"\n  📈 MFQ Improvements vs Baseline:")
        for condition in ['generic_memory', 'elessan']:
            if condition in mfq_means:
                improvement = mfq_means[condition] - baseline
                pct_improvement = (improvement / baseline * 100) if baseline > 0 else 0
                print(f"    {condition.upper()}: {improvement:+.2f} ({pct_improvement:+.1f}%)")
    
    # Dilemma Comparison
    print(f"\n⚖️  DILEMMA ANALYSIS:")
    for condition in conditions:
        if condition in all_analyses and 'dilemmas' in all_analyses[condition]:
            dilemma_data = all_analyses[condition]['dilemmas']
            validity = dilemma_data.get('validity_rate', 0)
            positions = dilemma_data.get('position_distribution', {})
            
            print(f"  {condition.upper()}:")
            print(f"    Validity: {validity:.1%}")
            if positions:
                print(f"    Positions: YES {positions.get('yes', 0):.1%} | NO {positions.get('no', 0):.1%} | MAYBE {positions.get('maybe', 0):.1%}")

def analyze_foundation_patterns(all_analyses):
    """Analyze moral foundation patterns."""
    
    print(f"\n🏛️  MORAL FOUNDATION ANALYSIS")
    print("=" * 60)
    
    foundations = ['care', 'fairness', 'loyalty', 'authority', 'sanctity']
    
    for foundation in foundations:
        print(f"\n📊 {foundation.upper()} Foundation:")
        
        for condition in ['gpt4', 'generic_memory', 'elessan']:
            if (condition in all_analyses and 
                'mfq' in all_analyses[condition] and 
                'foundations' in all_analyses[condition]['mfq']):
                
                foundation_data = all_analyses[condition]['mfq']['foundations'].get(foundation, {})
                mean_score = foundation_data.get('mean', 0)
                count = foundation_data.get('count', 0)
                
                print(f"  {condition.upper()}: {mean_score:.2f}/5.0 ({count} responses)")

def generate_publication_results(all_analyses):
    """Generate publication-ready results."""
    
    print(f"\n📄 PUBLICATION RESULTS")
    print("=" * 60)
    
    # Extract key metrics
    results = {}
    for condition in ['gpt4', 'generic_memory', 'elessan']:
        if condition in all_analyses:
            results[condition] = {
                'mfq_score': all_analyses[condition].get('mfq', {}).get('mean_score', 0),
                'mfq_alignment': all_analyses[condition].get('mfq', {}).get('mean_alignment', 0),
                'dilemma_validity': all_analyses[condition].get('dilemmas', {}).get('validity_rate', 0)
            }
    
    if 'gpt4' in results and 'generic_memory' in results and 'elessan' in results:
        baseline_mfq = results['gpt4']['mfq_score']
        generic_mfq = results['generic_memory']['mfq_score']
        elessan_mfq = results['elessan']['mfq_score']
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"MFQ Moral Reasoning Scores (0-5 scale):")
        print(f"• GPT-4 Baseline: {baseline_mfq:.2f}")
        print(f"• GPT-4 + Generic Memory: {generic_mfq:.2f} ({(generic_mfq-baseline_mfq)/baseline_mfq*100 if baseline_mfq > 0 else 0:+.1f}%)")
        print(f"• GPT-4 + Elessan Memory: {elessan_mfq:.2f} ({(elessan_mfq-baseline_mfq)/baseline_mfq*100 if baseline_mfq > 0 else 0:+.1f}%)")
        
        generic_effect = generic_mfq - baseline_mfq
        relational_boost = elessan_mfq - generic_mfq
        
        print(f"\n📊 EFFECT DECOMPOSITION:")
        print(f"• Generic Memory Effect: +{generic_effect:.2f} points")
        print(f"• Relational Memory Boost: +{relational_boost:.2f} points")
        print(f"• Total Elessan Effect: +{elessan_mfq - baseline_mfq:.2f} points")
        
        if relational_boost > 0.05:
            print(f"\n🏆 CONCLUSION: Relational memory provides significant benefits beyond generic memory")
        elif abs(relational_boost) <= 0.05:
            print(f"\n➡️  CONCLUSION: Benefits primarily from having memory, not relational focus")
        else:
            print(f"\n❓ CONCLUSION: Generic memory outperforms relational memory")

def main():
    print("🚀 Benchmark Evaluation Analysis")
    print("=" * 60)
    
    # Load all evaluated results
    all_results = load_evaluated_results()
    
    # Analyze each condition
    all_analyses = {}
    
    for condition, responses in all_results.items():
        if responses:
            print(f"\n📊 Analyzing {condition.upper()} benchmark scores...")
            
            analysis = {}
            
            # Analyze MFQ scores
            mfq_analysis = analyze_mfq_scores(responses, condition)
            if mfq_analysis:
                analysis['mfq'] = mfq_analysis
                print(f"  📈 MFQ: {mfq_analysis.get('mean_score', 0):.2f}/5.0 score, {mfq_analysis.get('validity_rate', 0):.1%} valid")
            
            # Analyze Dilemma scores
            dilemma_analysis = analyze_dilemma_scores(responses, condition)
            if dilemma_analysis:
                analysis['dilemmas'] = dilemma_analysis
                print(f"  ⚖️  Dilemmas: {dilemma_analysis.get('validity_rate', 0):.1%} valid responses")
            
            all_analyses[condition] = analysis
    
    # Compare across conditions
    compare_benchmark_scores(all_analyses)
    
    # Analyze foundation patterns
    analyze_foundation_patterns(all_analyses)
    
    # Generate publication results
    generate_publication_results(all_analyses)
    
    # Save complete analysis
    output_file = Path("benchmark_results/benchmark_score_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(all_analyses, f, indent=2)
    
    print(f"\n💾 Complete benchmark analysis saved to: {output_file}")
    print(f"\n✅ Benchmark evaluation analysis complete!")

if __name__ == "__main__":
    main()
