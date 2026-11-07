"""Analyze the protocol-v2 end-to-end agent runs (coding_protocol_v2.json).

    python3 analyze_agent_runs.py            # -> agent_runs_evidence.json and report/agent_results.tex

Reads runs/coding-v2/*/result.json plus each run's localization, trace and patch.
Paired comparisons use only issues where both conditions completed. Standard library
only; no model calls.
"""

from __future__ import annotations

import json
import math
import random
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROTOCOL = json.loads((ROOT / 'coding_protocol_v2.json').read_text())
RUNS = ROOT / PROTOCOL['runs_dir']
CACHE = ROOT / PROTOCOL['cache_dir']
CONDITIONS = PROTOCOL['conditions']


def gold_files(patch):
    return {p for p in re.findall(r'^diff --git a/(\S+) b/', patch, flags=re.M)
            if p.startswith('pydicom/') and p.endswith('.py') and 'tests' not in p.split('/')}


def explorer_reported(run_dir):
    """Implementation files the explorer reported to the parent (any condition)."""
    found = set()
    for line in (run_dir / 'events.jsonl').read_text().splitlines():
        event = json.loads(line) if line.strip() else {}
        part = event.get('part') or {}
        if part.get('tool') == 'task' and (part.get('state') or {}).get('input', {}).get('subagent_type') == 'explore':
            found |= {p for p in re.findall(r'(pydicom/[\w./-]+?\.py)', str(part['state'].get('output', '')))
                      if 'tests' not in p.split('/')}
    return found


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [centre - half, centre + half]


def bootstrap_mean(diffs, reps=10000, seed=329):
    rng = random.Random(seed)
    n = len(diffs)
    if n == 0:
        return [None, None]
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return [means[int(0.025 * reps)], means[int(0.975 * reps) - 1]]


def sign_test(wins, losses):
    n, k = wins + losses, min(wins, losses)
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def load():
    rows = {r['instance_id']: r for r in json.loads((CACHE / 'tasks.json').read_text())}
    valid = json.loads((CACHE / 'environment_checks.json').read_text())
    runs = {}
    for path in sorted(RUNS.glob('v2-*/result.json')):
        result = json.loads(path.read_text())
        run_dir = path.parent
        gold = gold_files(rows[result['task']]['patch'])
        reported = explorer_reported(run_dir)
        edited = set(re.findall(r'^diff --git a/(\S+) b/', (run_dir / 'patch.diff').read_text(errors='replace'), flags=re.M))
        runs[(result['task'], result['condition'])] = {
            **{k: result.get(k) for k in ('passed', 'accounted_cost_usd', 'agent_elapsed_s', 'explore_elapsed_s',
                                           'writer_elapsed_s', 'evaluation_elapsed_s', 'timed_out', 'fallbacks',
                                           'explore_generation_calls', 'jev_calls', 'request_count', 'costs_complete')},
            'explorer_hit': bool(reported & gold), 'explorer_files': len(reported), 'patch_hit': bool(edited & gold),
            'gold': sorted(gold)}
    errors = sorted(p.name for p in RUNS.glob('*.batch-error.json'))
    return rows, valid, runs, errors


def summarize(runs, tasks):
    out = {}
    for c in CONDITIONS:
        group = [runs[(t, c)] for t in tasks if (t, c) in runs]
        n = len(group)
        passed = sum(r['passed'] for r in group)
        times = [r['agent_elapsed_s'] for r in group]
        out[c] = {
            'runs': n, 'passed': passed, 'pass_rate': passed / n if n else None, 'pass_ci95': wilson(passed, n),
            'cost_mean_usd': statistics.mean(r['accounted_cost_usd'] for r in group) if n else None,
            'time_mean_s': statistics.mean(times) if n else None,
            'time_median_s': statistics.median(times) if n else None,
            'explore_mean_s': statistics.mean(r['explore_elapsed_s'] or 0 for r in group) if n else None,
            'writer_mean_s': statistics.mean(r['writer_elapsed_s'] or 0 for r in group) if n else None,
            'explorer_hit_rate': sum(r['explorer_hit'] for r in group) / n if n else None,
            'patch_hit_rate': sum(r['patch_hit'] for r in group) / n if n else None,
            'timeouts': sum(bool(r['timed_out']) for r in group),
            'fallbacks': sum(r['fallbacks'] or 0 for r in group),
        }
    return out


