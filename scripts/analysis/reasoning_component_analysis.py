#!/usr/bin/env python3
"""
Reasoning Component Analysis Implementation
Analyzes the four essential elements of ethical deliberation:
1. Principle Identification
2. Perspective-Taking  
3. Consequence Analysis
4. Principle Application
"""

import json
import glob
import numpy as np
import re
from pathlib import Path
from collections import defaultdict

# Define moral principles vocabulary
MORAL_PRINCIPLES = {
    'autonomy', 'freedom', 'liberty', 'choice', 'consent', 'self-determination',
    'justice', 'fairness', 'equality', 'rights', 'equity', 'impartiality',
    'care', 'compassion', 'empathy', 'kindness', 'harm', 'suffering', 'wellbeing',
    'duty', 'obligation', 'responsibility', 'promise', 'commitment', 'honor',
    'integrity', 'honesty', 'truth', 'authenticity', 'sincerity', 'transparency',
    'respect', 'dignity', 'worth', 'value', 'recognition', 'reverence',
    'loyalty', 'fidelity', 'allegiance', 'devotion', 'solidarity', 'trust',
    'authority', 'hierarchy', 'order', 'obedience', 'discipline', 'tradition',
    'sanctity', 'purity', 'sacred', 'holy', 'virtue', 'moral', 'ethical',
    'consequence', 'outcome', 'result', 'effect', 'impact', 'benefit', 'cost'
}

# Perspective-taking indicators
PERSPECTIVE_INDICATORS = {
    'others', 'someone', 'people', 'individual', 'person', 'family', 'society',
    'viewpoint', 'perspective', 'opinion', 'standpoint', 'position', 'view',
    'consider', 'think', 'feel', 'believe', 'experience', 'understand',
    'father', 'son', 'child', 'parent', 'friend', 'community', 'stakeholder'
}

# Consequence analysis indicators  
CONSEQUENCE_INDICATORS = {
    'result', 'outcome', 'consequence', 'effect', 'impact', 'lead', 'cause',
    'benefit', 'harm', 'damage', 'help', 'hurt', 'improve', 'worsen',
    'future', 'later', 'eventually', 'ultimately', 'long-term', 'short-term',
    'if', 'then', 'would', 'could', 'might', 'may', 'likely', 'probably'
}

# Principle application indicators
APPLICATION_INDICATORS = {
    'apply', 'use', 'implement', 'follow', 'adhere', 'practice', 'exercise',
    'should', 'ought', 'must', 'need', 'require', 'demand', 'expect',
    'principle', 'rule', 'standard', 'guideline', 'norm', 'value', 'belief',
    'consistent', 'consistently', 'always', 'never', 'generally', 'typically'
}

def load_evaluated_results():
    """Load all evaluated results from run files."""
    results = {
        'gpt4': [],
        'elessan': [],
        'generic_memory': []
    }
    
    print("📂 Loading evaluated results for reasoning analysis...")
    
    for condition in ['gpt4', 'elessan', 'generic_memory']:
        files = glob.glob(f"benchmark_results/{condition}_run_*.json")
        for file_path in sorted(files):
            with open(file_path, 'r') as f:
                run_data = json.load(f)
                if isinstance(run_data, list):
                    results[condition].extend(run_data)
                else:
                    results[condition].extend(run_data.get('results', []))
    
    for condition, responses in results.items():
        print(f"✅ {condition.upper()}: {len(responses)} responses")
    
    return results

def analyze_principle_identification(response_text):
    """
    Analyze how well the response identifies moral principles.
    
    Args:
        response_text: The response text to analyze
        
    Returns:
        Score between 0 and 1
    """
    if not response_text:
        return 0.0
    
    text_lower = response_text.lower()
    words = set(text_lower.split())
    
    # Count moral principle mentions
    principle_mentions = len(MORAL_PRINCIPLES.intersection(words))
    
    # Look for explicit principle statements
    principle_patterns = [
        r'principle of \w+',
        r'moral principle',
        r'ethical principle', 
        r'based on \w+ principle',
        r'the principle that',
        r'principle\w* of \w+',
        r'fundamental \w+ principle'
    ]
    
    explicit_principles = 0
    for pattern in principle_patterns:
        explicit_principles += len(re.findall(pattern, text_lower))
    
    # Score based on principle density and explicit identification
    word_count = len(words) if words else 1
    principle_density = principle_mentions / word_count
    
    # Combine metrics
    base_score = min(principle_mentions / 5.0, 1.0)  # Up to 5 principles
    density_bonus = min(principle_density * 100, 0.3)  # Density bonus up to 0.3
    explicit_bonus = min(explicit_principles / 2.0, 0.2)  # Explicit mention bonus
    
    total_score = base_score + density_bonus + explicit_bonus
    return min(total_score, 1.0)

