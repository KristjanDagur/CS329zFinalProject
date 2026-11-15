"""Reproduce the evidence-matched study offline; no API calls or gate fitting."""
import argparse, collections, json, platform, time
import numpy as np
import scipy, sklearn
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
import intent_probe as i
import intent_analysis as a
import intent_significance as s
import retrieval_probe as r

NAMES={'jev_static':'Jev, static catalog','sol_static':'Sol, static catalog',
       'jev_retrieved':'Jev + fixed retrieval','sol_retrieved':'Sol + fixed retrieval',
       'agent':'Native retrieval agent','tfidf_svm':'TF-IDF + linear SVM'}


def classical():
    """Support-only fit; fixed settings, no tuning. Preserve measured training timing."""
    dest=r.RUNS/'classical.json'
    params=r.P['classical_baseline']
    support=i.read(i.CACHE/'support.json')
    frozen=i.read(i.ROOT/'retrieval_frozen.json')
    source_hash=i.digest(dict(params=params,support=support,test_ids=frozen['test_ids'],
                             sklearn=sklearn.__version__,fit_definition='tfidf-word-char-linear-svc-v1'))
    if dest.exists():
        saved=i.read(dest)
        if saved['fit_input_hash']!=source_hash:
            raise RuntimeError('Saved classical baseline inputs changed')
        return saved
    rows={x['id']:x for x in i.read(i.CACHE/'test.json')}
    features=FeatureUnion([
        ('word',TfidfVectorizer(ngram_range=tuple(params['word_ngram_range']),min_df=params['min_df'],max_features=params['max_features_per_view'],sublinear_tf=True)),
        ('char',TfidfVectorizer(analyzer='char_wb',ngram_range=tuple(params['char_ngram_range']),min_df=params['min_df'],max_features=params['max_features_per_view'],sublinear_tf=True))])
    model=Pipeline([('features',features),('classifier',LinearSVC(C=params['C'],max_iter=params['max_iter'],random_state=r.P['seed']))])
    started=time.monotonic()
    model.fit([x['text'] for x in support],[x['label'] for x in support])
    train_s=time.monotonic()-started
    started=time.monotonic()
    pred=model.predict([rows[k]['text'] for k in frozen['test_ids']])
    predict_s=time.monotonic()-started
    saved=dict(fit_input_hash=source_hash,params=params,sklearn=sklearn.__version__,
               training_rows=len(support),training_wall_s=train_s,prediction_batch_wall_s=predict_s,
               prediction=dict(zip(frozen['test_ids'],pred.tolist())),api_usd=0,
               note='All support labels used for supervised training. API cost zero; local compute is reported in seconds, not priced as free deployment.')
    i.dump(dest,saved)
    return saved


def aligned():
    frozen=i.read(i.ROOT/'retrieval_frozen.json')
    if frozen['signature']!=r.signature():
        raise RuntimeError('Collection signature mismatch')
    rows={x['id']:x for x in i.read(i.CACHE/'test.json')}
    ids=frozen['test_ids']
    records={c:r.results('test',c) for c in r.CONDITIONS}
    for c,rs in records.items():
        if set(rs)!=set(ids):
            raise RuntimeError('Missing/extra frozen results: '+c)
        for k in ids:
            if rs[k]['signature']!=frozen['signature'] or rs[k]['input_hash']!=i.digest(rows[k]['text']):
                raise RuntimeError('Input signature mismatch')
    support_ids={x['id'] for x in i.read(i.CACHE/'support.json')}
    for k in ids:
        for c in ('jev_retrieved','sol_retrieved'):
            ev=i.read(r.RUNS/r.signature()[:16]/'test'/k/c/'fixed_evidence.json')
            if not {x['support_id'] for x in ev}<=support_ids or i.digest(ev)!=records[c][k]['evidence_hash']:
                raise RuntimeError('Retrieval evidence provenance failed')
        if records['jev_retrieved'][k]['evidence_hash']!=records['sol_retrieved'][k]['evidence_hash']:
            raise RuntimeError('Different evidence supplied to the two models')
    return frozen,ids,rows,records


def safe_cluster(delta,labels,**kwargs):
    if not np.any(delta):
        return dict(mean=0,ci95=[0,0],pvalue=1,one_sided_95_lower=0,note='Identical paired outcomes')
    return s.cluster_mean_test(delta,labels,**kwargs)


