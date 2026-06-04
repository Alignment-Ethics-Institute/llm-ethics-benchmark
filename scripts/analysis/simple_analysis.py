#!/usr/bin/env python3
"""
Simple analysis of benchmark results
"""

import json
from collections import defaultdict, Counter

def analyze_responses():
    """Analyze the original responses for meaningful differences"""
    
    print("🔍 ANALYZING ORIGINAL RESPONSES")
    print("=" * 50)
    
    # Load original consolidated results
    with open('benchmark_results/all_results_consolidated.json', 'r') as f:
        results = json.load(f)
    
    comparison = {}
    
    for model in ['gpt4', 'elessan']:
        if model not in results:
            continue
            
        responses = results[model]
        print(f"\n📊 {model.upper()} Analysis ({len(responses)} responses):")
        
        # Analyze response characteristics
        word_counts = []
        argument_counts = []
        principle_counts = []
        positions = []
        principles_used = []
        
        for response in responses:
            if 'processed_response' in response:
                proc = response['processed_response']
                
                # Word count
                word_count = proc.get('word_count', 0)
                if word_count > 0:
                    word_counts.append(word_count)
                
                # Arguments
                args = proc.get('arguments', [])
                argument_counts.append(len(args))
                
                # Principles
                principles = proc.get('principles', [])
                principle_counts.append(len(principles))
                principles_used.extend(principles)
                
                # Position
                position = proc.get('position', 'unknown')
                positions.append(position)
        
        # Calculate statistics
        if word_counts:
            import statistics
            avg_words = statistics.mean(word_counts)
            avg_args = statistics.mean(argument_counts)
            avg_principles = statistics.mean(principle_counts)
            
            print(f"  📝 Average words per response: {avg_words:.1f}")
            print(f"  🎯 Average arguments per response: {avg_args:.1f}")
            print(f"  ⚖️  Average principles per response: {avg_principles:.1f}")
            
            # Position distribution
            position_counts = Counter(positions)
            print(f"  📊 Position distribution: {dict(position_counts)}")
            
            # Most common principles
            principle_counts_dict = Counter(principles_used)
            top_principles = principle_counts_dict.most_common(5)
            print(f"  🏛️  Top principles used: {top_principles}")
            
            # Store for comparison
            comparison[model] = {
                'avg_words': avg_words,
                'avg_arguments': avg_args,
                'avg_principles': avg_principles,
                'positions': dict(position_counts),
                'top_principles': top_principles
            }
    
    # Compare the two models
    print(f"\n🆚 MODEL COMPARISON")
    print("=" * 50)
    
    if 'gpt4' in comparison and 'elessan' in comparison:
        gpt4 = comparison['gpt4']
        elessan = comparison['elessan']
        
        print(f"\n📝 Response Length:")
        print(f"  GPT-4: {gpt4['avg_words']:.1f} words")
        print(f"  Elessan: {elessan['avg_words']:.1f} words")
        word_diff = elessan['avg_words'] - gpt4['avg_words']
        print(f"  Difference: {word_diff:+.1f} words ({word_diff/gpt4['avg_words']*100:+.1f}%)")
        
        print(f"\n🎯 Argumentation:")
        print(f"  GPT-4: {gpt4['avg_arguments']:.1f} arguments")
        print(f"  Elessan: {elessan['avg_arguments']:.1f} arguments")
        arg_diff = elessan['avg_arguments'] - gpt4['avg_arguments']
        print(f"  Difference: {arg_diff:+.1f} arguments ({arg_diff/gpt4['avg_arguments']*100:+.1f}%)")
        
        print(f"\n⚖️  Moral Principles:")
        print(f"  GPT-4: {gpt4['avg_principles']:.1f} principles")
        print(f"  Elessan: {elessan['avg_principles']:.1f} principles")
        prin_diff = elessan['avg_principles'] - gpt4['avg_principles']
        print(f"  Difference: {prin_diff:+.1f} principles ({prin_diff/gpt4['avg_principles']*100:+.1f}%)")
        
        print(f"\n📊 Position Distribution:")
        print(f"  GPT-4: {gpt4['positions']}")
        print(f"  Elessan: {elessan['positions']}")
        
        print(f"\n🏛️  Top Principles Used:")
        print(f"  GPT-4: {gpt4['top_principles']}")
        print(f"  Elessan: {elessan['top_principles']}")

def analyze_by_question_type():
    """Analyze differences by question type"""
    
    print(f"\n📋 ANALYSIS BY QUESTION TYPE")
    print("=" * 50)
    
    with open('benchmark_results/all_results_consolidated.json', 'r') as f:
        results = json.load(f)
    
    # Group by question type
    by_type = {
        'mfq': {'gpt4': [], 'elessan': []},
        'dilemmas': {'gpt4': [], 'elessan': []}
    }
    
    for model in ['gpt4', 'elessan']:
        if model in results:
            for response in results[model]:
                question_id = response.get('question_id', '')
                
                if 'Dilemma' in question_id:
                    by_type['dilemmas'][model].append(response)
                elif any(x in question_id for x in ['care', 'fairness', 'loyalty', 'authority', 'sanctity']):
                    by_type['mfq'][model].append(response)
    
    # Analyze each type
    for q_type in ['mfq', 'dilemmas']:
        print(f"\n📊 {q_type.upper()} Questions:")
        
        for model in ['gpt4', 'elessan']:
            responses = by_type[q_type][model]
            if not responses:
                continue
                
            # Calculate averages
            word_counts = []
            arg_counts = []
            
            for response in responses:
                if 'processed_response' in response:
                    proc = response['processed_response']
                    word_counts.append(proc.get('word_count', 0))
                    arg_counts.append(len(proc.get('arguments', [])))
            
            if word_counts:
                import statistics
                avg_words = statistics.mean([w for w in word_counts if w > 0])
                avg_args = statistics.mean(arg_counts)
                
                print(f"  {model.upper()}: {avg_words:.1f} words, {avg_args:.1f} arguments ({len(responses)} responses)")

def main():
    print("🚀 Simple Benchmark Analysis")
    print("=" * 50)
    
    try:
        analyze_responses()
        analyze_by_question_type()
        
        print(f"\n✅ Analysis complete!")
        print(f"\n💡 KEY INSIGHT: The real value is in HOW the models reason,")
        print(f"   not just their final positions. Look for differences in:")
        print(f"   • Depth of argumentation")
        print(f"   • Variety of moral principles considered")
        print(f"   • Consistency of reasoning patterns")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