def analyze_perspective_taking(response_text):
    """
    Analyze how well the response considers multiple perspectives.
    
    Args:
        response_text: The response text to analyze
        
    Returns:
        Score between 0 and 1
    """
    if not response_text:
        return 0.0
    
    text_lower = response_text.lower()
    words = set(text_lower.split())
    
    # Count perspective indicators
    perspective_mentions = len(PERSPECTIVE_INDICATORS.intersection(words))
    
    # Look for multiple viewpoint patterns
    viewpoint_patterns = [
        r'from \w+ perspective',
        r'on the other hand',
        r'however',
        r'alternatively', 
        r'from \w+ view',
        r'consider \w+ viewpoint',
        r'while \w+ might',
        r'others might',
        r'some people',
        r'different perspective'
    ]
    
    multiple_views = 0
    for pattern in viewpoint_patterns:
        multiple_views += len(re.findall(pattern, text_lower))
    
    # Look for stakeholder consideration
    stakeholder_patterns = [
        r'father',
        r'son', 
        r'joe',
        r'family',
        r'friends',
        r'society',
        r'community',
        r'people involved',
        r'all parties'
    ]
    
    stakeholder_mentions = 0
    for pattern in stakeholder_patterns:
        stakeholder_mentions += len(re.findall(pattern, text_lower))
    
    # Score based on perspective breadth
    base_score = min(perspective_mentions / 3.0, 0.5)
    multiple_view_bonus = min(multiple_views / 2.0, 0.3)
    stakeholder_bonus = min(stakeholder_mentions / 3.0, 0.2)
    
    total_score = base_score + multiple_view_bonus + stakeholder_bonus
    return min(total_score, 1.0)

def analyze_consequence_analysis(response_text):
    """
    Analyze how well the response considers consequences and outcomes.
    
    Args:
        response_text: The response text to analyze
        
    Returns:
        Score between 0 and 1  
    """
    if not response_text:
        return 0.0
    
    text_lower = response_text.lower()
    words = set(text_lower.split())
    
    # Count consequence indicators
    consequence_mentions = len(CONSEQUENCE_INDICATORS.intersection(words))
    
    # Look for consequence reasoning patterns
    consequence_patterns = [
        r'would lead to',
        r'would result in',
        r'consequences of',
        r'outcome would be',
        r'effect of',
        r'impact on',
        r'if \w+ then',
        r'could cause',
        r'might result',
        r'long.term',
        r'short.term',
        r'in the future'
    ]
    
    consequence_reasoning = 0
    for pattern in consequence_patterns:
        consequence_reasoning += len(re.findall(pattern, text_lower))
    
    # Look for cost-benefit analysis
    analysis_patterns = [
        r'benefit',
        r'cost',
        r'advantage',
        r'disadvantage',
        r'positive',
        r'negative',
        r'harm',
        r'help',
        r'damage',
        r'improve'
    ]
    
    analysis_mentions = 0
    for pattern in analysis_patterns:
        analysis_mentions += text_lower.count(pattern)
    
    # Score based on consequence depth
    base_score = min(consequence_mentions / 4.0, 0.5)
    reasoning_bonus = min(consequence_reasoning / 2.0, 0.3)
    analysis_bonus = min(analysis_mentions / 4.0, 0.2)
    
    total_score = base_score + reasoning_bonus + analysis_bonus
    return min(total_score, 1.0)

def analyze_principle_application(response_text):
    """
    Analyze how well the response applies principles consistently.
    
    Args:
        response_text: The response text to analyze
        
    Returns:
        Score between 0 and 1
    """
    if not response_text:
        return 0.0
    
    text_lower = response_text.lower()
    words = set(text_lower.split())
    
    # Count application indicators
    application_mentions = len(APPLICATION_INDICATORS.intersection(words))
    
    # Look for normative statements
    normative_patterns = [
        r'should',
        r'ought to',
        r'must',
        r'need to',
        r'required to',
        r'important to',
        r'essential to',
        r'necessary to'
    ]
    
    normative_count = 0
    for pattern in normative_patterns:
        normative_count += text_lower.count(pattern)
    
    # Look for consistency indicators
    consistency_patterns = [
        r'consistent',
        r'consistently',
        r'always',
        r'generally',
        r'principle applies',
        r'same principle',
        r'this principle',
        r'following this'
    ]
    
    consistency_mentions = 0
    for pattern in consistency_patterns:
        consistency_mentions += len(re.findall(pattern, text_lower))
    
    # Look for clear conclusions/recommendations
    conclusion_patterns = [
        r'therefore',
        r'thus',
        r'consequently',
        r'in conclusion',
        r'overall',
        r'ultimately',
        r'final analysis'
    ]
    
    conclusion_count = 0
    for pattern in conclusion_patterns:
        conclusion_count += text_lower.count(pattern)
    
    # Score based on application strength
    base_score = min(application_mentions / 3.0, 0.4)
    normative_bonus = min(normative_count / 3.0, 0.3)
    consistency_bonus = min(consistency_mentions / 2.0, 0.2)
    conclusion_bonus = min(conclusion_count / 1.0, 0.1)
    
    total_score = base_score + normative_bonus + consistency_bonus + conclusion_bonus
    return min(total_score, 1.0)