def build():
    frozen,ids,rows,records=aligned()
    gold=[rows[k]['label'] for k in ids]
    labels=np.asarray(gold)
    correct={c:np.array([int(rs[k]['status']=='complete' and rs[k]['prediction']==rows[k]['label']) for k in ids]) for c,rs in records.items()}
    costs={c:np.array([rs[k]['cost_usd'] for k in ids]) for c,rs in records.items()}
    metrics={}
    for c,rs in records.items():
        metrics[c]=a.metrics(gold,[rs[k]['prediction'] if rs[k]['status']=='complete' else None for k in ids],
                             costs[c].tolist(),[rs[k]['elapsed_s'] for k in ids],sorted(set(gold)),[rs[k]['calls'] for k in ids])
        metrics[c]['failed']=sum(rs[k]['status']!='complete' for k in ids)
    cb=classical()
    metrics['tfidf_svm']=a.metrics(gold,[cb['prediction'][k] for k in ids],[0]*len(ids),[],sorted(set(gold)))
    comparisons={}
    pairs=r.P['analysis']['primary_accuracy_comparisons']
    # The final pair is a secondary cost/quality contrast, outside the four-test primary family.
    for left,right in pairs+[['jev_retrieved','agent']]:
        name=left+'__'+right
        delta=correct[left]-correct[right]
        comparisons[name]=dict(left=left,right=right,primary=[left,right] in pairs,
            accuracy_difference=float(np.mean(delta)),cost_reduction=float(1-costs[left].mean()/costs[right].mean()),
            exact_mcnemar=s.mcnemar(correct[left],correct[right],left,right),
            bootstrap=s.bootstrap(correct[left],correct[right],costs[left],costs[right],labels,
                                  r.P['analysis']['bootstrap_replicates'],r.P['analysis']['bootstrap_seed']),
            cluster_accuracy=safe_cluster(delta,labels))
        if right=='agent':
            comparisons[name]['secondary_noninferiority_2pp']=safe_cluster(delta,labels,null=-.02,alternative='greater')
    adjusted=s.holm({k:v['exact_mcnemar']['pvalue'] for k,v in comparisons.items() if v['primary']})
    for k,p in adjusted.items():
        comparisons[k]['holm_p']=p
    interaction=(correct['jev_retrieved']-correct['jev_static'])-(correct['sol_retrieved']-correct['sol_static'])
    overlap={i.normalize(x['text']) for x in i.read(i.CACHE/'support.json')}
    clean=np.array([i.normalize(rows[k]['text']) not in overlap for k in ids])
    per_intent={label:{c:float(np.mean(v[labels==label])) for c,v in correct.items()} for label in sorted(set(gold))}
    errors=[]
    for j,k in enumerate(ids):
        if not correct['jev_retrieved'][j] or not correct['sol_retrieved'][j]:
            errors.append(dict(id=k,text=rows[k]['text'],gold=gold[j],
                               predictions={c:rs[k]['prediction'] for c,rs in records.items()},
                               support_overlap=not bool(clean[j])))
    providers=collections.defaultdict(set)
    token_summary={c:dict(prompt=0,completion=0,cached=0,uncached_token_price_usd=0.0) for c in r.CONDITIONS}
    for rec in i.read(r.RUNS/'ledger_export.json'):
        if '/test/' not in rec['job'] or rec['state']!='complete':
            continue
        c=rec['job'].split('/')[-1]
        receipt=rec['receipt']; usage=receipt.get('usage',{})
        providers[rec['model']].add(str(receipt.get('provider')))
        pricing=frozen['models'][rec['model']]['pricing']
        t=token_summary[c]
        t['prompt']+=usage.get('prompt_tokens',0)
        t['completion']+=usage.get('completion_tokens',0)
        t['cached']+=(usage.get('prompt_tokens_details') or {}).get('cached_tokens',0)
        t['uncached_token_price_usd']+=usage.get('prompt_tokens',0)*float(pricing['prompt'])+usage.get('completion_tokens',0)*float(pricing['completion'])
    live={c:r.results('live',c) for c in r.CONDITIONS}
    timing={}
    if all(set(v)==set(frozen['live_ids']) for v in live.values()):
        lid=frozen['live_ids']; rng=np.random.default_rng(r.P['seed']+1)
        draws=rng.integers(0,len(lid),size=(10000,len(lid)))
        for c,rs in live.items():
            lat=np.array([rs[k]['elapsed_s'] for k in lid])
            base=np.array([live['agent'][k]['elapsed_s'] for k in lid])
            timing[c]=dict(n=len(lid),mean_s=float(np.mean(lat)),p50_s=float(np.median(lat)),p95_s=float(np.quantile(lat,.95)),
                           mean_difference_vs_agent_s=float(np.mean(lat-base)),
                           paired_mean_difference_ci95=[float(v) for v in np.quantile(np.mean((lat-base)[draws],axis=1),[.025,.975])],
                           failures=sum(x['status']!='complete' for x in rs.values()))
    old={c:i.results('test',p) for c,p in [('jev_static','jev'),('sol_static','direct'),('agent','agent')]}
    replication={c:dict(old_accuracy=float(np.mean([rs[k]['prediction']==rows[k]['label'] for k in ids])),
                        changed_predictions=sum(rs[k]['prediction']!=records[c][k]['prediction'] for k in ids)) for c,rs in old.items()}
    data=dict(signature=frozen['signature'],analysis_source_sha256=i.digest((i.ROOT/'retrieval_analysis.py').read_bytes()),
              versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__),
              n=len(ids),metrics=metrics,comparisons=comparisons,secondary_evidence_interaction=safe_cluster(interaction,labels),
              nonoverlap=dict(n=int(clean.sum()),accuracy={c:float(v[clean].mean()) for c,v in correct.items()}),
              per_intent=per_intent,errors=errors,classical=cb,token_accounting=token_summary,
              observed_providers={k:sorted(v) for k,v in providers.items()},serial_live_latency=timing,
              replication_vs_original=replication,ledger=i.read(r.RUNS/'ledger_export.json'),
              limitations=r.P['analysis']['test_status'])
    # Store a compact ledger summary, not duplicate all raw receipts in the result artifact.
    ledger=data.pop('ledger')
    data['spend']=dict(accounted_usd=sum(x['amount'] for x in ledger),
                       billed_usd=sum(x['amount'] for x in ledger if x['state']=='complete'),
                       unresolved_usd=sum(x['amount'] for x in ledger if x['state'] in ('unresolved','reserved')),
                       phases={p:sum(x['amount'] for x in ledger if x['phase']==p) for p in ('development','test','live')})
    i.dump(i.ROOT/'retrieval_evidence.json',data)
    report(data)
    print(json.dumps(dict(n=data['n'],metrics={c:dict(accuracy=v['accuracy'],mean_usd=v['mean_usd'],failed=v.get('failed')) for c,v in metrics.items()},spend=data['spend']),indent=2))
    return data


