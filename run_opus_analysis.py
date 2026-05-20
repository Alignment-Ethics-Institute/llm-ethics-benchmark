#!/usr/bin/env python3
"""Run Opus 4.6 analysis to completion."""
import sys, os, json
os.chdir('/Users/devagatica/LLM_Ethics_Benchmark')
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('/Users/devagatica/LLM_Ethics_Benchmark/.env')
from thought_sovereignty_study.run_study import *
from thought_sovereignty_study.probes import ALL_PROBES
from shared.model_registry import MODEL_REGISTRY

mn = 'opus-4.6'
mc = MODEL_REGISTRY.get(mn)
clients = init_clients(mc, need_judge=True)
responses = json.load(open(f'thought_sovereignty_study/{mn}/responses.json'))
analyzed = analyze_all_responses(mn, clients, responses, ALL_PROBES)
good = len([a for a in analyzed if a.get('scores') is not None])
print(f'\n{mn}: {good} analyzed')
summary = generate_model_summary(mn, ALL_PROBES, analyzed)
print_model_summary(summary)
