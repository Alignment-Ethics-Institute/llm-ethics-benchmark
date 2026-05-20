#!/usr/bin/env python3
"""
Detailed Analysis of Elessan's Reasoning Trade-offs
Deep dive into what exactly Elessan does differently in:
1. Principle Identification
2. Perspective-Taking  
3. Consequence Analysis
"""

import json
import glob
import numpy as np
import re
from pathlib import Path
from collections import defaultdict, Counter

# Enhanced vocabularies for detailed analysis
MORAL_PRINCIPLES_DETAILED = {
    'autonomy': ['autonomy', 'freedom', 'liberty', 'choice', 'consent', 'self-determination', 'independence'],
    'justice': ['justice', 'fairness', 'equality', 'rights', 'equity', 'impartiality', 'fair'],
    'care': ['care', 'compassion', 'empathy', 'kindness', 'harm', 'suffering', 'wellbeing', 'help'],
    'duty': ['duty', 'obligation', 'responsibility', 'promise', 'commitment', 'honor', 'covenant'],
    'integrity': ['integrity', 'honesty', 'truth', 'authenticity', 'sincerity', 'transparency', 'genuine'],
    'respect': ['respect', 'dignity', 'worth', 'value', 'recognition', 'reverence', 'honor'],
    'loyalty': ['loyalty', 'fidelity', 'allegiance', 'devotion', 'solidarity', 'trust', 'faithful'],
    'authority': ['authority', 'hierarchy', 'order', 'obedience', 'discipline', 'tradition', 'power'],
    'sanctity': ['sanctity', 'purity', 'sacred', 'holy', 'virtue', 'moral', 'divine', 'righteous']
}

PERSPECTIVE_CATEGORIES = {
    'direct_stakeholders': ['father', 'son', 'joe', 'parent', 'child', 'family'],
    'broader_community': ['friends', 'society', 'community', 'people', 'others', 'everyone'],
    'institutional': ['camp', 'work', 'school', 'organization', 'system'],
    'viewpoint_markers': ['perspective', 'viewpoint', 'opinion', 'standpoint', 'view', 'side'],
    'alternative_thinking': ['however', 'alternatively', 'on the other hand', 'but', 'while', 'although']
}

CONSEQUENCE_TYPES = {
    'immediate': ['now', 'immediately', 'right away', 'at once', 'instantly'],
    'short_term': ['soon', 'shortly', 'quickly', 'in the near future', 'next'],
    'long_term': ['future', 'eventually', 'ultimately', 'long-term', 'in time', 'later'],
    'emotional': ['feel', 'emotion', 'hurt', 'happy', 'sad', 'angry', 'trust', 'relationship'],
    'practical': ['money', 'cost', 'benefit', 'loss', 'gain', 'practical', 'material'],
    'social': ['reputation', 'social', 'community', 'friends', 'relationships', 'status'],
    'moral': ['right', 'wrong', 'moral', 'ethical', 'conscience', 'values', 'principles']
}

def load_evaluated_results():
    """Load all evaluated results from run files."""
    results = {
        'gpt4': [],
        'elessan': [],
        'generic_memory': []
    }
    
    print("📂 Loading evaluated results for detailed analysis...")
    
    for condition in ['gpt4', 'elessan', 'generic_memory']:
        files = glob.glob(f"benchmark_results/{condition}_run_*.json")
        for file_path in sorted(files):
            with open(file_path, 'r') as f:
                run_data = json.load(f)
                if isinstance(run_data, list):
                    results[condition].extend(run_data)
                else:
                    results[condition].extend(run_data.get('results', []))
    
    return results