def report(d):
    lines=['# Does fixed retrieval replace the retrieval agent?','',
           'Exploratory follow-up on the previously examined BANKING77 test set. Protocol and new collection were frozen before new outcomes. Original results and failed risk certification remain unchanged.','',
           f"All {d['n']:,} frozen examples are included in each condition. Static and retrieved Jev/Sol arms were collected contemporaneously with the native agent. Fixed retrieval supplies the same eight support-only BM25 examples to both models; it never uses gold test labels or agent-generated queries.",'',
           '## Accuracy and actual API cost','',
           '| Condition | Correct | Accuracy | Mean API USD/query | Failures |',
           '|---|---:|---:|---:|---:|']
    for c,m in d['metrics'].items():
        lines.append(f"| {NAMES[c]} | {m['correct']}/{m['n']} | {100*m['accuracy']:.2f}% | {m['mean_usd']:.7f} | {m.get('failed',0)} |")
    lines+=['','The supervised TF-IDF baseline uses all 7,039 support labels for fitting, whereas the prompted static arms receive one exemplar per intent. Its API bill is zero; local compute is separate. Training took %.2f seconds and batch test prediction %.3f seconds.'%(d['classical']['training_wall_s'],d['classical']['prediction_batch_wall_s']),
            '', '## Prespecified paired comparisons','',
            'The four primary exact McNemar tests receive Holm correction. Bootstrap intervals use 10,000 paired within-intent draws; whole-intent sensitivity appears alongside them. The already observed benchmark makes these follow-up findings exploratory.']
    for key,v in d['comparisons'].items():
        ci=v['bootstrap']['within_intent']['accuracy_difference']['ci95']; cc=v['bootstrap']['intent_cluster']['accuracy_difference']['ci95']
        lines+=['',f"- **{NAMES[v['left']]} minus {NAMES[v['right']]}:** {100*v['accuracy_difference']:+.3f} percentage points; paired 95% CI [{100*ci[0]:.3f}, {100*ci[1]:.3f}], intent-cluster bootstrap [{100*cc[0]:.3f}, {100*cc[1]:.3f}]. Exact McNemar p={v['exact_mcnemar']['p_text']}"+(f"; Holm p={v['holm_p']:.6g}." if 'holm_p' in v else ' (secondary).')]
        if v['right']=='agent':
            cost_ci=v['bootstrap']['within_intent']['cost_reduction']['ci95']
            ni=v['secondary_noninferiority_2pp']
            lines[-1]+=f" Cost reduction {100*v['cost_reduction']:.2f}% (95% CI {100*cost_ci[0]:.2f}–{100*cost_ci[1]:.2f}%). Cluster one-sided 95% accuracy lower bound {100*ni['one_sided_95_lower']:.3f} points against the -2-point tolerance."
    interaction=d['secondary_evidence_interaction']
    lines+=['','## What the comparison identifies','',
            f"The secondary difference in retrieval gains (Jev gain minus Sol gain) is {100*interaction['mean']:+.3f} percentage points. This distinguishes the effect of supplying evidence within each model from a comparison of model families. The native agent can choose its queries and perform multiple calls, so its contrast with fixed retrieval measures that entire package, not reasoning alone.",
            '',f"Excluding normalized support/test overlap leaves {d['nonoverlap']['n']} examples; accuracies are "+', '.join(f'{NAMES[c]} {100*v:.2f}%' for c,v in d['nonoverlap']['accuracy'].items())+'.',
            '', '## Serial timing and price sensitivity','']
    if d['serial_live_latency']:
        for c,t in d['serial_live_latency'].items():
            lines.append(f"- {NAMES[c]}: median {t['p50_s']:.3f}s, p95 {t['p95_s']:.3f}s, mean {t['mean_s']:.3f}s; n={t['n']} fresh serial development runs.")
    else:
        lines.append('Serial timing panel pending; parallel collection times are not deployment latency estimates.')
    lines+=['','Native runtime was warmed without model calls. Serial measurements include per-query fixed retrieval and model calls but exclude server startup and index construction. The 30-example panel gives limited tail precision and is not a production load test.','']
    for c,t in d['token_accounting'].items():
        fraction=t['cached']/t['prompt'] if t['prompt'] else 0
        lines.append(f"- {NAMES[c]}: {100*fraction:.1f}% cached prompt tokens; uncached token-price sensitivity ${t['uncached_token_price_usd']/d['n']:.7f}/query.")
    lines+=['','Uncached estimates reprice recorded prompt/completion tokens at frozen list prices; they are not new cold-cache measurements or estimates of local CPU cost.',
            '', '## Limitations and reproducibility','',
            'One public closed-set dataset, one sampled rollout per test arm, and one model pair. Prior test outcomes informed the motivation for this follow-up. No new threshold, trained router or certification is fitted. The original risk-certification failure cannot be repaired by these results. Provider prices/caching and model randomness limit deployment extrapolation. Raw errors, per-intent scores, changes versus the original rollout, full uncertainty and receipts are preserved.',
            '',f"Research spend: ${d['spend']['billed_usd']:.6f} confirmed, ${d['spend']['unresolved_usd']:.6f} unresolved/reserved. No Tinker spending.",
            '', 'Install requirements-retrieval.txt, prepare the pinned original data, unpack retrieval_runs.tar.xz, then run `python3 retrieval_analysis.py`. Optional figures: `python3 retrieval_analysis.py --figures` with matplotlib 3.11.2. These commands make no paid calls.',
            '', 'AI-use disclosure: Rami authorized and directed the extension; Codex (Astra) designed the controlled comparison, implemented collection/analysis, and drafted this report. Team review is required before paper submission.','']
    (i.ROOT/'report/retrieval_results.md').write_text('\n'.join(lines))


