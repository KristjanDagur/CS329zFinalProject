"""Post-hoc paired tests on frozen BANKING77 trajectories; no API calls.

python3 intent_significance.py [--figures]
Requires requirements-intent-stats.txt. Original results/archive stay unchanged.
"""
import argparse
import collections
import math
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy import stats

import intent_probe as i
import intent_analysis as a


def p_fields(p):
    p=float(p)
    if p==0:
        return dict(pvalue=None,pvalue_upper_bound=1e-300,p_text='<1e-300',numerical_underflow=True)
    if not math.isfinite(p) or not 0<=p<=1:
        raise ValueError('Invalid p-value')
    return dict(pvalue=p,p_text=f'{p:.6g}',numerical_underflow=False)


def t_test(x,y):
    x,y=np.asarray(x,dtype=float),np.asarray(y,dtype=float)
    if x.shape!=y.shape or x.ndim!=1 or len(x)<2 or not np.all(np.isfinite(x-y)):
        raise ValueError('Finite, aligned paired samples are required')
    difference=x-y
    if np.std(difference,ddof=1)==0:
        raise ValueError('A t-test is undefined for constant paired differences')
    result=stats.ttest_rel(x,y,nan_policy='raise')
    ci=result.confidence_interval(.95)
    return dict(n=len(x),mean_difference=float(np.mean(difference)),t=float(result.statistic),
                df=int(result.df),mean_difference_ci95=[float(ci.low),float(ci.high)],
                standard_error=float(stats.sem(difference)),**p_fields(result.pvalue))


def mcnemar(x,y,left='candidate',right='agent'):
    x,y=np.asarray(x,dtype=bool),np.asarray(y,dtype=bool)
    if x.shape!=y.shape:
        raise ValueError('Paired outcomes must align')
    wins=int(np.sum(x&~y))
    losses=int(np.sum(~x&y))
    p=1.0 if wins+losses==0 else stats.binomtest(wins,wins+losses,.5,alternative='two-sided').pvalue
    return dict(both_correct=int(np.sum(x&y)),both_wrong=int(np.sum(~x&~y)),
                discordant=wins+losses,method_a=left,method_b=right,
                **{left+'_only_correct':wins,right+'_only_correct':losses},**p_fields(p))


def cluster_mean_test(difference,labels,null=0,alternative='two-sided'):
    """Intercept-only CR1 cluster SE; t reference with G-1 degrees of freedom."""
    difference=np.asarray(difference,dtype=float)
    groups=[np.flatnonzero(np.asarray(labels)==label) for label in sorted(set(labels))]
    mean=float(np.mean(difference))
    scores=np.array([np.sum(difference[g]-mean) for g in groups])
    variance=len(groups)/(len(groups)-1)*np.sum(scores**2)/len(difference)**2
    se=float(np.sqrt(variance))
    if se==0:
        raise ValueError('Cluster SE is zero')
    t=(mean-null)/se
    df=len(groups)-1
    p=2*stats.t.sf(abs(t),df) if alternative=='two-sided' else stats.t.sf(t,df) if alternative=='greater' else stats.t.cdf(t,df)
    q=stats.t.ppf(.975,df)
    return dict(n=len(difference),clusters=len(groups),df=df,mean=mean,standard_error=se,
                t=float(t),null=null,alternative=alternative,ci95=[float(mean-q*se),float(mean+q*se)],
                one_sided_95_lower=float(mean-stats.t.ppf(.95,df)*se),**p_fields(p))


