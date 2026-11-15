"""Contemporaneous evidence-matched BANKING77 experiment; original sources unchanged."""
from __future__ import annotations
import argparse, collections, concurrent.futures, datetime as dt, fcntl, json, math
import os, random, secrets, threading, time
from pathlib import Path
import intent_probe as i
from intent_native import NativePool

ROOT = i.ROOT
RUNS = ROOT / 'runs/retrieval'
P = i.read(ROOT / 'retrieval_protocol.json')
CONDITIONS = P['conditions']
SOURCES = ['retrieval_probe.py', 'retrieval_protocol.json', 'intent_probe.py',
           'intent_protocol.json', 'intent_native.py', 'intent_tools.js']


def source_hashes():
    return {n: i.digest((ROOT/n).read_bytes()) for n in SOURCES}


def signature():
    return i.digest(dict(sources=source_hashes(),
                        data={n:i.digest((i.CACHE/n).read_bytes()) for n in
                              ['support.json','development.json','test.json','catalog.json','data_receipt.json']},
                        models=i.read(RUNS/'model_snapshot.json')['models']))


def balanced(split, per_intent):
    rows=i.read(i.CACHE/(split+'.json'))
    chosen=[]
    for label in sorted({r['label'] for r in rows}):
        chosen.extend(i.ordered([r for r in rows if r['label']==label],P['seed'])[:per_intent])
    return i.ordered(chosen,P['seed'])


def snapshot(key):
    models=i.api(key,'/v1/models?output_modalities=all')['data']
    wanted={i.P['jev_model'],i.P['strong_model']}
    selected={m['id']:m for m in models if m['id'] in wanted}
    if set(selected)!=wanted:
        raise RuntimeError('Required models unavailable')
    allowance=i.api(key,'/v1/key')['data']
    safe={k:allowance.get(k) for k in ('limit','limit_remaining','usage','usage_daily')}
    if safe['limit_remaining'] is None or safe['limit_remaining'] < P['total_budget_usd']:
        raise RuntimeError('Available account allowance is below the extension cap')
    old=i.Ledger(i.RUNS/'ledger.sqlite3').status()['accounted_usd']
    if old+P['total_budget_usd'] > i.P['total_budget_usd']:
        raise RuntimeError('Extension would exceed original workstream ceiling')
    path=RUNS/'model_snapshot.json'
    if path.exists():
        raise RuntimeError('Snapshot exists; preserve it rather than overwrite')
    i.dump(path,dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),models=selected,
                     allowance=safe,original_accounted_usd=old))
    print(json.dumps(dict(allowance=safe,original_accounted_usd=old,
        models={m:dict(canonical_slug=v.get('canonical_slug'),pricing=v['pricing']) for m,v in selected.items()})),flush=True)


def make_body(condition, text, catalog, evidence):
    retrieved=condition.endswith('_retrieved')
    state={'user_utterance':text}
    if retrieved:
        state['retrieved_examples']=evidence
    extra=(' '+P['retrieval_instruction']) if retrieved else ''
    if condition.startswith('jev_'):
        return dict(model=i.P['jev_model'],state=state,questions={'intent':{
            'type':'choice','instructions':i.P['decision_instructions']+extra,
            'criteria':{k:dict(description=v['description'],example=v['example']) for k,v in catalog.items()}}})
    return dict(messages=[dict(role='system',content=i.P['direct_instructions']+extra+'\nCatalog: '+json.dumps(catalog,ensure_ascii=False)),
                          dict(role='user',content=json.dumps(state,ensure_ascii=False))])


