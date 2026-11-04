"""Recompute the curated midpoint evidence without network or model calls."""
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parent
PRIMARY=[
 'm1-stable-cheap-v3','m1-stable-strong-v1',
 'm1-chunked-cheap-v1','m1-chunked-strong-v1',
 'm1-merge-cheap-v1','m1-merge-strong-v1',
 'm2-stable-jev-v1','m2-chunked-jev-v1','m2-merge-jev-v1',
]
SUPPLEMENTARY=['m2-stable-jev-sensitivity075','m4-clean-stable-cheap-v1']


def analyze(runs):
    primary=[json.loads((runs/r/'result.json').read_text()) for r in PRIMARY]
    hashes={json.loads((runs/r/'manifest.json').read_text())['protocol']['source_hash'] for r in PRIMARY}
    if len(hashes)!=1: raise ValueError('Primary runs use different source revisions')
    groups={}
    for policy in ['cheap','strong','jev']:
        items=[r for r in primary if r['policy']==policy]
        if len(items)!=3 or len({r['task'] for r in items})!=3: raise ValueError('Incomplete paired study')
        groups[policy]={
            'tasks':len(items),'successful_tasks':sum(r['passed'] for r in items),
            'billed_cost_usd':sum(r['billed_cost_usd'] for r in items) if all(r['costs_complete'] for r in items) else None,
            'mean_elapsed_s':statistics.mean(r['elapsed_s'] for r in items),
            'providers':sorted({p for r in items for p in r['providers']}),
        }
        if groups[policy]['billed_cost_usd'] is not None:
            groups[policy]['mean_billed_cost_usd']=groups[policy]['billed_cost_usd']/len(items)
    gate=[r for r in primary if r['policy']=='jev']
    accepted=[r for r in gate if r['selected_model']=='qwen/qwen3-coder-next']
    ledger={}
    for line in (runs/'spend_ledger.jsonl').read_text().splitlines():
        item=json.loads(line);ledger[item['id']]=item
    supplementary=[json.loads((runs/r/'result.json').read_text()) for r in SUPPLEMENTARY if (runs/r/'result.json').exists()]
    exclusions={
        'm1-stable-cheap-v1':'Sandbox prevented the local HTTP server from binding; no API call.',
        'm1-stable-cheap-v2':'Harness integration failure: wrong effective directory/path rules. Kept in artifacts and total spending, excluded from the post-fix comparison.',
    }
    return {
        'schema_version':1,'dataset':'synthetic-midpoint-v1','recorded_date':'2026-11-03',
        'claim':'Engineering feasibility only. Three constructed development tasks do not establish cost/performance equivalence or calibrated risk.',
        'primary_source_hash':next(iter(hashes)), 'primary_run_ids':PRIMARY,
        'primary_threshold':.90,'primary_results':primary,'policy_summary':groups,
        'cheap_coverage':len(accepted)/len(gate),
        'cheap_selective_risk':sum(not r['passed'] for r in accepted)/len(accepted) if accepted else None,
        'mean_gate_latency_s':statistics.mean(r['gate']['latency_s'] for r in gate),
        'gate_scores':{r['task']:r['gate']['score'] for r in gate},
        'supplementary_results':supplementary,'excluded_attempts':exclusions,
        'reserved_sanity_tasks_model_run':False,
        'total_session_accounted_usd':sum(r['amount'] for r in ledger.values()),
        'unresolved_request_reservations':sum(r['state']=='reserved' for r in ledger.values()),
    }


if __name__=='__main__':
    runs=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'runs'
    output=ROOT/'midpoint_evidence.json'
    output.write_text(json.dumps(analyze(runs),indent=2)+'\n')
    print(output)