def bootstrap(correct,baseline,cost,base_cost,labels,reps,seed):
    """Paired within-intent resampling and whole-intent resampling sensitivities."""
    labels=np.asarray(labels)
    groups=[np.flatnonzero(labels==label) for label in sorted(set(labels))]
    rng=np.random.default_rng(seed)
    draws={'accuracy_difference':[],'cost_difference':[],'cost_reduction':[]}
    for offset in range(0,reps,128):
        count=min(128,reps-offset)
        ids=np.concatenate([rng.choice(g,size=(count,len(g)),replace=True) for g in groups],axis=1)
        draws['accuracy_difference'].extend(np.mean((correct-baseline)[ids],axis=1))
        draws['cost_difference'].extend(np.mean((cost-base_cost)[ids],axis=1))
        draws['cost_reduction'].extend(1-np.sum(cost[ids],axis=1)/np.sum(base_cost[ids],axis=1))
    cluster_ids=rng.integers(0,len(groups),size=(reps,len(groups)))
    totals=np.array([[np.sum(correct[g]-baseline[g]),np.sum(cost[g]-base_cost[g]),
                      np.sum(cost[g]),np.sum(base_cost[g]),len(g)] for g in groups])
    sampled=np.sum(totals[cluster_ids],axis=1)
    clustered={'accuracy_difference':sampled[:,0]/sampled[:,4],
               'cost_difference':sampled[:,1]/sampled[:,4],
               'cost_reduction':1-sampled[:,2]/sampled[:,3]}
    def summarize(values):
        return {k:dict(ci95=[float(v) for v in np.quantile(v,[.025,.975])],
                       one_sided_95_lower=float(np.quantile(v,.05))) for k,v in values.items()}
    return dict(replicates=reps,seed=seed,within_intent=summarize(draws),intent_cluster=summarize(clustered))


def random_gains(delta,k,reps,rng):
    """Exact sampling of the {-1,0,1} gain sum in k uniformly chosen IDs."""
    delta=np.asarray(delta)
    if not np.all(np.isin(delta,[-1,0,1])) or not 0<=k<=len(delta):
        raise ValueError('Binary paired gains and valid sample size required')
    if k in (0,len(delta)):
        return np.full(reps,0 if k==0 else np.sum(delta),dtype=int)
    pos=int(np.sum(delta==1));neg=int(np.sum(delta==-1));zero=len(delta)-pos-neg
    positives=rng.hypergeometric(pos,neg+zero,k,size=reps)
    remaining=k-positives
    negatives=np.zeros(reps,dtype=int) if neg==0 else remaining if zero==0 else rng.hypergeometric(neg,zero,remaining)
    return positives-negatives


def randomization(jev_correct,agent_correct,candidate_correct,mask,labels,reps,seed):
    delta=jev_correct-agent_correct
    observed=int(np.sum(candidate_correct-agent_correct))
    rng=np.random.default_rng(seed)
    gains=random_gains(delta,int(np.sum(mask)),reps,rng)
    stratified=np.zeros(reps,dtype=int)
    labels=np.asarray(labels)
    for label in sorted(set(labels)):
        group=labels==label
        stratified+=random_gains(delta[group],int(np.sum(mask[group])),reps,rng)
    def summarize(draws):
        extreme=int(np.sum(draws>=observed))
        return dict(observed_accuracy=float(np.mean(candidate_correct)),
                    random_mean_accuracy=float(np.mean(agent_correct)+np.mean(draws)/len(delta)),
                    exceedances=extreme,replicates=reps,plus_one_p=(extreme+1)/(reps+1),
                    note='Monte Carlo randomization p=(exceedances+1)/(replicates+1), not an exact tail probability or a population guarantee.')
    return dict(seed=seed,matched_total_coverage=summarize(gains),
                matched_coverage_within_each_intent=summarize(stratified))


def holm(pvalues):
    order=sorted(pvalues,key=pvalues.get)
    adjusted={}
    running=0
    for rank,key in enumerate(order):
        running=max(running,min(1,(len(order)-rank)*pvalues[key]))
        adjusted[key]=running
    return adjusted


