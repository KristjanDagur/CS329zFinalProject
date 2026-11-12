"""Offline, paired BANKING77 analysis. No model calls and no threshold fitting.

Run after collection: python3 intent_analysis.py
Optionally add --figures with matplotlib installed. Archives contain all receipts.
"""
import argparse
import collections
import math
from pathlib import Path
import random
import statistics

import intent_probe as i


def quantile(values, p):
    if not values:
        return None
    values=sorted(values)
    x=(len(values)-1)*p
    lo=int(x)
    return values[lo]+(values[min(lo+1,len(values)-1)]-values[lo])*(x-lo)


def wilson(k,n):
    if not n:
        return [0,1]
    z=1.959963984540054
    center=(k/n+z*z/(2*n))/(1+z*z/n)
    half=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/(1+z*z/n)
    return [center-half,center+half]


def metrics(gold,prediction,cost,latency,labels,calls=None):
    n=len(gold)
    correct=sum(g==p for g,p in zip(gold,prediction))
    tp=collections.Counter(g for g,p in zip(gold,prediction) if g==p)
    ng,np=collections.Counter(gold),collections.Counter(prediction)
    return dict(n=n,correct=correct,accuracy=correct/n,accuracy_wilson_95=wilson(correct,n),
        macro_f1=statistics.mean(2*tp[c]/(ng[c]+np[c]) if ng[c]+np[c] else 0 for c in labels),
        missing_predictions=sum(p is None for p in prediction),total_usd=sum(cost),
        mean_usd=sum(cost)/n,usd_per_correct=sum(cost)/correct if correct else None,
        replay_or_load_elapsed_p50_s=quantile(latency,.5),replay_or_load_elapsed_p95_s=quantile(latency,.95),
        mean_calls=statistics.mean(calls) if calls else None)


def compose(jev,agent,accept):
    pred,cost,latency,calls=[],[],[],[]
    for j,a,use in zip(jev,agent,accept):
        pred.append(j['prediction'] if use else a['prediction'])
        cost.append(j['cost_usd']+(0 if use else a['cost_usd']))
        latency.append(j['elapsed_s']+(0 if use else a['elapsed_s']))
        calls.append(j['calls']+(0 if use else a['calls']))
    return dict(pred=pred,cost=cost,latency=latency,calls=calls)


def paired_bootstrap(rows,gold,values,baseline,reps,seed):
    rng=random.Random(seed)
    groups=collections.defaultdict(list)
    for n,r in enumerate(rows):
        groups[r['label']].append(n)
    delta={c:[] for c in values if c!=baseline}
    ratios={c:[] for c in delta}
    for _ in range(reps):
        ids=[rng.choice(group) for group in groups.values() for _ in group]
        base_correct=sum(values[baseline]['pred'][k]==gold[k] for k in ids)
        base_cost=sum(values[baseline]['cost'][k] for k in ids)
        for c in delta:
            delta[c].append((sum(values[c]['pred'][k]==gold[k] for k in ids)-base_correct)/len(ids))
            ratios[c].append(sum(values[c]['cost'][k] for k in ids)/base_cost)
    return {c:dict(accuracy_difference_95=[quantile(delta[c],.025),quantile(delta[c],.975)],
                   one_sided_95_lower=quantile(delta[c],.05),
                   cost_ratio_95=[quantile(ratios[c],.025),quantile(ratios[c],.975)]) for c in delta}