def analyze_principle_usage_patterns(responses, condition_name):
    """Analyze detailed patterns in principle usage."""
    
    principle_usage = defaultdict(list)
    principle_cooccurrence = defaultdict(lambda: defaultdict(int))
    principle_contexts = defaultdict(list)
    
    for response in responses:
        response_text = ''
        if 'processed_response' in response:
            response_text = response['processed_response'].get('full_response', '')
        elif 'full_response' in response:
            response_text = response['full_response']
        
        if not response_text:
            continue
            
        text_lower = response_text.lower()
        found_principles = []
        
        # Track which principles are mentioned
        for principle_category, terms in MORAL_PRINCIPLES_DETAILED.items():
            mentions = 0
            contexts = []
            for term in terms:
                count = text_lower.count(term)
                mentions += count
                
                # Extract context around principle mentions
                if count > 0:
                    pattern = rf'.{{0,30}}\b{re.escape(term)}\b.{{0,30}}'
                    matches = re.findall(pattern, text_lower)
                    contexts.extend(matches)
            
            if mentions > 0:
                found_principles.append(principle_category)
                principle_usage[principle_category].append(mentions)
                principle_contexts[principle_category].extend(contexts)
        
        # Track co-occurrence of principles
        for i, p1 in enumerate(found_principles):
            for j, p2 in enumerate(found_principles):
                if i != j:
                    principle_cooccurrence[p1][p2] += 1
    
    # Calculate statistics
    principle_stats = {}
    for principle, usage_counts in principle_usage.items():
        principle_stats[principle] = {
            'frequency': len(usage_counts) / len(responses) if responses else 0,
            'avg_mentions_when_used': np.mean(usage_counts) if usage_counts else 0,
            'total_mentions': sum(usage_counts),
            'sample_contexts': principle_contexts[principle][:3]  # First 3 contexts
        }
    
    return {
        'principle_stats': principle_stats,
        'cooccurrence': dict(principle_cooccurrence),
        'total_responses': len(responses)
    }

def analyze_perspective_patterns(responses, condition_name):
    """Analyze detailed patterns in perspective-taking."""
    
    perspective_usage = defaultdict(list)
    stakeholder_mentions = defaultdict(int)
    perspective_depth = []
    
    for response in responses:
        response_text = ''
        if 'processed_response' in response:
            response_text = response['processed_response'].get('full_response', '')
        elif 'full_response' in response:
            response_text = response['full_response']
        
        if not response_text:
            continue
            
        text_lower = response_text.lower()
        response_perspectives = []
        
        # Analyze each perspective category
        for category, terms in PERSPECTIVE_CATEGORIES.items():
            mentions = 0
            for term in terms:
                if isinstance(term, str):
                    mentions += text_lower.count(term)
                else:  # phrase
                    mentions += len(re.findall(re.escape(term), text_lower))
            
            if mentions > 0:
                perspective_usage[category].append(mentions)
                response_perspectives.append(category)
        
        # Count distinct stakeholders mentioned
        stakeholders_found = 0
        for stakeholder_group, terms in PERSPECTIVE_CATEGORIES.items():
            if stakeholder_group in ['direct_stakeholders', 'broader_community', 'institutional']:
                for term in terms:
                    if term in text_lower:
                        stakeholders_found += 1
                        stakeholder_mentions[term] += 1
                        break  # Count each group once per response
        
        perspective_depth.append(len(response_perspectives))
    
    # Calculate perspective statistics
    perspective_stats = {}
    for category, usage_counts in perspective_usage.items():
        perspective_stats[category] = {
            'frequency': len(usage_counts) / len(responses) if responses else 0,
            'avg_mentions_when_used': np.mean(usage_counts) if usage_counts else 0,
            'total_mentions': sum(usage_counts)
        }
    
    return {
        'perspective_stats': perspective_stats,
        'stakeholder_mentions': dict(stakeholder_mentions),
        'avg_perspective_depth': np.mean(perspective_depth) if perspective_depth else 0,
        'perspective_depth_distribution': Counter(perspective_depth),
        'total_responses': len(responses)
    }

def analyze_consequence_patterns(responses, condition_name):
    """Analyze detailed patterns in consequence analysis."""
    
    consequence_usage = defaultdict(list)
    temporal_focus = defaultdict(int)
    consequence_depth = []
    
    for response in responses:
        response_text = ''
        if 'processed_response' in response:
            response_text = response['processed_response'].get('full_response', '')
        elif 'full_response' in response:
            response_text = response['full_response']
        
        if not response_text:
            continue
            
        text_lower = response_text.lower()
        response_consequences = []
        
        # Analyze each consequence type
        for category, terms in CONSEQUENCE_TYPES.items():
            mentions = 0
            for term in terms:
                mentions += text_lower.count(term)
            
            if mentions > 0:
                consequence_usage[category].append(mentions)
                response_consequences.append(category)
                temporal_focus[category] += mentions
        
        consequence_depth.append(len(response_consequences))
        
        # Look for causal reasoning patterns
        causal_patterns = [
            r'if .+ then',
            r'would .+ result',
            r'could .+ lead',
            r'might .+ cause',
            r'because .+ therefore',
            r'since .+ consequently'
        ]
        
        causal_reasoning = 0
        for pattern in causal_patterns:
            causal_reasoning += len(re.findall(pattern, text_lower))
    
    # Calculate consequence statistics
    consequence_stats = {}
    for category, usage_counts in consequence_usage.items():
        consequence_stats[category] = {
            'frequency': len(usage_counts) / len(responses) if responses else 0,
            'avg_mentions_when_used': np.mean(usage_counts) if usage_counts else 0,
            'total_mentions': sum(usage_counts)
        }
    
    return {
        'consequence_stats': consequence_stats,
        'temporal_focus': dict(temporal_focus),
        'avg_consequence_depth': np.mean(consequence_depth) if consequence_depth else 0,
        'consequence_depth_distribution': Counter(consequence_depth),
        'total_responses': len(responses)
    }