def load_pairs():
    frozen=i.read(i.ROOT/'intent_frozen.json')
    for path,key in [('intent_probe.py','source_sha256'),('intent_native.py','native_sha256')]:
        if i.digest((i.ROOT/path).read_bytes())!=frozen[key]:
            raise RuntimeError('Frozen source changed: '+path)
    if i.protocol_signature()!=frozen['signature']:
        raise RuntimeError('Frozen data/protocol signature mismatch')
    ids=sorted(frozen['test_ids'])
    rows={r['id']:r for r in i.read(i.CACHE/'test.json')}
    records={c:i.results('test',c) for c in ('jev','direct','agent')}
    if any(set(rs)!=set(ids) for rs in records.values()):
        raise RuntimeError('Complete one-to-one frozen trajectories are required')
    gold=[rows[k]['label'] for k in ids]
    prepared={}
    for c,rs in records.items():
        prepared[c]=[]
        for k in ids:
            r=rs[k]
            if r['signature']!=frozen['signature'] or r['input_hash']!=i.digest(rows[k]['text']):
                raise RuntimeError('Mismatched paired trajectory: '+k)
            prepared[c].append(dict(r,prediction=r['prediction'] if r['status']=='complete' else None))
    threshold=i.read(i.ROOT/'intent_analysis_plan.json')['fixed_uncertified_candidate']['threshold']
    mask=np.array([i.accepted(r,threshold) for r in prepared['jev']])
    values={c:dict(correct=np.array([r['prediction']==g for r,g in zip(rs,gold)],dtype=float),
                   cost=np.array([r['cost_usd'] for r in rs])) for c,rs in prepared.items()}
    routed=a.compose(prepared['jev'],prepared['agent'],mask)
    values['cascade']=dict(correct=np.array([p==g for p,g in zip(routed['pred'],gold)],dtype=float),cost=np.array(routed['cost']))
    original=i.read(i.ROOT/'intent_evidence.json')
    for key,original_key in [('jev','jev'),('direct','direct'),('agent','agent'),('cascade','candidate_uncertified')]:
        assert abs(np.mean(values[key]['correct'])-original['metrics'][original_key]['accuracy'])<1e-12
        assert abs(np.mean(values[key]['cost'])-original['metrics'][original_key]['mean_usd'])<1e-12
    return frozen,ids,[rows[k] for k in ids],values,mask,original


