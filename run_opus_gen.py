#!/usr/bin/env python3
"""Run Opus 4.6 generation to completion."""
import sys, os, json
os.chdir('/Users/devagatica/LLM_Ethics_Benchmark')
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('/Users/devagatica/LLM_Ethics_Benchmark/.env')
from thought_sovereignty_study.run_study import *
from thought_sovereignty_study.probes import ALL_PROBES, RUNS_PER_PROBE
from shared.model_registry import MODEL_REGISTRY

mn = 'opus-4.6'
mc = MODEL_REGISTRY.get(mn)
clients = init_clients(mc, need_judge=False)
responses = generate_responses(mn, mc, clients, ALL_PROBES, RUNS_PER_PROBE)
good = len([r for r in responses if r.get('response') and not r.get('is_error')])
print(f'\nOpus 4.6 generation complete: {good}/1650')