def compare(runs, tasks, a, b):
    pairs = [(runs[(t, a)], runs[(t, b)]) for t in tasks if (t, a) in runs and (t, b) in runs]
    wins = sum(x['passed'] and not y['passed'] for x, y in pairs)
    losses = sum(y['passed'] and not x['passed'] for x, y in pairs)
    cost = [x['accounted_cost_usd'] - y['accounted_cost_usd'] for x, y in pairs]
    time_ = [x['agent_elapsed_s'] - y['agent_elapsed_s'] for x, y in pairs]
    mean_b_cost = statistics.mean(y['accounted_cost_usd'] for _, y in pairs) if pairs else None
    mean_b_time = statistics.mean(y['agent_elapsed_s'] for _, y in pairs) if pairs else None
    return {'pairs': len(pairs), 'success_wins': wins, 'success_losses': losses, 'success_sign_p': sign_test(wins, losses),
            'cost_diff_mean_usd': statistics.mean(cost) if cost else None, 'cost_diff_ci95': bootstrap_mean(cost),
            'cost_change_pct': 100 * statistics.mean(cost) / mean_b_cost if cost and mean_b_cost else None,
            'time_diff_mean_s': statistics.mean(time_) if time_ else None, 'time_diff_ci95': bootstrap_mean(time_),
            'time_change_pct': 100 * statistics.mean(time_) / mean_b_time if time_ and mean_b_time else None}


def by_localization(runs, tasks):
    """Does pointing the agent at a gold file go with more repairs? (Jev and search runs.)"""
    out = {}
    for c in ('jev', 'search'):
        group = [runs[(t, c)] for t in tasks if (t, c) in runs]
        for hit in (True, False):
            sub = [r for r in group if r['explorer_hit'] == hit]
            out[f'{c}_{"hit" if hit else "miss"}'] = {'runs': len(sub), 'passed': sum(r['passed'] for r in sub)}
    return out


def main():
    rows, valid, runs, errors = load()
    valid_tasks = [t['instance_id'] for t in PROTOCOL['tasks'] if valid.get(t['instance_id'], {}).get('valid')]
    complete = [t for t in valid_tasks if all((t, c) in runs for c in CONDITIONS)]
    evidence = {
        'protocol': PROTOCOL['protocol'], 'tasks_frozen': len(PROTOCOL['tasks']), 'tasks_valid': len(valid_tasks),
        'tasks_dropped': sorted(set(t['instance_id'] for t in PROTOCOL['tasks']) - set(valid_tasks)),
        'tasks_complete_all_conditions': len(complete), 'runs_completed': len(runs), 'batch_errors': errors,
        'total_cost_usd': sum(r['accounted_cost_usd'] for r in runs.values()),
        'conditions': summarize(runs, complete),
        'comparisons': {f'{a}_vs_{b}': compare(runs, complete, a, b)
                        for a, b in [('jev', 'native'), ('search', 'native'), ('oracle', 'native'),
                                     ('jev', 'search'), ('oracle', 'jev')]},
        'by_localization': by_localization(runs, complete),
        'runs': {f'{t}|{c}': v for (t, c), v in sorted(runs.items())},
    }
    (ROOT / 'agent_runs_evidence.json').write_text(json.dumps(evidence, indent=1))
    write_tex(evidence)
    print(f"{evidence['runs_completed']} runs; {len(complete)} of {len(valid_tasks)} valid issues complete in all "
          f"conditions; ${evidence['total_cost_usd']:.4f}; batch errors {len(errors)}")
    print(f"{'condition':8s} {'passed':>8s} {'95% CI':>15s} {'cost':>8s} {'time':>7s} {'median':>7s} {'explore':>8s} "
          f"{'writer':>7s} {'expl.hit':>8s} {'patch.hit':>9s}")
    for c, s in evidence['conditions'].items():
        if not s['runs']:
            continue
        lo, hi = s['pass_ci95']
        print(f"{c:8s} {s['passed']:>3d}/{s['runs']:<4d} [{100*lo:4.0f}%,{100*hi:4.0f}%] ${s['cost_mean_usd']:.4f} "
              f"{s['time_mean_s']:6.1f}s {s['time_median_s']:6.1f}s {s['explore_mean_s']:7.2f}s {s['writer_mean_s']:6.1f}s "
              f"{100*s['explorer_hit_rate']:7.0f}% {100*s['patch_hit_rate']:8.0f}%")
    for name, v in evidence['comparisons'].items():
        if not v['pairs']:
            continue
        print(f"{name:16s} n={v['pairs']} success W/L {v['success_wins']}/{v['success_losses']} (p={v['success_sign_p']:.3f}) "
              f"cost {v['cost_change_pct']:+.0f}% CI[{v['cost_diff_ci95'][0]:+.4f},{v['cost_diff_ci95'][1]:+.4f}] "
              f"time {v['time_change_pct']:+.0f}% ({v['time_diff_mean_s']:+.1f}s, CI[{v['time_diff_ci95'][0]:+.1f},{v['time_diff_ci95'][1]:+.1f}])")
    print('repairs by localization:', evidence['by_localization'])