def analysis(reps=10000,permutations=20000,seed=32977):
    frozen,ids,rows,values,mask,original=load_pairs()
    candidate,agent=values['cascade'],values['agent']
    d=candidate['correct']-agent['correct']
    cost_delta=candidate['cost']-agent['cost']
    accuracy=t_test(candidate['correct'],agent['correct'])
    cost=t_test(candidate['cost'],agent['cost'])
    adjusted=holm({'accuracy':accuracy['pvalue'],'cost':cost['pvalue'] or cost['pvalue_upper_bound']})
    for key,value in [('accuracy',accuracy),('cost',cost)]:
        value['holm_two_endpoint_family']=(dict(pvalue=None,pvalue_upper_bound=adjusted[key],
            p_text=f'<{adjusted[key]:.6g}',numerical_underflow=True)
            if value['numerical_underflow'] else p_fields(adjusted[key]))
    margin=frozen['analysis']['accuracy_margin']
    ni=stats.ttest_1samp(d,-margin,alternative='greater')
    cost_target=stats.ttest_1samp(candidate['cost']-(1-frozen['analysis']['cost_reduction_target'])*agent['cost'],0,alternative='less')
    labels=[r['label'] for r in rows]
    cluster_accuracy=cluster_mean_test(d,labels)
    cluster_cost=cluster_mean_test(cost_delta,labels)
    cluster_adjusted=holm({'accuracy':cluster_accuracy['pvalue'],'cost':cluster_cost['pvalue']})
    cluster_accuracy['holm_two_endpoint_family']=p_fields(cluster_adjusted['accuracy'])
    cluster_cost['holm_two_endpoint_family']=p_fields(cluster_adjusted['cost'])
    ci=bootstrap(candidate['correct'],agent['correct'],candidate['cost'],agent['cost'],labels,reps,seed)
    support_norm={i.normalize(r['text']) for r in i.read(i.CACHE/'support.json')}
    clean=np.array([i.normalize(r['text']) not in support_norm for r in rows])
    unique=[];seen=set()
    for n,r in enumerate(rows):
        norm=i.normalize(r['text'])
        if norm not in seen:
            unique.append(n);seen.add(norm)
    secondary={}
    for name,other in [('jev_only_vs_agent',values['jev']),('cascade_vs_direct',values['direct'])]:
        lhs=values['jev'] if name.startswith('jev_only') else candidate
        rhs=agent if name.startswith('jev_only') else other
        secondary[name]=dict(accuracy=t_test(lhs['correct'],rhs['correct']),
            exact_mcnemar=mcnemar(lhs['correct'],rhs['correct'],
                left='jev_only' if name.startswith('jev_only') else 'cascade',
                right='agent' if name.startswith('jev_only') else 'direct'),cost=t_test(lhs['cost'],rhs['cost']))
    secondary_adjust=holm({k:v['exact_mcnemar']['pvalue'] or v['exact_mcnemar']['pvalue_upper_bound'] for k,v in secondary.items()})
    for key in secondary:
        secondary[key]['exact_mcnemar_holm_secondary_family']=p_fields(secondary_adjust[key])
    result=dict(analysis_kind='Post-hoc user-requested inference on unchanged frozen trajectories; not a new pre-registered experiment.',
        comparison='Fixed 0.96 Jev cascade (uncertified) minus always-native retrieval Sol agent',
        n=len(ids),signature=frozen['signature'],threshold=frozen['selected_threshold'],
        point_estimates=dict(cascade_accuracy=float(np.mean(candidate['correct'])),agent_accuracy=float(np.mean(agent['correct'])),
            accuracy_difference=float(np.mean(d)),cascade_usd_per_query=float(np.mean(candidate['cost'])),
            agent_usd_per_query=float(np.mean(agent['cost'])),cost_difference_usd=float(np.mean(cost_delta)),
            cost_reduction=float(1-np.sum(candidate['cost'])/np.sum(agent['cost'])),coverage=float(np.mean(mask))),
        requested_paired_t_tests=dict(accuracy=accuracy,cost=cost),exact_accuracy_mcnemar=mcnemar(candidate['correct'],agent['correct']),
        noninferiority=dict(null='Mean cascade-minus-agent accuracy <= -0.02',margin=margin,t=float(ni.statistic),df=int(ni.df),
            one_sided_95_lower=float(np.mean(d)-stats.t.ppf(.95,len(d)-1)*stats.sem(d)),**p_fields(ni.pvalue)),
        cost_reduction_at_least_30pct=dict(null='Mean cascade cost >= 0.70 * mean agent cost',t=float(cost_target.statistic),df=int(cost_target.df),**p_fields(cost_target.pvalue)),
        bootstrap=ci,
        intent_cluster_sensitivity=dict(accuracy=cluster_accuracy,cost=cluster_cost,
            noninferiority=cluster_mean_test(d,labels,null=-margin,alternative='greater')),
        support_nonoverlap=dict(n=int(np.sum(clean)),accuracy=t_test(candidate['correct'][clean],agent['correct'][clean]),
            exact_mcnemar=mcnemar(candidate['correct'][clean],agent['correct'][clean]),cost=t_test(candidate['cost'][clean],agent['cost'][clean])),
        unique_normalized_utterances=dict(n=len(unique),removed=len(rows)-len(unique),
            accuracy=t_test(candidate['correct'][unique],agent['correct'][unique]),
            exact_mcnemar=mcnemar(candidate['correct'][unique],agent['correct'][unique])),
        randomization=randomization(values['jev']['correct'],agent['correct'],candidate['correct'],mask,labels,permutations,seed+1),
        secondary_comparisons=secondary,certification_unchanged=original['certification'],new_model_calls=0,new_model_spend_usd=0,
        versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        inputs=dict(frozen_sha256=i.digest((i.ROOT/'intent_frozen.json').read_bytes()),
                    statistics_source_sha256=i.digest(Path(__file__).read_bytes()),
                    original_evidence_sha256=i.digest((i.ROOT/'intent_evidence.json').read_bytes()),
                    analysis_plan_sha256=i.digest((i.ROOT/'intent_analysis_plan.json').read_bytes()),
                    paired_data_sha256=i.digest([dict(id=k,gold=r['label'],jev_correct=float(values['jev']['correct'][n]),
                        cascade_correct=float(candidate['correct'][n]),agent_correct=float(agent['correct'][n]),
                        cascade_cost=float(candidate['cost'][n]),agent_cost=float(agent['cost'][n])) for n,(k,r) in enumerate(zip(ids,rows))])))
    i.dump(i.ROOT/'intent_significance.json',result)
    write_report(result)
    return result