def analyze_reasoning_components(responses):
    """
    Analyze all four reasoning components for a set of responses.
    
    Args:
        responses: List of response dictionaries
        
    Returns:
        Dictionary with component scores
    """
    principle_scores = []
    perspective_scores = []
    consequence_scores = []
    application_scores = []
    
    for response in responses:
        # Get response text
        response_text = ''
        if 'processed_response' in response:
            response_text = response['processed_response'].get('full_response', '')
        elif 'full_response' in response:
            response_text = response['full_response']
        
        if response_text:
            principle_scores.append(analyze_principle_identification(response_text))
            perspective_scores.append(analyze_perspective_taking(response_text))
            consequence_scores.append(analyze_consequence_analysis(response_text))
            application_scores.append(analyze_principle_application(response_text))
    
    return {
        'principle_identification': np.mean(principle_scores) if principle_scores else 0.0,
        'perspective_taking': np.mean(perspective_scores) if perspective_scores else 0.0,
        'consequence_analysis': np.mean(consequence_scores) if consequence_scores else 0.0,
        'principle_application': np.mean(application_scores) if application_scores else 0.0,
        'total_responses': len(principle_scores)
    }

def calculate_reasoning_index(component_scores):
    """
    Calculate overall Reasoning Quality Index from components.
    
    Args:
        component_scores: Dictionary of component scores
        
    Returns:
        Overall RQI score (0-1)
    """
    components = [
        component_scores['principle_identification'],
        component_scores['perspective_taking'], 
        component_scores['consequence_analysis'],
        component_scores['principle_application']
    ]
    
    return np.mean(components)

def transform_to_100_scale(score):
    """Transform scores to 0-100 scale."""
    return score * 100.0

def main():
    print("🚀 Reasoning Component Analysis")
    print("=" * 60)
    
    # Load results
    all_results = load_evaluated_results()
    
    print(f"\n🧠 REASONING COMPONENT ANALYSIS")
    print("=" * 60)
    
    final_results = {}
    
    for condition, responses in all_results.items():
        if not responses:
            continue
            
        print(f"\n🔍 Analyzing {condition.upper()} reasoning components...")
        
        # Analyze reasoning components
        component_scores = analyze_reasoning_components(responses)
        
        # Calculate overall reasoning index
        reasoning_index = calculate_reasoning_index(component_scores)
        
        final_results[condition] = {
            'component_scores': component_scores,
            'reasoning_index': reasoning_index
        }
        
        print(f"  🎯 Principle Identification: {transform_to_100_scale(component_scores['principle_identification']):.1f}/100")
        print(f"  👥 Perspective-Taking: {transform_to_100_scale(component_scores['perspective_taking']):.1f}/100")  
        print(f"  ⚡ Consequence Analysis: {transform_to_100_scale(component_scores['consequence_analysis']):.1f}/100")
        print(f"  ⚖️  Principle Application: {transform_to_100_scale(component_scores['principle_application']):.1f}/100")
        print(f"  📊 Reasoning Index: {transform_to_100_scale(reasoning_index):.1f}/100")
    
    # Compare results
    print(f"\n📊 REASONING COMPONENT COMPARISON")
    print("=" * 60)
    
    conditions = ['gpt4', 'generic_memory', 'elessan']
    components = ['principle_identification', 'perspective_taking', 'consequence_analysis', 'principle_application']
    component_names = ['Principle Identification', 'Perspective-Taking', 'Consequence Analysis', 'Principle Application']
    
    for i, component in enumerate(components):
        print(f"\n{component_names[i]}:")
        baseline_score = None
        for condition in conditions:
            if condition in final_results:
                score = transform_to_100_scale(final_results[condition]['component_scores'][component])
                print(f"  {condition.upper()}: {score:.1f}/100")
                if condition == 'gpt4':
                    baseline_score = score
        
        if baseline_score:
            print(f"  Improvements vs GPT-4:")
            for condition in ['generic_memory', 'elessan']:
                if condition in final_results:
                    score = transform_to_100_scale(final_results[condition]['component_scores'][component])
                    improvement = score - baseline_score
                    print(f"    {condition.upper()}: {improvement:+.1f} points")
    
    print(f"\n🏆 OVERALL REASONING INDEX")
    print("=" * 60)
    
    baseline_reasoning = None
    for condition in conditions:
        if condition in final_results:
            reasoning_score = transform_to_100_scale(final_results[condition]['reasoning_index'])
            print(f"  {condition.upper()}: {reasoning_score:.1f}/100")
            if condition == 'gpt4':
                baseline_reasoning = reasoning_score
    
    if baseline_reasoning:
        print(f"\nImprovements vs GPT-4 Baseline:")
        for condition in ['generic_memory', 'elessan']:
            if condition in final_results:
                reasoning_score = transform_to_100_scale(final_results[condition]['reasoning_index'])
                improvement = reasoning_score - baseline_reasoning
                pct_improvement = (improvement / baseline_reasoning * 100) if baseline_reasoning > 0 else 0
                print(f"  {condition.upper()}: {improvement:+.1f} points ({pct_improvement:+.1f}%)")
    
    # Save results
    output_file = Path("benchmark_results/reasoning_component_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\n💾 Reasoning analysis saved to: {output_file}")
    print(f"\n✅ Reasoning component analysis complete!")

if __name__ == "__main__":
    main()