def compare_reasoning_patterns(all_analyses):
    """Compare reasoning patterns across conditions."""
    
    print(f"\n🔍 DETAILED REASONING PATTERN ANALYSIS")
    print("=" * 70)
    
    conditions = ['gpt4', 'generic_memory', 'elessan']
    
    # Principle Analysis Comparison
    print(f"\n🎯 PRINCIPLE IDENTIFICATION PATTERNS")
    print("-" * 50)
    
    principle_categories = list(MORAL_PRINCIPLES_DETAILED.keys())
    
    for principle in principle_categories:
        print(f"\n{principle.upper()} Principle:")
        baseline_freq = None
        for condition in conditions:
            if condition in all_analyses:
                stats = all_analyses[condition]['principle_analysis']['principle_stats'].get(principle, {})
                freq = stats.get('frequency', 0) * 100
                avg_mentions = stats.get('avg_mentions_when_used', 0)
                
                print(f"  {condition.upper()}: {freq:.1f}% frequency, {avg_mentions:.1f} avg mentions")
                
                if condition == 'gpt4':
                    baseline_freq = freq
                elif baseline_freq and freq > 0:
                    diff = freq - baseline_freq
                    print(f"    Change vs GPT-4: {diff:+.1f}%")
    
    # Perspective Analysis Comparison  
    print(f"\n👥 PERSPECTIVE-TAKING PATTERNS")
    print("-" * 50)
    
    perspective_categories = list(PERSPECTIVE_CATEGORIES.keys())
    
    for category in perspective_categories:
        print(f"\n{category.replace('_', ' ').upper()}:")
        baseline_freq = None
        for condition in conditions:
            if condition in all_analyses:
                stats = all_analyses[condition]['perspective_analysis']['perspective_stats'].get(category, {})
                freq = stats.get('frequency', 0) * 100
                
                print(f"  {condition.upper()}: {freq:.1f}% frequency")
                
                if condition == 'gpt4':
                    baseline_freq = freq
                elif baseline_freq and freq > 0:
                    diff = freq - baseline_freq
                    print(f"    Change vs GPT-4: {diff:+.1f}%")
    
    # Consequence Analysis Comparison
    print(f"\n⚡ CONSEQUENCE ANALYSIS PATTERNS")
    print("-" * 50)
    
    consequence_categories = list(CONSEQUENCE_TYPES.keys())
    
    for category in consequence_categories:
        print(f"\n{category.replace('_', ' ').upper()} CONSEQUENCES:")
        baseline_freq = None
        for condition in conditions:
            if condition in all_analyses:
                stats = all_analyses[condition]['consequence_analysis']['consequence_stats'].get(category, {})
                freq = stats.get('frequency', 0) * 100
                
                print(f"  {condition.upper()}: {freq:.1f}% frequency")
                
                if condition == 'gpt4':
                    baseline_freq = freq
                elif baseline_freq and freq > 0:
                    diff = freq - baseline_freq
                    print(f"    Change vs GPT-4: {diff:+.1f}%")