class Collector(i.Collector):
    def __init__(self,key,workers):
        self.key=key
        self.protocol,self.save=i.P,i.dump
        frozen_parent=i.read(ROOT/'intent_frozen.json')
        if i.digest((ROOT/'intent_probe.py').read_bytes())!=frozen_parent['source_sha256'] or i.digest((ROOT/'intent_native.py').read_bytes())!=frozen_parent['native_sha256']:
            raise RuntimeError('Original frozen sources changed')
        for n,sha in i.DATA_SHA256.items():
            if i.digest((i.CACHE/n).read_bytes())!=sha:
                raise RuntimeError('Original raw data changed')
        self.catalog=i.read(i.CACHE/'catalog.json')
        if i.digest(self.catalog)!=i.read(i.CACHE/'data_receipt.json')['catalog_hash']:
            raise RuntimeError('Original catalog changed')
        self.retriever=i.Retriever(i.read(i.CACHE/'support.json'))
        self.snapshot=i.read(RUNS/'model_snapshot.json')
        self.signature=signature()
        self.base=RUNS/self.signature[:16]
        self.base.mkdir(parents=True,exist_ok=True)
        manifest=dict(signature=self.signature,protocol=P,source_sha256=source_hashes(),
                      data=i.read(i.CACHE/'data_receipt.json'),models=self.snapshot['models'])
        mp=self.base/'manifest.json'
        if mp.exists() and i.read(mp)!=manifest:
            raise RuntimeError('Manifest changed')
        i.dump(mp,manifest)
        self.ledger=i.Ledger(RUNS/'ledger.sqlite3',total=P['total_budget_usd'],phases=P['phase_budget_usd'])
        self.semaphore=threading.BoundedSemaphore(workers)
        self.jobs,self.sessions,self.lock={},{},threading.Lock()
        self.native_token=secrets.token_urlsafe(24)
        self.server=self.start_server()
        self.native_pool=NativePool(self,count=2)

    def run(self,row,split,condition):
        out=self.base/split/row['id']/condition
        if (out/'result.json').exists():
            result=i.read(out/'result.json')
            if result['signature']!=self.signature or result['input_hash']!=i.digest(row['text']):
                raise RuntimeError('Resume signature mismatch')
            return dict(result,resumed=True)
        if out.exists():
            raise RuntimeError('Partial paid job requires explicit audit: '+str(out))
        out.mkdir(parents=True)
        job=dict(id=self.signature[:16]+'/'+split+'/'+row['id']+'/'+condition,
                 route=secrets.token_hex(16),token=secrets.token_urlsafe(24),out=out,
                 phase=split,condition=condition,tools=[],errors=[],lock=threading.Lock())
        with self.lock:
            self.jobs[job['route']]=job
        started=time.monotonic()
        result=dict(signature=self.signature,id=row['id'],split=split,condition=condition,
                    input_hash=i.digest(row['text']),status='failed',prediction=None)
        i.dump(out/'input.json',dict(id=row['id'],utterance=row['text']))
        try:
            evidence=[]
            if condition.endswith('_retrieved'):
                retrieval_start=time.monotonic()
                evidence=self.retriever.search(row['text'],P['retrieval_k'])
                result['retrieval_s']=time.monotonic()-retrieval_start
                result['evidence_hash']=i.digest(evidence)
                i.dump(out/'fixed_evidence.json',evidence)
            if condition=='agent':
                result.update(self.agent(job,row['text']))
            else:
                body=make_body(condition,row['text'],self.catalog,evidence)
                if condition.startswith('jev_'):
                    result.update(i.parse_jev(self.call(job,i.P['jev_model'],body,'/alpha/decisions'),self.catalog))
                else:
                    response=self.strong(job,body)
                    result['prediction']=i.parse_prediction(response['choices'][0]['message']['content'],self.catalog)['intent']
            result['status']='complete'
        except Exception as error:
            result['error']=dict(type=type(error).__name__,message=str(error).replace(self.key,'[REDACTED]')[:500])
        records=self.ledger.records(job['id'])
        result.update(elapsed_s=time.monotonic()-started,cost_usd=sum(r['amount'] for r in records),
                      unresolved_calls=sum(r['state'] in ('reserved','unresolved') for r in records),
                      calls=len(records),retrieval_calls=len(job['tools'])+int(condition.endswith('_retrieved')),
                      adapter_errors=job['errors'])
        i.dump(out/'result.json',result)
        return result

    def collect(self,split,workers,limit=0):
        if split=='development':
            rows=balanced(split,P['development_count']//77)
        else:
            frozen=i.read(ROOT/'retrieval_frozen.json')
            if frozen['signature']!=self.signature or frozen['source_sha256']!=source_hashes():
                raise RuntimeError('Frozen implementation changed')
            ids=set(frozen['test_ids'] if split=='test' else frozen['live_ids'])
            rows=[r for r in i.read(i.CACHE/('test.json' if split=='test' else 'development.json')) if r['id'] in ids]
        if limit:
            rows=rows[:limit]
        rng=random.Random(P['seed']+{'development':0,'test':1,'live':2}[split])
        rng.shuffle(rows)
        plan=[]
        for row in rows:
            arms=list(CONDITIONS)
            rng.shuffle(arms)
            plan.extend((row,c) for c in arms)
        i.dump(self.base/('schedule-'+split+'.json'),[dict(id=r['id'],condition=c) for r,c in plan])
        if split=='live':
            self.native_pool.start()
        started=time.monotonic()
        done,failed=0,0
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(self.run,r,split,c) for r,c in plan]
            for f in concurrent.futures.as_completed(futures):
                result=f.result()
                done+=1
                failed+=result['status']!='complete'
                if done%100==0 or result['status']!='complete' or done==len(plan):
                    print(json.dumps(dict(done=done,total=len(plan),failures=failed,
                        last={k:result.get(k) for k in ('id','condition','status','error')},
                        wall_s=round(time.monotonic()-started,1),budget=self.ledger.status())),flush=True)
        report=dict(signature=self.signature,split=split,workers=workers,completed=done,
                    failures=failed,wall_s=time.monotonic()-started,budget=self.ledger.status())
        i.dump(self.base/f'collection-{split}-{time.time_ns()}.json',report)
        i.dump(RUNS/'ledger_export.json',self.ledger.records())


