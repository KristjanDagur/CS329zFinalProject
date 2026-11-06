"""Reproduce the frozen 15-run comparison offline; optionally compile its PDF.

Reads only the declared primary run IDs from coding_runs.zip, so later teammate
or demo runs cannot silently alter the published comparison. No API calls.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent


def analyze():
    with zipfile.ZipFile(ROOT / 'coding_runs.zip') as archive:
        def read(name):
            return json.loads(archive.read(name))
        protocol = read('source/coding_protocol.json')
        source_hash = hashlib.sha256(json.dumps({
            name: archive.read('source/' + name).decode()
            for name in ('coding_probe.py', 'coding_protocol.json')
        }, sort_keys=True).encode()).hexdigest()
        results = []
        for condition in protocol['conditions']:
            for task in protocol['tasks']:
                run_id = 'e0-' + task['instance_id'].rsplit('-', 1)[1] + '-' + condition + '-v1'
                prefix = 'runs/coding/' + run_id + '/'
                result = read(prefix + 'result.json')
                requests = read(prefix + 'requests.json')
                assert result['task'] == task['instance_id'] and result['condition'] == condition
                assert result['source_hash'] == source_hash
                assert result['costs_complete'] and requests
                assert all(r.get('cost_status') == 'settled' for r in requests)
                assert math.isclose(sum(r['cost_usd'] for r in requests), result['billed_cost_usd'], abs_tol=1e-10)
                result['exploration_cost_usd'] = sum(r['cost_usd'] for r in requests if r['role'].startswith('explore'))
                result['jev_cost_usd'] = sum(r['cost_usd'] for r in requests if r['kind'] == 'decision')
                results.append(result)
        groups = {}
        for condition in protocol['conditions']:
            group = [r for r in results if r['condition'] == condition]
            groups[condition] = {'tasks': len(group), 'passed': sum(r['passed'] for r in group),
                'total_cost_usd': sum(r['billed_cost_usd'] for r in group),
                'mean_cost_usd': sum(r['billed_cost_usd'] for r in group)/len(group),
                'mean_agent_s': sum(r['agent_elapsed_s'] for r in group)/len(group),
                'exploration_generation_calls': sum(r['explore_generation_calls'] for r in group),
                'jev_calls': sum(r['jev_calls'] for r in group),
                'total_exploration_cost_usd': sum(r['exploration_cost_usd'] for r in group),
                'total_jev_cost_usd': sum(r['jev_cost_usd'] for r in group)}
        checks = read('environment/environment_checks.json')
        assert len(checks) == 5 and all(r['valid'] for r in checks.values())
        evidence = {'protocol': protocol, 'source_hash': source_hash,
             'archive_sha256': hashlib.sha256((ROOT / 'coding_runs.zip').read_bytes()).hexdigest(),
             'data_receipt': read('environment/data_receipt.json'), 'results': results, 'conditions': groups,
             'total_spend_usd': sum(r['billed_cost_usd'] for r in results),
             'jev_savings_vs_native': 1-groups['jev']['mean_cost_usd']/groups['native']['mean_cost_usd'],
             'jev_premium_vs_search': groups['jev']['mean_cost_usd']/groups['search']['mean_cost_usd']-1,
             'conclusion': 'All three conditions solved the same 2/5 development issues. Jev is cheaper than native exploration but search-only is cheaper still. No added value over retrieval or performance equivalence is established.',
             'limitations': ['Five convenience-selected development issues in one repository, one rollout each.',
                 'Native local pytest, not official Docker SWE-bench evaluation.',
                 'Native explorer has whole-repository access; replacements use bounded candidates.',
                 'Stochastic writer recovery can hide localization errors; total cost differences are not all direct Jev overhead.',
                 'No calibrated confidence, 5% risk guarantee, or held-out performance claim.']}
    (ROOT / 'coding_evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    labels = {'native': 'Native generative explorer', 'jev': 'Jev file selection', 'search': 'Search only'}
    rows = []
    macros = []
    for condition, prefix in [('native', 'Native'), ('jev', 'Jev'), ('search', 'Search')]:
        r = groups[condition]
        macros += [rf'\newcommand{{\{prefix}Passed}}{{{r["passed"]}}}',
                   rf'\newcommand{{\{prefix}Cost}}{{{r["mean_cost_usd"]:.6f}}}',
                   rf'\newcommand{{\{prefix}Time}}{{{r["mean_agent_s"]:.2f}}}']
        rows.append(f'{labels[condition]} & {r["passed"]}/5 & {r["mean_cost_usd"]:.6f} & {r["mean_agent_s"]:.2f} '+r'\\')
    macros += [rf'\newcommand{{\Savings}}{{{100*evidence["jev_savings_vs_native"]:.1f}}}',
               rf'\newcommand{{\TotalSpend}}{{{evidence["total_spend_usd"]:.6f}}}',
               rf'\newcommand{{\ExplorerCalls}}{{{groups["native"]["exploration_generation_calls"]}}}',
               '\\newcommand{\\CodingRows}{\n'+'\n'.join(rows)+'\n}']
    (ROOT / 'report/coding_results.tex').write_text('\n'.join(macros)+'\n')
    print(json.dumps(groups, indent=2))
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compile', action='store_true')
    args = parser.parse_args()
    analyze()
    if args.compile:
        compiler = shutil.which('pdflatex') or '/Library/TeX/texbin/pdflatex'
        env = os.environ.copy()
        fonts = ROOT / '.runtime/texmf'
        if fonts.exists():
            env.update(TEXMFHOME=str(fonts), TEXMFVAR=str(ROOT / '.runtime/texmf-var'))
        tex = r'\pdfmapfile{+uhv.map}\pdfmapfile{+utm.map}\pdfmapfile{+ucr.map}\input{coding_midpoint.tex}' if fonts.exists() else 'coding_midpoint.tex'
        for _ in range(2):
            proc = subprocess.run([compiler, '-interaction=nonstopmode', '-halt-on-error', tex],
                                  cwd=ROOT / 'report', env=env, capture_output=True, text=True)
            if proc.returncode:
                raise RuntimeError(proc.stdout[-2500:])
        print(ROOT / 'report/coding_midpoint.pdf')