def evaluate():
    frozen=i.read(i.ROOT/'intent_frozen.json')
    analysis_plan=i.read(i.ROOT/'intent_analysis_plan.json')
    assert i.protocol_signature()==frozen['signature']
    assert i.digest((i.ROOT/'intent_probe.py').read_bytes())==frozen['source_sha256']
    assert i.digest((i.ROOT/'intent_native.py').read_bytes())==frozen['native_sha256']
    wanted=set(frozen['test_ids'])
    rows=sorted([r for r in i.read(i.CACHE/'test.json') if r['id'] in wanted],key=lambda r:r['id'])
    assert len(rows)==len(wanted)==frozen['sample_count']
    gold=[r['label'] for r in rows]
    labels=sorted(i.read(i.CACHE/'catalog.json'))
    records={}
    for c in ('jev','direct','agent'):
        found=i.results('test',c)
        if set(found)!=wanted:
            raise RuntimeError(f'{c}: only {len(found)}/{len(wanted)} frozen results; finish collection before analysis')
        records[c]=[dict(found[r['id']]) for r in rows]
        for row,result in zip(rows,records[c]):
            assert result['input_hash']==i.digest(row['text']) and result['signature']==frozen['signature']
            if result['status']!='complete':
                result['prediction']=None
    # A portable archive carries JSON receipts, not a live SQLite database.
    ledger=i.Ledger(i.RUNS/'ledger.sqlite3')
    calls=ledger.records()
    if calls:
        spending=ledger.status()
    else:
        exported=i.read(i.RUNS/'ledger_export.json')
        calls,spending=exported['records'],exported['summary']
        if not calls:
            raise RuntimeError('No accounting receipts are available')
    # Reconcile any late-settling transport receipt into the offline accounting.
    by_job=collections.defaultdict(list)
    for call in calls:
        by_job[call['job']].append(call)
    reconcile=[]
    for c,rs in records.items():
        for row,result in zip(rows,rs):
            job=frozen['signature'][:16]+'/test/'+row['id']+'/'+c
            actual=by_job[job]
            total=sum(x['amount'] for x in actual)
            if abs(total-result['cost_usd'])>1e-10:
                reconcile.append(dict(id=row['id'],condition=c,recorded=result['cost_usd'],accounted=total))
                result['cost_usd']=total
            result['calls']=len(actual)
    values={c:dict(pred=[r['prediction'] for r in rs],cost=[r['cost_usd'] for r in rs],
                   latency=[r['elapsed_s'] for r in rs],calls=[r['calls'] for r in rs]) for c,rs in records.items()}
    candidate_threshold=analysis_plan['fixed_uncertified_candidate']['threshold']
    mask=[i.accepted(r,candidate_threshold) for r in records['jev']]
    certified_mask=[i.accepted(r,frozen['effective_threshold']) for r in records['jev']]
    values['candidate_uncertified']=compose(records['jev'],records['agent'],mask)
    values['certified_fallback']=compose(records['jev'],records['agent'],certified_mask)
    accepted_n=sum(mask)
    accepted_errors=sum(use and p!=g for use,p,g in zip(mask,values['jev']['pred'],gold))
    random_metrics=[]
    valid=[n for n,r in enumerate(records['jev']) if r['status']=='complete']
    for seed in frozen['analysis']['random_seeds']:
        picked=set(random.Random(seed).sample(valid,accepted_n))
        v=compose(records['jev'],records['agent'],[n in picked for n in range(len(rows))])
        m=metrics(gold,v['pred'],v['cost'],v['latency'],labels,v['calls'])
        random_metrics.append(dict(seed=seed,**m))
        if seed==frozen['analysis']['random_seeds'][0]:
            values['random_matched_seed32977']=v
    all_metrics={c:metrics(gold,v['pred'],v['cost'],v['latency'],labels,v['calls']) for c,v in values.items()}
    # A free nearest-example reference, declared optional in the original plan.
    retriever=i.Retriever(i.read(i.CACHE/'support.json'))
    bm25=[]
    for row in rows:
        hits=retriever.search(row['text'],1)
        bm25.append(hits[0]['intent'] if hits else None)
    all_metrics['bm25_nearest']=metrics(gold,bm25,[0]*len(rows),[0]*len(rows),labels)
    paired=paired_bootstrap(rows,gold,values,'agent',frozen['analysis']['bootstrap_replicates'],frozen['analysis']['bootstrap_seed'])
    valid_indices=[n for n,r in enumerate(records['jev']) if r['status']=='complete']
    brier=statistics.mean(sum((p-(label==gold[n]))**2 for label,p in records['jev'][n]['probabilities'].items()) for n in valid_indices)
    reliability=[]
    for lo in range(10):
        ids=[n for n in valid_indices if lo/10 <= records['jev'][n]['score'] and (records['jev'][n]['score']<(lo+1)/10 or lo==9)]
        reliability.append(dict(lower=lo/10,upper=(lo+1)/10,n=len(ids),
            mean_score=statistics.mean(records['jev'][n]['score'] for n in ids) if ids else None,
            accuracy=statistics.mean(values['jev']['pred'][n]==gold[n] for n in ids) if ids else None))
    ece=sum(b['n']*abs(b['mean_score']-b['accuracy']) for b in reliability if b['n'])/len(valid_indices)
    risk_coverage=[]
    for threshold in frozen['protocol']['threshold_grid']:
        chosen=[n for n,r in enumerate(records['jev']) if i.accepted(r,threshold)]
        errors=sum(values['jev']['pred'][n]!=gold[n] for n in chosen)
        risk_coverage.append(dict(threshold=threshold,accepted=len(chosen),coverage=len(chosen)/len(rows),
                                  errors=errors,risk=errors/len(chosen) if chosen else None))
    support_norm={i.normalize(r['text']) for r in i.read(i.CACHE/'support.json')}
    clean=[n for n,r in enumerate(rows) if i.normalize(r['text']) not in support_norm]
    nonoverlap={c:dict(n=len(clean),correct=sum(v['pred'][n]==gold[n] for n in clean),
                     accuracy=statistics.mean(v['pred'][n]==gold[n] for n in clean)) for c,v in values.items()}
    confusions={c:[dict(gold=g,predicted=p,count=n) for (g,p),n in collections.Counter((g,p) for g,p in zip(gold,v['pred']) if g!=p).most_common(15)] for c,v in values.items()}
    escalated=[n for n,use in enumerate(mask) if not use]
    corrections=sum(values['jev']['pred'][n]!=gold[n] and values['agent']['pred'][n]==gold[n] for n in escalated)
    regressions=sum(values['jev']['pred'][n]==gold[n] and values['agent']['pred'][n]!=gold[n] for n in escalated)
    disagreements=sum(values['candidate_uncertified']['pred'][n]!=values['agent']['pred'][n] for n in range(len(rows)))
    candidate=all_metrics['candidate_uncertified']
    baseline=all_metrics['agent']
    errors=[dict(id=r['id'],text=r['text'],gold=gold[n],jev_prediction=values['jev']['pred'][n],
                 score=records['jev'][n].get('score'),agent_prediction=values['agent']['pred'][n],
                 direct_prediction=values['direct']['pred'][n],candidate_prediction=values['candidate_uncertified']['pred'][n],
                 jev_accepted=mask[n],support_overlap=n not in clean) for n,r in enumerate(rows)
            if values['candidate_uncertified']['pred'][n]!=gold[n]]
    provider_counts=collections.Counter((c['model'],c['receipt'].get('provider')) for c in calls if c['job'].startswith(frozen['signature'][:16]+'/test/') and c['state']=='complete')
    result=dict(dataset='BANKING77',signature=frozen['signature'],n=len(rows),certification=frozen['certification'],
        effective_certified_threshold=frozen['effective_threshold'],candidate_threshold=candidate_threshold,
        candidate_certified=False,metrics=all_metrics,paired_vs_agent=paired,
        candidate_acceptance=dict(n=accepted_n,coverage=accepted_n/len(rows),errors=accepted_errors,
            risk=accepted_errors/accepted_n if accepted_n else None,
            one_sided_95_binomial_upper=i.binomial_upper(accepted_errors,accepted_n)),
        random_matched=dict(seeds=frozen['analysis']['random_seeds'],per_seed=random_metrics,
            mean_accuracy=statistics.mean(m['accuracy'] for m in random_metrics),
            min_accuracy=min(m['accuracy'] for m in random_metrics),max_accuracy=max(m['accuracy'] for m in random_metrics),
            mean_usd=statistics.mean(m['mean_usd'] for m in random_metrics)),
        calibration=dict(multiclass_brier=brier,ece_10_bins=ece,bins=reliability,valid_n=len(valid_indices)),
        risk_coverage_descriptive_only=risk_coverage,nonoverlap=nonoverlap,
        fallback=dict(escalated=len(escalated),corrections=corrections,regressions=regressions,
            candidate_agent_disagreements=disagreements),confusions=confusions,
        errors=errors,reconciliation=reconcile,research_spending=spending,
        providers=[dict(model=m,provider=p,n=n) for (m,p),n in provider_counts.items()],
        candidate_targets=dict(certified_5pct_risk=False,
            cost_reduction=1-candidate['mean_usd']/baseline['mean_usd'],
            cost_reduction_at_least_30pct=candidate['mean_usd']<=.7*baseline['mean_usd'],
            accuracy_difference=candidate['accuracy']-baseline['accuracy'],
            within_2pts_one_sided_95=paired['candidate_uncertified']['one_sided_95_lower']>=-.02),
        limitations=[
            'The 0.96 candidate failed independent certification and remains uncertified; the default certified policy always escalates and offers no savings.',
            'One rollout per example, one public closed-set dataset, and one served model pair; no OOS or production banking claim.',
            'Binomial intervals assume independent exchangeable errors; stratification, utterance similarity, and grouped duplicates limit population-risk interpretation.',
            'Public benchmark pretraining contamination cannot be ruled out. Local held-out splitting does not establish absence of pretraining contamination.',
            'Replay/load elapsed times include concurrency and queue effects; they are not measured deployed-cascade latency. Serial live development results are separate.',
            'Prompts/catalog and native-agent overhead differ from the direct baseline by design. A cascade must be assessed against direct strong as well as the agent.',
            'Costs are observed OpenRouter charges including cache/reasoning where billed; unresolved transport attempts remain conservatively reserved.',
        ])
    live_path=i.RUNS/'live_evidence.json'
    if live_path.exists():
        live=i.read(live_path)
        result['live_certified_fallback']=dict(n=len(live['rows']),note=live['note'],
            p50_s=quantile([r['elapsed_s'] for r in live['rows']],.5),
            p95_s=quantile([r['elapsed_s'] for r in live['rows']],.95),
            mean_usd=statistics.mean(r['cost_usd'] for r in live['rows']),correct=sum(r['correct'] for r in live['rows']))
    i.dump(i.ROOT/'intent_evidence.json',result)
    i.dump(i.RUNS/'ledger_export.json',dict(summary=spending,records=calls))
    write_report(result)
    return result