def identify_elessan_signature_patterns(all_analyses):
    """Identify Elessan's distinctive reasoning signature."""
    
    print(f"\n🎯 ELESSAN'S REASONING SIGNATURE")
    print("=" * 70)
    
    if 'elessan' not in all_analyses or 'gpt4' not in all_analyses:
        print("Missing data for comparison")
        return
    
    elessan = all_analyses['elessan']
    gpt4 = all_analyses['gpt4']
    
    # Principle signature
    print(f"\n📈 PRINCIPLE IDENTIFICATION SIGNATURE:")
    principle_diffs = []
    for principle in MORAL_PRINCIPLES_DETAILED.keys():
        elessan_freq = elessan['principle_analysis']['principle_stats'].get(principle, {}).get('frequency', 0)
        gpt4_freq = gpt4['principle_analysis']['principle_stats'].get(principle, {}).get('frequency', 0)
        
        if gpt4_freq > 0:
            diff = ((elessan_freq - gpt4_freq) / gpt4_freq) * 100
            principle_diffs.append((principle, diff))
    
    # Sort by largest differences
    principle_diffs.sort(key=lambda x: abs(x[1]), reverse=True)
    
    print("Most distinctive principle patterns:")
    for principle, diff in principle_diffs[:5]:
        direction = "↗️ Enhanced" if diff > 0 else "↘️ Reduced"
        print(f"  {principle.upper()}: {diff:+.1f}% {direction}")
    
    # Perspective signature
    print(f"\n👥 PERSPECTIVE-TAKING SIGNATURE:")
    perspective_diffs = []
    for category in PERSPECTIVE_CATEGORIES.keys():
        elessan_freq = elessan['perspective_analysis']['perspective_stats'].get(category, {}).get('frequency', 0)
        gpt4_freq = gpt4['perspective_analysis']['perspective_stats'].get(category, {}).get('frequency', 0)
        
        if gpt4_freq > 0:
            diff = ((elessan_freq - gpt4_freq) / gpt4_freq) * 100
            perspective_diffs.append((category, diff))
    
    perspective_diffs.sort(key=lambda x: abs(x[1]), reverse=True)
    
    print("Most distinctive perspective patterns:")
    for category, diff in perspective_diffs[:5]:
        direction = "↗️ Enhanced" if diff > 0 else "↘️ Reduced"
        print(f"  {category.replace('_', ' ').upper()}: {diff:+.1f}% {direction}")
    
    # Consequence signature
    print(f"\n⚡ CONSEQUENCE ANALYSIS SIGNATURE:")
    consequence_diffs = []
    for category in CONSEQUENCE_TYPES.keys():
        elessan_freq = elessan['consequence_analysis']['consequence_stats'].get(category, {}).get('frequency', 0)
        gpt4_freq = gpt4['consequence_analysis']['consequence_stats'].get(category, {}).get('frequency', 0)
        
        if gpt4_freq > 0:
            diff = ((elessan_freq - gpt4_freq) / gpt4_freq) * 100
            consequence_diffs.append((category, diff))
    
    consequence_diffs.sort(key=lambda x: abs(x[1]), reverse=True)
    
    print("Most distinctive consequence patterns:")
    for category, diff in consequence_diffs[:5]:
        direction = "↗️ Enhanced" if diff > 0 else "↘️ Reduced"
        print(f"  {category.replace('_', ' ').upper()}: {diff:+.1f}% {direction}")

def main():
    print("🚀 Detailed Reasoning Trade-off Analysis")
    print("=" * 70)
    
    # Load results
    all_results = load_evaluated_results()
    
    print(f"\n🧠 DEEP REASONING ANALYSIS")
    print("=" * 70)
    
    all_analyses = {}
    
    for condition, responses in all_results.items():
        if not responses:
            continue
            
        print(f"\n🔍 Deep analysis of {condition.upper()}...")
        
        # Analyze each reasoning component in detail
        principle_analysis = analyze_principle_usage_patterns(responses, condition)
        perspective_analysis = analyze_perspective_patterns(responses, condition)
        consequence_analysis = analyze_consequence_patterns(responses, condition)
        
        all_analyses[condition] = {
            'principle_analysis': principle_analysis,
            'perspective_analysis': perspective_analysis,
            'consequence_analysis': consequence_analysis
        }
        
        print(f"  ✅ Analyzed {len(responses)} responses")
    
    # Compare patterns across conditions
    compare_reasoning_patterns(all_analyses)
    
    # Identify Elessan's signature
    identify_elessan_signature_patterns(all_analyses)
    
    # Save detailed analysis
    output_file = Path("benchmark_results/detailed_reasoning_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(all_analyses, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to: {output_file}")
    print(f"\n✅ Deep reasoning analysis complete!")

if __name__ == "__main__":
    main()