def write_tex(evidence):
    names = {'native': 'Native generative explorer', 'jev': 'Jev file selection', 'search': 'Search only',
             'oracle': 'Oracle (gold files)'}
    rows = []
    for c in CONDITIONS:
        s = evidence['conditions'][c]
        if not s['runs']:
            continue
        rows.append(f"{names[c]} & {s['passed']}/{s['runs']} & {s['cost_mean_usd']:.4f} & {s['time_mean_s']:.1f} & "
                    f"{s['explore_mean_s']:.1f} & {100 * s['explorer_hit_rate']:.0f} \\\\")
    def fmt(x, digits=0):
        return 'n/a' if x is None else f'{x:.{digits}f}'
    c = evidence['comparisons']
    macros = {
        'AgFrozen': evidence['tasks_frozen'], 'AgValid': evidence['tasks_valid'],
        'AgDropped': len(evidence['tasks_dropped']), 'AgComplete': evidence['tasks_complete_all_conditions'],
        'AgRuns': evidence['runs_completed'], 'AgSpend': f"{evidence['total_cost_usd']:.2f}",
    }
    for key, tag in [('jev_vs_native', 'JevNative'), ('search_vs_native', 'SearchNative'), ('jev_vs_search', 'JevSearch'),
                     ('oracle_vs_native', 'OracleNative'), ('oracle_vs_jev', 'OracleJev')]:
        v = c[key]
        macros[f'Ag{tag}TimePct'] = fmt(v['time_change_pct'])
        macros[f'Ag{tag}TimeS'] = fmt(v['time_diff_mean_s'], 1)
        macros[f'Ag{tag}TimeLow'] = fmt(v['time_diff_ci95'][0], 1)
        macros[f'Ag{tag}TimeHigh'] = fmt(v['time_diff_ci95'][1], 1)
        macros[f'Ag{tag}CostPct'] = fmt(v['cost_change_pct'])
        macros[f'Ag{tag}Wins'] = v['success_wins']
        macros[f'Ag{tag}Losses'] = v['success_losses']
    for cond in CONDITIONS:
        s = evidence['conditions'][cond]
        macros[f'Ag{cond.capitalize()}Passed'] = s['passed']
        macros[f'Ag{cond.capitalize()}Time'] = fmt(s['time_mean_s'], 1)
        macros[f'Ag{cond.capitalize()}Explore'] = fmt(s['explore_mean_s'], 1)
    lines = ['% Generated by analyze_agent_runs.py; do not edit by hand.']
    lines += [f'\\newcommand{{\\{k}}}{{{v}}}' for k, v in macros.items()]
    lines.append('\\newcommand{\\AgentRows}{' + '\n'.join(rows) + '}')
    (ROOT / 'report' / 'agent_results.tex').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