def write_report(e):
    m=e['metrics']
    lines=['# BANKING77 results','',
        'Rami’s individual experiment. All 3,080 official test examples; settings frozen before test collection. '
        'The fixed 0.96 cascade is **uncertified**: independent certification gave a 5.157% one-sided upper error bound, exceeding the 5% target. '
        'The predeclared certified fallback always invokes the agent.','',
        '| Condition | Correct / 3,080 | Accuracy | Macro-F1 | Mean USD |',
        '|---|---:|---:|---:|---:|']
    for c in ('jev','direct','agent','candidate_uncertified','certified_fallback','random_matched_seed32977','bm25_nearest'):
        r=m[c]
        lines.append(f"| {c} | {r['correct']} | {r['accuracy']:.2%} | {r['macro_f1']:.4f} | ${r['mean_usd']:.6f} |")
    a=e['candidate_acceptance']; target=e['candidate_targets'];pair=e['paired_vs_agent']['candidate_uncertified']
    lines += ['',f"The fixed candidate accepted {a['n']}/{e['n']} ({a['coverage']:.1%}), with {a['errors']} accepted errors ({a['risk']:.2%}). "
        f"Its observed cost reduction against the always-agent condition was {target['cost_reduction']:.1%}. "
        f"Its accuracy difference was {100*target['accuracy_difference']:+.2f} percentage points "
        f"(paired stratified bootstrap 95% interval {100*pair['accuracy_difference_95'][0]:+.2f} to {100*pair['accuracy_difference_95'][1]:+.2f}).",
        '',f"The one-sided 95% lower accuracy-difference bound is {100*pair['one_sided_95_lower']:+.2f} points; "
        f"the predeclared 2-point noninferiority target {'is met under this bootstrap analysis' if target['within_2pts_one_sided_95'] else 'is not established'}. "
        'This does not undo the failed independent risk certification.',
        '',f"Across 20 matched-coverage random seeds, mean accuracy was {e['random_matched']['mean_accuracy']:.2%} "
        f"(seed range {e['random_matched']['min_accuracy']:.2%}–{e['random_matched']['max_accuracy']:.2%}). "
        f"On escalated examples the fallback corrected {e['fallback']['corrections']} Jev errors and introduced {e['fallback']['regressions']} regressions.",
        '',f"Actual research spending, including development/prototype attempts: ${e['research_spending']['billed_usd']:.4f} confirmed "
        f"plus ${e['research_spending']['reserved_usd']:.4f} unresolved reservations. Deployment policy costs in the table count only the calls that policy uses, not every research comparator.",
        '', '## Interpretation and limitations','']
    lines += ['- '+t for t in e['limitations']]
    lines += ['', '## Reproduction','',
        'Prepare the pinned official data, unpack `intent_runs.zip` into the repository root, and run `python3 intent_analysis.py`. '
        'No API key or model calls are needed for analysis. `intent_evidence.json` contains the full metrics, uncertainties, confusion pairs, error rows, provider counts and cost reconciliation.',
        '', '## AI-use and authorship','',
        'Rami selected this workstream and directed the implementation and evaluation. Codex implemented the runner, checks, data collection, analysis, and this draft report text. '
        'The team must review the interpretation and authorship before incorporating it into the final report. No report or video has been submitted.',
        '', 'Data attribution: PolyAI/PolyAI-LDN, BANKING77, task-specific-datasets revision `57ec275d8078af65b7731c2a98be812d844a6d6b`, CC BY 4.0. '
        'Original study: Casanueva et al., “Efficient Intent Detection with Dual Sentence Encoders,” 2020, https://arxiv.org/abs/2003.04807.','']
    (i.ROOT/'report/intent_results.md').write_text('\n'.join(lines))


