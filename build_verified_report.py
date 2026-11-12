"""Frozen analysis of the 30-run SWE-bench Verified pilot (verified-explore-v1).

Selects exactly the declared pilot run IDs (vpilot-<instance>-<condition>), checks
they are complete and share one source hash, and writes verified_evidence.json and
report/verified_results.tex. Gold patches are read here only to measure whether the
returned files / edited files contain the files the upstream fix changes; they never
reached the agent. No model calls. Kept separate from verified_probe.py so analysis
changes do not alter the runner's source hash.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / 'runs' / 'verified'
PROTOCOL = json.loads((ROOT / 'verified_protocol.json').read_text())
SAMPLE = json.loads((ROOT / 'verified_sample.json').read_text())
CONDITIONS = PROTOCOL['conditions']
LABELS = {'native': 'Native generative explorer', 'jev': 'Jev file selection', 'search': 'Search only'}


def analyze():
    ids = SAMPLE['pilot_subset']['instance_ids']
    rows = {r['instance_id']: r for r in json.loads((ROOT / '.runtime/verified/tasks.json').read_text())}
    gold = {i: set(re.findall(r'^diff --git a/(\S+)', rows[i]['patch'], re.M)) for i in ids}
    results, per_task = [], {}
    for i in ids:
        for c in CONDITIONS:
            d = RUNS / f'vpilot-{i}-{c}'
            r = json.loads((d / 'result.json').read_text())
            assert (r['task'], r['condition']) == (i, c) and r['costs_complete'] and r['grading_status'] == 'graded'
            recs = json.loads((d / 'requests.json').read_text())
            r['explore_cost'] = sum(x['cost_usd'] or 0 for x in recs if x['role'].startswith('explore'))
            r['explore_s'] = sum(x.get('elapsed_s') or 0 for x in recs if x['role'].startswith('explore'))
            r['writer_cost'] = sum(x['cost_usd'] or 0 for x in recs if not x['role'].startswith('explore'))
            r['writer_calls'] = sum(not x['role'].startswith('explore') for x in recs)
            locs = [json.loads(p.read_text()) for p in sorted(d.glob('localization-*.json'))]
            r['gold_in_candidates'] = bool(locs) and bool(gold[i] & {x['path'] for x in locs[0]['candidates']})
            r['gold_in_returned'] = bool(locs) and bool(gold[i] & set(locs[0]['selected']))
            r['jev_top_score'] = max(locs[0]['scores']) if c == 'jev' else None
            r['edited_gold_file'] = bool(gold[i] & set(r['changed_files']))
            results.append(r)
            per_task.setdefault(i, {})[c] = r['passed']
    hashes = {r['source_hash'] for r in results}
    assert len(results) == 3 * len(ids) and len(hashes) == 1, 'pilot runs incomplete or mixed protocol versions'
    groups = {}
    for c in CONDITIONS:
        g = [r for r in results if r['condition'] == c]
        n = len(g)
        groups[c] = {'tasks': n, 'passed': sum(r['passed'] for r in g),
                     'mean_cost_usd': sum(r['accounted_cost_usd'] for r in g) / n,
                     'mean_agent_s': sum(r['agent_elapsed_s'] for r in g) / n,
                     'mean_explore_cost_usd': sum(r['explore_cost'] for r in g) / n,
                     'mean_explore_s': sum(r['explore_s'] for r in g) / n,
                     'mean_writer_cost_usd': sum(r['writer_cost'] for r in g) / n,
                     'mean_writer_calls': sum(r['writer_calls'] for r in g) / n,
                     'explore_generation_calls': sum(r['explore_generation_calls'] for r in g),
                     'jev_calls': sum(r['jev_calls'] for r in g), 'fallbacks': sum(r['fallbacks'] for r in g),
                     'run_tests_calls': sum(r['run_tests_calls'] for r in g),
                     'gold_in_returned': sum(r['gold_in_returned'] for r in g),
                     'edited_gold_file': sum(r['edited_gold_file'] for r in g),
                     'timeouts': sum(r['timed_out'] for r in g), 'forbidden': sum(bool(r['forbidden_changes']) for r in g)}
    total = sum(r['accounted_cost_usd'] for r in results)
    savings = 1 - groups['jev']['mean_cost_usd'] / groups['native']['mean_cost_usd']
    evidence = {'protocol': PROTOCOL['protocol'], 'source_hash': hashes.pop(), 'instance_ids': ids,
                'conditions': groups, 'paired_outcomes': per_task, 'total_spend_usd': total,
                'jev_savings_vs_native': savings,
                'jev_scores_hit_vs_miss': {
                    'hit': sorted(r['jev_top_score'] for r in results if r['condition'] == 'jev' and r['gold_in_returned']),
                    'miss': sorted(r['jev_top_score'] for r in results if r['condition'] == 'jev' and not r['gold_in_returned'])},
                'runs': [{k: r[k] for k in ('run_id', 'task', 'condition', 'passed', 'accounted_cost_usd', 'agent_elapsed_s',
                                            'explore_cost', 'writer_cost', 'gold_in_candidates', 'gold_in_returned',
                                            'jev_top_score', 'edited_gold_file', 'run_tests_calls')} for r in results],
                'limitations': ['Ten tasks, one rollout per task and condition; no equivalence or superiority claim.',
                                'Gold-file overlap is an analysis proxy for localization quality, not the outcome.']}
    (ROOT / 'verified_evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    g = groups
    macros = [
        rf'\newcommand{{\VNativePassed}}{{{g["native"]["passed"]}}}',
        rf'\newcommand{{\VJevPassed}}{{{g["jev"]["passed"]}}}',
        rf'\newcommand{{\VSearchPassed}}{{{g["search"]["passed"]}}}',
        rf'\newcommand{{\VNativeCost}}{{{g["native"]["mean_cost_usd"]:.3f}}}',
        rf'\newcommand{{\VJevCost}}{{{g["jev"]["mean_cost_usd"]:.3f}}}',
        rf'\newcommand{{\VSearchCost}}{{{g["search"]["mean_cost_usd"]:.3f}}}',
        rf'\newcommand{{\VNativeTime}}{{{g["native"]["mean_agent_s"]:.1f}}}',
        rf'\newcommand{{\VJevTime}}{{{g["jev"]["mean_agent_s"]:.1f}}}',
        rf'\newcommand{{\VSearchTime}}{{{g["search"]["mean_agent_s"]:.1f}}}',
        rf'\newcommand{{\VSavings}}{{{100 * savings:.0f}}}',
        rf'\newcommand{{\VNativeExploreCost}}{{{g["native"]["mean_explore_cost_usd"]:.3f}}}',
        rf'\newcommand{{\VNativeExploreTime}}{{{g["native"]["mean_explore_s"]:.1f}}}',
        rf'\newcommand{{\VNativeExploreCalls}}{{{g["native"]["explore_generation_calls"]}}}',
        rf'\newcommand{{\VJevGoldReturned}}{{{g["jev"]["gold_in_returned"]}}}',
        rf'\newcommand{{\VSearchGoldReturned}}{{{g["search"]["gold_in_returned"]}}}',
        rf'\newcommand{{\VEditedGold}}{{{sum(x["edited_gold_file"] for x in g.values())}}}',
        rf'\newcommand{{\VTotalSpend}}{{{total:.2f}}}',
        '\\newcommand{\\VerifiedRows}{\n' + '\n'.join(
            f'{LABELS[c]} & {g[c]["passed"]}/{g[c]["tasks"]} & {g[c]["mean_cost_usd"]:.3f} & '
            f'{g[c]["mean_explore_cost_usd"]:.4f} & {g[c]["mean_writer_cost_usd"]:.3f} & {g[c]["mean_agent_s"]:.1f} \\\\'
            for c in CONDITIONS) + '\n}']
    # Development-pilot rows at the same precision as the Verified rows (from the frozen coding_evidence.json).
    dev = json.loads((ROOT / 'coding_evidence.json').read_text())['conditions']
    macros.append('\\newcommand{\\DevRows}{\n' + '\n'.join(
        f'{LABELS[c]} & {dev[c]["passed"]}/{dev[c]["tasks"]} & {dev[c]["mean_cost_usd"]:.3f} & & & {dev[c]["mean_agent_s"]:.1f} \\\\'
        for c in CONDITIONS) + '\n}')
    (ROOT / 'report/verified_results.tex').write_text('\n'.join(macros) + '\n')
    print(json.dumps(groups, indent=2))
    return evidence


if __name__ == '__main__':
    analyze()