def results(split,condition):
    return {p.parent.parent.name:i.read(p) for p in (RUNS/signature()[:16]/split).glob('*/'+condition+'/result.json')}


def freeze():
    if (ROOT/'retrieval_frozen.json').exists():
        old=i.read(ROOT/'retrieval_frozen.json')
        if old['signature']!=signature():
            raise RuntimeError('Existing freeze does not match; retain it and audit')
        print('Existing freeze retained')
        return
    dev={c:results('development',c) for c in CONDITIONS}
    expected={r['id'] for r in balanced('development',P['development_count']//77)}
    if any(set(rs)!=expected for rs in dev.values()):
        raise RuntimeError('Complete paired development panel required')
    if any(sum(r['status']!='complete' for r in rs.values())/len(rs)>.05 for rs in dev.values()):
        raise RuntimeError('Development failure rate exceeds 5%; audit first')
    for rid in expected:
        if dev['jev_retrieved'][rid].get('evidence_hash')!=dev['sol_retrieved'][rid].get('evidence_hash'):
            raise RuntimeError('Fixed evidence differs between models')
    means={c:sum(r['cost_usd'] for r in rs.values())/len(rs) for c,rs in dev.items()}
    count=next((n for n in (P['test_count'],P['minimum_test_count']) if n*sum(means.values())*1.25<=P['phase_budget_usd']['test']),None)
    if count is None:
        raise RuntimeError('Neither planned sample fits budget')
    live_ids=[r['id'] for r in i.ordered(balanced('development',2),P['seed']+30)[:P['live_count']]]
    frozen=dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),signature=signature(),protocol=P,
                source_sha256=source_hashes(),models=i.read(RUNS/'model_snapshot.json')['models'],
                development_ids=sorted(expected),development_mean_costs=means,
                test_ids=sorted(r['id'] for r in balanced('test',count//77)),live_ids=live_ids,
                projected_final_usd=count*sum(means.values()),
                projected_with_25pct_margin=count*sum(means.values())*1.25,
                original_archive_sha256=i.digest((ROOT/'intent_runs.tar.xz').read_bytes()),
                original_evidence_sha256=i.digest((ROOT/'intent_evidence.json').read_bytes()))
    i.dump(ROOT/'retrieval_frozen.json',frozen)
    print(json.dumps({k:v for k,v in frozen.items() if k in ('signature','development_mean_costs','projected_final_usd','projected_with_25pct_margin')}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['snapshot','collect','freeze','status','balance'])
    parser.add_argument('--split',choices=['development','test','live'],default='development')
    parser.add_argument('--workers',type=int,default=24)
    parser.add_argument('--limit',type=int,default=0)
    args=parser.parse_args()
    RUNS.mkdir(parents=True,exist_ok=True)
    if args.action=='snapshot':
        snapshot(i.key_from_environment())
    elif args.action=='freeze':
        freeze()
    elif args.action=='balance':
        data=i.api(i.key_from_environment(),'/v1/key')['data']
        safe={k:data.get(k) for k in ('limit','limit_remaining','usage','usage_daily')}
        i.dump(RUNS/('allowance-'+str(time.time_ns())+'.json'),safe)
        print(json.dumps(safe))
    elif args.action=='status':
        print(json.dumps(i.Ledger(RUNS/'ledger.sqlite3',P['total_budget_usd'],P['phase_budget_usd']).status()))
        for split in ('development','test','live'):
            print(split,json.dumps({c:dict(n=len(rs:=results(split,c)),failures=sum(r['status']!='complete' for r in rs.values())) for c in CONDITIONS}))
    else:
        if not 1<=args.workers<=24 or args.split=='live' and args.workers!=1:
            raise ValueError('Use 1..24 workers; live timing must be serial')
        with (RUNS/'collector.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            collector=Collector(i.key_from_environment(),args.workers)
            try:
                collector.collect(args.split,args.workers,args.limit)
            finally:
                collector.close()


if __name__=='__main__':
    main()