def write_report(r):
    point=r['point_estimates'];tests=r['requested_paired_t_tests'];mc=r['exact_accuracy_mcnemar']
    bootstrap=r['bootstrap'];cluster=r['intent_cluster_sensitivity'];ni=r['noninferiority']
    def interval(values,scale=1):
        return f'{scale*values[0]:.3f} to {scale*values[1]:.3f}'
    cost_ci=tests['cost']['mean_difference_ci95']
    random=r['randomization']
    text=f'''# Paired statistical analysis: Jev cascade versus retrieval Sol

The fixed 0.96 cascade is **significantly cheaper and slightly less accurate** than always using the retrieval agent. The loss is small enough to meet the originally specified two-percentage-point margin. These are compatible conclusions: a detectable loss can still be within a practical tolerance. We cannot claim equal accuracy or successful risk certification.

This is a **post-hoc follow-up requested after the main results were observed**. It reuses the same {r['n']:,} frozen paired questions, predictions, threshold and receipts. No test example, gate or model was changed; no new model calls or spending occurred. The two requested t-tests use questions as paired observations. Holm correction controls their two-endpoint family; both remain significant. Additional tests below are labeled sensitivity or secondary analyses.

## Requested paired t-tests

- **Accuracy:** {100*point['cascade_accuracy']:.2f}% cascade versus {100*point['agent_accuracy']:.2f}% agent; difference **{100*point['accuracy_difference']:.3f} percentage points**. Paired t({tests['accuracy']['df']}) = {tests['accuracy']['t']:.4f}, two-sided p = **{tests['accuracy']['p_text']}**, Holm-adjusted p = {tests['accuracy']['holm_two_endpoint_family']['p_text']}. The t-based 95% difference interval is {interval(tests['accuracy']['mean_difference_ci95'],100)} points. The difference favors the always-agent condition.
- **Cost:** ${point['cascade_usd_per_query']:.6f} versus ${point['agent_usd_per_query']:.6f} per query; difference **${point['cost_difference_usd']:.6f}/query**. Paired t({tests['cost']['df']}) = {tests['cost']['t']:.4f}, two-sided **p {tests['cost']['p_text']}** (numerical underflow; not p=0). The mean savings are ${-1000*point['cost_difference_usd']:.3f} per 1,000 queries, with 95% t interval ${-1000*cost_ci[1]:.3f}–${-1000*cost_ci[0]:.3f}. This tests no mean cost difference, not whether the reduction equals exactly 59%.

Relative savings are defined as **1 − mean(cascade cost)/mean(agent cost)**, not the average of per-question percentages. Observed reduction: **{100*point['cost_reduction']:.2f}%**. The {bootstrap['replicates']:,}-replicate paired within-intent bootstrap 95% interval is **{interval(bootstrap['within_intent']['cost_reduction']['ci95'],100)}%**. Resampling whole intents gives **{interval(bootstrap['intent_cluster']['cost_reduction']['ci95'],100)}%**. Neither interval includes zero or the originally specified 30% savings target.

## Exact accuracy check and practical tolerance

Accuracy is binary, so the exact paired McNemar test is a more natural check than a normal approximation. The cascade alone is correct on **{mc['candidate_only_correct']}** questions; the agent alone on **{mc['agent_only_correct']}**. Both are correct on {mc['both_correct']}; both wrong on {mc['both_wrong']}. The exact two-sided p-value is **{mc['p_text']}**, confirming the small accuracy loss. Questions on which both methods agree do not drive this test.

The two-point accuracy margin was specified before test collection. Testing H0: accuracy(cascade) − accuracy(agent) ≤ −0.02 against a larger difference gives one-sided p = **{ni['p_text']}**. The one-sided 95% t lower bound is **{100*ni['one_sided_95_lower']:.3f} points**, above −2. Whole-intent cluster inference gives a lower bound of **{100*cluster['noninferiority']['one_sided_95_lower']:.3f} points** and p = {cluster['noninferiority']['p_text']}. This supports noninferiority relative to that chosen margin, not equivalence. The original analysis, using a bootstrap rule specified before test collection, is preserved unchanged in intent_evidence.json.

## Dependence and data sensitivity

Similar questions within an intent may be dependent. We therefore use an intercept-only CR1 cluster standard error with intents as {cluster['accuracy']['clusters']} clusters and a t reference with {cluster['accuracy']['df']} degrees of freedom. At equal class sizes this is equivalent to a paired t-test on the 77 intent-level mean differences. The cluster accuracy p-value is **{cluster['accuracy']['p_text']}**, with 95% interval **{interval(cluster['accuracy']['ci95'],100)} points**. The cluster cost p-value is **{cluster['cost']['p_text']}**. The whole-intent bootstrap gives an accuracy-difference interval of **{interval(bootstrap['intent_cluster']['accuracy_difference']['ci95'],100)} points**. This permits dependence within intents but still assumes independent intent clusters; it is a sensitivity analysis, not proof of generalization to unseen banking domains.

Excluding normalized support/test overlap leaves {r['support_nonoverlap']['n']:,} questions; exact McNemar p = {r['support_nonoverlap']['exact_mcnemar']['p_text']}. Keeping one deterministic row per normalized test utterance leaves {r['unique_normalized_utterances']['n']:,}, removing {r['unique_normalized_utterances']['removed']} duplicates; exact p = {r['unique_normalized_utterances']['exact_mcnemar']['p_text']}. Neither operation alters the primary official-test result.

## Does confidence help beyond accepting a random subset?

We shuffle the acceptance mask while retaining the same accepted count, condition on the existing Jev/agent predictions, and ask whether a random mask reaches at least the observed cascade accuracy. Among {random['matched_total_coverage']['replicates']:,} random masks, {random['matched_total_coverage']['exceedances']} match or exceed it; plus-one Monte Carlo p = {random['matched_total_coverage']['plus_one_p']:.6g}. A stricter shuffle preserves each intent's accepted count, testing whether selection helps within intents rather than only choosing easy categories: {random['matched_coverage_within_each_intent']['exceedances']} exceedances; p = {random['matched_coverage_within_each_intent']['plus_one_p']:.6g}. These are finite Monte Carlo p-values at the reported resolution, not exact tiny tail probabilities. They support confidence-based selection on these recorded trajectories, not a calibrated 5% risk guarantee.

## Other comparators and limits

The supplemental JSON includes Jev-only versus the retrieval agent, and the cascade versus direct Sol, each with paired t-tests and exact McNemar tests. Their two exact accuracy tests receive a separate Holm correction. They distinguish the cheap standalone classifier from the cascade and keep the lower-cost direct baseline visible. They are secondary analyses, not independent replications.

The certification failure remains unchanged: its one-sided upper accepted-error bound was 5.157%, above 5%. Later tests cannot erase it. Statistical significance does not certify safety, establish zero quality loss, or account for future model/provider changes. There is one model rollout per example; inference concerns variability across comparable questions, not uncertainty in these already observed finite-benchmark totals. Cached common fallback trajectories produce the intended pairing. Dollar results include Jev overhead and actual fallback charges; current cache exposure and provider prices may not transfer to a different deployment. Latency was collected under parallel load or on only 12 live development cases, so no deployed-latency significance claim is added.

## Reproduction and references

Install requirements-intent-stats.txt, prepare the pinned data, and unpack the existing intent_runs.tar.xz archive. Run `python3 intent_significance.py`; `--figures` optionally uses matplotlib 3.11.2. Results are intent_significance.json and this report. Seeds, input hashes, exact contingencies and package versions are recorded. The original evidence, source fingerprints and archive remain unchanged.

Methods: [SciPy paired t-test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_rel.html), [SciPy one-sample/one-sided tests](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_1samp.html), [statsmodels exact McNemar documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html), [cluster covariance documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html). The exact McNemar calculation uses SciPy's binomial test on discordant counts, avoiding an additional statsmodels dependency.

AI-use disclosure: Rami requested this follow-up; Codex implemented the offline tests and drafted the interpretation. Team review is required before incorporation into the final paper.
'''
    (i.ROOT/'report/intent_statistics.md').write_text(text)
    def tex_p(value):
        mantissa,exponent=f'{value:.2e}'.split('e')
        return mantissa+rf'\times 10^{{{int(exponent)}}}'
    tex=rf'''% Supplemental post-hoc tests on the unchanged frozen BANKING77 records.
\paragraph{{Paired significance analysis.}}
The fixed, uncertified cascade scored {100*point['cascade_accuracy']:.2f}\% versus
{100*point['agent_accuracy']:.2f}\% for the retrieval agent.
The {100*abs(point['accuracy_difference']):.2f}-percentage-point loss was significant
(paired $t({tests['accuracy']['df']})={tests['accuracy']['t']:.2f}$,
$p={tex_p(tests['accuracy']['pvalue'])}$; exact McNemar $p={tex_p(mc['pvalue'])}$,
{mc['candidate_only_correct']} cascade-only versus {mc['agent_only_correct']} agent-only successes).
The one-sided 95\% lower difference bound was
{100*ni['one_sided_95_lower']:.2f} points, above the prespecified $-2$-point margin.
Mean cost fell {100*point['cost_reduction']:.2f}\%
(paired bootstrap 95\% CI {100*bootstrap['within_intent']['cost_reduction']['ci95'][0]:.2f}--{100*bootstrap['within_intent']['cost_reduction']['ci95'][1]:.2f}\%;
paired $t({tests['cost']['df']})={tests['cost']['t']:.2f}$, $p<10^{{-300}}$).
Thus the evidence supports a cheaper method with a small measurable quality loss,
not equal accuracy. These additional tests were requested after observing the main
results; the threshold and trajectories were unchanged. The independent 5\% risk
certification still failed and is not superseded by these tests.
'''
    (i.ROOT/'report/intent_statistics.tex').write_text(tex)