def figures(d):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dest=i.ROOT/'report/retrieval_figures'; dest.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(9,5))
    colors={'jev_static':'#74b9ff','jev_retrieved':'#0984e3','sol_static':'#f8b86b','sol_retrieved':'#d97706','agent':'#7c3aed','tfidf_svm':'#5b6770'}
    for c,m in d['metrics'].items():
        ax.scatter(1000*m['mean_usd'],100*m['accuracy'],s=75,color=colors[c])
        ax.annotate(NAMES[c],(1000*m['mean_usd'],100*m['accuracy']),xytext=(6,6),textcoords='offset points',fontsize=8)
    for model in ('jev','sol'):
        x=[1000*d['metrics'][model+'_'+k]['mean_usd'] for k in ('static','retrieved')]
        y=[100*d['metrics'][model+'_'+k]['accuracy'] for k in ('static','retrieved')]
        ax.plot(x,y,color=colors[model+'_retrieved'],alpha=.6)
    ax.set(xlabel='Actual API USD per 1,000 queries',ylabel='Intent accuracy (%)',title='BANKING77: the value of supplying the same retrieved evidence')
    ax.margins(x=.25,y=.22); ax.grid(alpha=.18)
    fig.text(.1,.015,f"Exploratory follow-up · {d['n']:,} frozen official test examples · TF-IDF local compute excluded from API dollars",fontsize=8)
    fig.tight_layout(rect=(0,.04,1,1))
    for ext in ('png','pdf'): fig.savefig(dest/('accuracy_cost.'+ext),dpi=180)
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figures',action='store_true')
    args=parser.parse_args()
    data=build()
    if args.figures: figures(data)