def figures(e):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=i.ROOT/'report/intent_figures'
    out.mkdir(exist_ok=True)
    names=['jev','direct','agent','candidate_uncertified']
    labels=['Jev','Strong direct','Retrieval agent','Cascade (uncertified)']
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    colors=['#5086c1','#de9a36','#70777d','#309584']
    ms=[e['metrics'][n] for n in names]
    for ax,field,title in zip(axes,['accuracy','mean_usd'],['Intent accuracy','Observed cost per query (USD)']):
        vals=[m[field] for m in ms]
        ax.bar(range(4),vals,color=colors)
        ax.set_xticks(range(4),labels,rotation=15,ha='right')
        ax.set_title(title)
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y',alpha=.15)
        if field=='accuracy':
            low=[m['accuracy']-m['accuracy_wilson_95'][0] for m in ms]
            high=[m['accuracy_wilson_95'][1]-m['accuracy'] for m in ms]
            ax.errorbar(range(4),vals,yerr=[low,high],fmt='none',ecolor='#222222',capsize=3)
            ax.set_ylim(.7,1)
        else:
            ax.set_yscale('log')
    fig.savefig(out/'accuracy_cost.png',dpi=180)
    fig.savefig(out/'accuracy_cost.pdf')
    plt.close(fig)
    curve=[p for p in e['risk_coverage_descriptive_only'] if p['risk'] is not None]
    fig,ax=plt.subplots(figsize=(5.4,3.8),layout='constrained')
    ax.plot([p['coverage'] for p in curve],[p['risk'] for p in curve],color='#5086c1')
    a=e['candidate_acceptance']
    ax.scatter([a['coverage']],[a['risk']],color='#b24b48',label='Frozen 0.96 candidate (uncertified)',zorder=3)
    ax.axhline(.05,ls='--',color='#70777d',label='5% target')
    ax.set(xlabel='Fraction accepted by Jev',ylabel='Observed accepted error',title='Test risk–coverage (descriptive only)')
    ax.legend(fontsize=8)
    ax.spines[['top','right']].set_visible(False)
    fig.savefig(out/'risk_coverage.png',dpi=180)
    fig.savefig(out/'risk_coverage.pdf')
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figures',action='store_true')
    args=parser.parse_args()
    evidence=evaluate()
    if args.figures:
        figures(evidence)
    print({k:dict(accuracy=v['accuracy'],mean_usd=v['mean_usd']) for k,v in evidence['metrics'].items()})