def figures(r):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    b=r['bootstrap'];t=r['requested_paired_t_tests'];c=r['intent_cluster_sensitivity']
    fig,axes=plt.subplots(1,2,figsize=(10.5,3.5),layout='constrained')
    fig.suptitle('Fixed 0.96 cascade (uncertified): 95% intervals',fontsize=12)
    intervals=[t['accuracy']['mean_difference_ci95'],b['within_intent']['accuracy_difference']['ci95'],
               c['accuracy']['ci95'],b['intent_cluster']['accuracy_difference']['ci95']]
    labels=['Paired t','Within-intent bootstrap','Intent-cluster t','Intent-cluster bootstrap']
    mean=100*r['point_estimates']['accuracy_difference']
    for n,(bounds,label) in enumerate(zip(intervals,labels)):
        axes[0].errorbar([mean],[n],xerr=[[mean-100*bounds[0]],[100*bounds[1]-mean]],fmt='o',capsize=4,color='#467da6')
    axes[0].set_yticks(range(4),labels)
    axes[0].axvline(0,color='#666666',lw=1)
    axes[0].axvline(-2,ls='--',color='#b24b48',label='Prespecified −2-point margin')
    axes[0].set(xlabel='Cascade − agent accuracy (percentage points)',title='Small measurable accuracy loss')
    axes[0].legend(fontsize=8,loc='upper left')
    axes[0].set_ylim(-.5,4)
    mean=100*r['point_estimates']['cost_reduction']
    for n,key in enumerate(['within_intent','intent_cluster']):
        bounds=b[key]['cost_reduction']['ci95']
        axes[1].errorbar([mean],[n],xerr=[[mean-100*bounds[0]],[100*bounds[1]-mean]],fmt='o',capsize=4,color='#309584')
    axes[1].set_yticks(range(2),['Within-intent bootstrap','Intent-cluster bootstrap'])
    axes[1].axvline(0,color='#666666',lw=1)
    axes[1].axvline(30,ls='--',color='#b24b48',label='Prespecified 30% target')
    axes[1].set(xlabel='Relative cost reduction (%)',title='Large cost reduction')
    axes[1].legend(fontsize=8,loc='upper left')
    axes[1].set_ylim(-.15,1.8)
    for ax in axes:
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='x',alpha=.15)
    for suffix in ('png','pdf'):
        fig.savefig(i.ROOT/f'report/intent_figures/statistical_intervals.{suffix}',dpi=180)
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figures',action='store_true')
    args=parser.parse_args()
    r=analysis()
    if args.figures:
        figures(r)
    print({k:r[k] for k in ('point_estimates','requested_paired_t_tests','exact_accuracy_mcnemar','intent_cluster_sensitivity')})
