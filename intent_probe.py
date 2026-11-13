"""BANKING77: typed Jev decisions and native OpenCode retrieval escalation.

Python 3.11+, standard library. Gold labels stay in the evaluator process.
No model calls on import, prepare, select, freeze, status, or analyze.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import contextlib
import csv
import datetime as dt
import fcntl
import hashlib
import http.server
import json
import math
import os
from pathlib import Path
import random
import re
import secrets
import signal
import sqlite3
import subprocess
import tempfile
import threading
import time
import unicodedata
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / '.runtime/banking77'
RUNS = ROOT / 'runs/intent'
API = 'https://openrouter.ai/api'
P = json.loads((ROOT / 'intent_protocol.json').read_text())
DATA_SHA256 = {
    'train.csv':'b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b',
    'test.csv':'d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d',
    'categories.json':'53261da888122daf2d120d925458631d9619e15d82e56052e7a42e535ce32b63',
}


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else encoded(value)).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + secrets.token_hex(4) + '.tmp')
    tmp.write_bytes(encoded(value) + b'\n')
    os.replace(tmp, path)


def read(path):
    return json.loads(Path(path).read_text())


def normalize(text):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold()))


def ordered(rows, seed):
    return sorted(rows, key=lambda r: digest([seed, r['id']]))


def prepare():
    CACHE.mkdir(parents=True, exist_ok=True)
    receipts = {}
    for name in ('train.csv', 'test.csv', 'categories.json'):
        path = CACHE / name
        url = ('https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/'
               + P['dataset_revision'] + '/banking_data/' + name)
        if not path.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                path.write_bytes(response.read())
        receipts[name] = dict(url=url, bytes=path.stat().st_size, sha256=digest(path.read_bytes()))
        if receipts[name]['sha256'] != DATA_SHA256[name]:
            raise RuntimeError('Pinned dataset checksum mismatch: '+name)
    labels = read(CACHE / 'categories.json')
    data = {}
    for split, expected in [('train', 10003), ('test', 3080)]:
        with (CACHE / (split + '.csv')).open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == expected and len(labels) == 77
        assert all(set(r) == {'text', 'category'} and r['category'] in labels for r in rows)
        data[split] = [dict(id=f'{split}-{i:05d}', text=r['text'], label=r['category'])
                       for i, r in enumerate(rows)]
    # Whole normalized groups are assigned together, including cross-label duplicates.
    groups = collections.defaultdict(list)
    for r in data['train']:
        groups[normalize(r['text'])].append(r)
    bins = {'support': [], 'development': [], 'certification': []}
    grouped = collections.defaultdict(list)
    for key, rows in groups.items():
        grouped[min(r['label'] for r in rows)].append((key, rows))
    for label in sorted(grouped):
        gs = sorted(grouped[label], key=lambda g: digest([P['seed'], g[0]]))
        n = sum(len(g[1]) for g in gs)
        count = 0
        for _, rows in gs:
            name = 'support' if count < .70*n else 'development' if count < .85*n else 'certification'
            bins[name].extend(rows)
            count += len(rows)
    bins['test'] = data['test']
    norms = {s: {normalize(r['text']) for r in rs} for s, rs in bins.items()}
    assert not (norms['support'] & norms['development'] or norms['support'] & norms['certification']
                or norms['development'] & norms['certification'])
    catalog = {}
    for label in labels:
        exemplar = ordered([r for r in bins['support'] if r['label'] == label], P['seed'])[0]
        catalog[label] = dict(description=label.replace('_', ' '), example=exemplar['text'], support_id=exemplar['id'])
    report = dict(dataset_revision=P['dataset_revision'], receipts=receipts, seed=P['seed'],
                  counts={s: len(rs) for s, rs in bins.items()},
                  grouped_duplicates=sum(len(v)-1 for v in groups.values()),
                  cross_label_groups=sum(len({r['label'] for r in v}) > 1 for v in groups.values()),
                  train_test_overlap=len(norms['test'] & set(groups)),
                  support_test_overlap=len(norms['test'] & norms['support']),
                  overlap_policy='Keep all official test rows; flag normalized support overlap and report a secondary nonoverlap score. No overlap-based tuning.',
                  split_hash=digest({s: sorted(r['id'] for r in rs) for s, rs in bins.items()}),
                  catalog_hash=digest(catalog))
    for name, rows in bins.items():
        dump(CACHE / (name + '.json'), ordered(rows, P['seed']))
    dump(CACHE / 'catalog.json', catalog)
    dump(CACHE / 'data_receipt.json', report)
    print(json.dumps(report, indent=2))


class Retriever:
    """Deterministic BM25, with only official support rows in the index."""
    def __init__(self, rows):
        self.rows = rows
        self.tf = [collections.Counter(normalize(r['text']).split()) for r in rows]
        self.lengths = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.lengths) / len(rows)
        self.postings = collections.defaultdict(list)
        for i, c in enumerate(self.tf):
            for word in c:
                self.postings[word].append(i)

    def search(self, query, limit=8):
        scores = collections.defaultdict(float)
        for word in set(normalize(query).split()):
            ids = self.postings.get(word, [])
            idf = math.log(1 + (len(self.rows)-len(ids)+.5)/(len(ids)+.5))
            for i in ids:
                tf = self.tf[i][word]
                scores[i] += idf * tf * 2.5/(tf+1.5*(.25+.75*self.lengths[i]/self.avg))
        ranked = sorted(scores, key=lambda i: (-scores[i], self.rows[i]['id']))[:limit]
        return [dict(support_id=self.rows[i]['id'], text=self.rows[i]['text'],
                     intent=self.rows[i]['label'], score=round(scores[i], 6)) for i in ranked]


class Ledger:
    """Atomic reservations shared by all parallel workers; unresolved calls stay charged."""
    def __init__(self, path, total=None, phases=None):
        self.path, self.total = str(path), P['total_budget_usd'] if total is None else total
        self.phases = P['phase_budget_usd'] if phases is None else phases
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as con:
            con.execute('PRAGMA journal_mode=WAL')
            con.execute('CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, job TEXT, phase TEXT, model TEXT, '
                        'reserved REAL, amount REAL, state TEXT, receipt TEXT)')
            con.execute('CREATE INDEX IF NOT EXISTS calls_job ON calls(job)')

    def connection(self):
        return sqlite3.connect(self.path, timeout=60)

    def reserve(self, job, phase, model, amount, max_calls):
        with self.connection() as con:
            con.execute('BEGIN IMMEDIATE')
            total, = con.execute('SELECT COALESCE(SUM(amount),0) FROM calls').fetchone()
            local, count = con.execute('SELECT COALESCE(SUM(amount),0),COUNT(*) FROM calls WHERE job=? AND state!=?', (job, 'rate_limited')).fetchone()
            phased, = con.execute('SELECT COALESCE(SUM(amount),0) FROM calls WHERE phase=?', (phase,)).fetchone()
            if total + amount > self.total or phased + amount > self.phases[phase]:
                raise RuntimeError('Global or phase budget exhausted')
            if local + amount > P['task_budget_usd'] or count >= max_calls:
                raise RuntimeError('Job budget or call limit exhausted')
            rid = secrets.token_hex(12)
            con.execute('INSERT INTO calls VALUES (?,?,?,?,?,?,?,?)',
                        (rid, job, phase, model, amount, amount, 'reserved', '{}'))
            return rid

    def settle(self, rid, receipt, state='complete'):
        cost = receipt.get('cost_usd')
        if cost is not None and (not math.isfinite(float(cost)) or float(cost) < 0):
            raise ValueError('Invalid cost')
        with self.connection() as con:
            if cost is None:
                con.execute('UPDATE calls SET state=?,receipt=? WHERE id=?', ('unresolved', json.dumps(receipt), rid))
            else:
                con.execute('UPDATE calls SET amount=?,state=?,receipt=? WHERE id=?',
                            (float(cost), state, json.dumps(receipt), rid))

    def records(self, job=None):
        with self.connection() as con:
            con.row_factory = sqlite3.Row
            rows = con.execute('SELECT * FROM calls' + (' WHERE job=?' if job else ''), (job,) if job else ()).fetchall()
        return [dict(r, receipt=json.loads(r['receipt'])) for r in rows]

    def status(self):
        with self.connection() as con:
            states=list(con.execute('SELECT state,COUNT(*),SUM(amount) FROM calls GROUP BY state'))
            phases=dict(con.execute('SELECT phase,SUM(amount) FROM calls GROUP BY phase'))
        return dict(accounted_usd=sum(r[2] for r in states),
                    billed_usd=sum(r[2] for r in states if r[0]=='complete'),
                    reserved_usd=sum(r[2] for r in states if r[0] in ('reserved','unresolved')),
                    calls=sum(r[1] for r in states),states={r[0]:r[1] for r in states},
                    phases={p:phases.get(p,0) for p in self.phases})


def api(key, path, body=None):
    req = urllib.request.Request(API + path, data=None if body is None else encoded(body),
                                 headers={'Authorization': 'Bearer '+key, 'Content-Type': 'application/json',
                                          'X-Title': 'CS329Z BANKING77 controlled experiment'})
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.load(response)


def snapshot(key):
    models = api(key, '/v1/models?output_modalities=all')['data']
    selected = {m['id']: m for m in models if m['id'] in (P['jev_model'], P['strong_model'])}
    assert set(selected) == {P['jev_model'], P['strong_model']}
    allowance = api(key, '/v1/key')['data']
    safe = {k: allowance.get(k) for k in ('limit', 'limit_remaining', 'usage', 'usage_daily', 'is_free_tier')}
    dump(RUNS / 'model_snapshot.json', dict(at=dt.datetime.now(dt.timezone.utc).isoformat(), models=selected, allowance=safe))
    print(json.dumps(dict(allowance=safe, models={k: dict(pricing=v['pricing'], canonical_slug=v.get('canonical_slug')) for k,v in selected.items()}), indent=2))


def parse_jev(response, labels):
    answer = response['answers']['intent']
    probabilities = answer['probabilities']
    if set(probabilities) != set(labels) or answer['choice'] not in labels:
        raise ValueError('Jev label set differs from the 77-way catalog')
    values = list(probabilities.values())
    if any(isinstance(x, bool) or not isinstance(x, (int,float)) or not math.isfinite(x) or not 0 <= x <= 1 for x in values):
        raise ValueError('Invalid Jev probabilities')
    if abs(sum(values)-1) > .005 or probabilities[answer['choice']] < max(values)-1e-8:
        raise ValueError('Invalid probability normalization or argmax')
    return dict(prediction=answer['choice'], score=max(values), probabilities=probabilities,
                vendor_confidence=answer.get('confidence'))


def parse_prediction(text, labels):
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
    value = json.loads(text)
    if not isinstance(value, dict) or value.get('intent') not in labels:
        raise ValueError('Invalid canonical intent')
    return value


def validate_agent(text, catalog, tools):
    result = parse_prediction(text,catalog)
    searches = [t for t in tools if t['tool']=='search_examples']
    ids = {r['support_id'] for t in searches for r in t['result']}
    ids.update(t['result']['support_id'] for t in tools if t['tool']=='lookup_intent')
    cited = result.get('support_ids')
    if not searches or not isinstance(cited,list) or not cited or not set(cited) <= ids:
        raise ValueError('Missing real retrieval or invalid support citations')
    return dict(prediction=result['intent'],support_ids=cited)


def accepted(result, threshold):
    return result.get('status') == 'complete' and result.get('prediction') is not None and result.get('score', -1) >= threshold


def binomial_upper(errors, n, alpha=.05):
    """One-sided Clopper-Pearson upper bound, log-sum-exp binomial CDF."""
    if n == 0 or errors == n:
        return 1.0
    def cdf(p):
        terms = [math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)+k*math.log(p)+(n-k)*math.log1p(-p) for k in range(errors+1)]
        m = max(terms)
        return math.exp(m) * sum(math.exp(t-m) for t in terms)
    lo, hi = errors/n, 1-1e-15
    for _ in range(65):
        mid = (lo+hi)/2
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2


class Collector:
    def __init__(self, key, workers):
        self.key = key
        self.protocol, self.save = P, dump
        self.catalog = read(CACHE / 'catalog.json')
        if digest(self.catalog) != read(CACHE/'data_receipt.json')['catalog_hash']:
            raise RuntimeError('Frozen catalog checksum mismatch')
        for name,sha in DATA_SHA256.items():
            if digest((CACHE/name).read_bytes()) != sha:
                raise RuntimeError('Pinned data changed')
        self.retriever = Retriever(read(CACHE / 'support.json'))
        self.snapshot = read(RUNS / 'model_snapshot.json')
        self.signature = protocol_signature()
        self.base = RUNS / self.signature[:16]
        self.base.mkdir(parents=True, exist_ok=True)
        dump(self.base / 'manifest.json', dict(signature=self.signature, protocol=P,
            data=read(CACHE / 'data_receipt.json'), models=self.snapshot['models'],
            source_sha256=digest(Path(__file__).read_bytes())))
        self.ledger = Ledger(RUNS / 'ledger.sqlite3')
        self.semaphore = threading.BoundedSemaphore(workers)
        self.jobs, self.sessions, self.lock = {}, {}, threading.Lock()
        self.native_token = secrets.token_urlsafe(24)
        self.server = self.start_server()
        from intent_native import NativePool
        self.native_pool = NativePool(self,count=2)

    def call(self, job, model, body, path):
        pricing = self.snapshot['models'][model]['pricing']
        raw = encoded(body)
        if len(raw) > P['max_input_bytes']:
            raise ValueError('Input limit exceeded')
        # UTF-8 bytes + chat/tool envelope allowance conservatively bound tokens.
        reserve = max(.001, (len(raw)+512*(1+len(body.get('messages', []))+len(body.get('tools', [])))) * float(pricing['prompt'])
                      + P['max_output_tokens']*float(pricing['completion']))
        max_calls = P['max_model_requests_per_agent'] if job['condition']=='agent' else 1
        for attempt in range(3):
            with self.semaphore:
                rid = self.ledger.reserve(job['id'], job['phase'], model, reserve, max_calls)
                dump(job['out'] / ('request-'+rid+'.json'), body)
                start = time.monotonic()
                try:
                    response = api(self.key, path, body)
                    dump(job['out'] / ('response-'+rid+'.json'), response)
                    usage = response.get('usage', {})
                    cost, provider = usage.get('cost'), response.get('provider')
                    if cost is None and response.get('id'):
                        with contextlib.suppress(Exception):
                            info = api(self.key, '/v1/generation?id='+response['id'])['data']
                            cost, provider = info.get('total_cost'), info.get('provider_name')
                    receipt = dict(cost_usd=cost, elapsed_s=time.monotonic()-start, usage=usage,
                                   generation_id=response.get('id'), provider=provider,
                                   served_model=response.get('model'), input_bytes=len(raw))
                    self.ledger.settle(rid, receipt)
                    dump(job['out'] / ('receipt-'+rid+'.json'), receipt)
                    if 'error' in response:
                        raise RuntimeError('Upstream error in response')
                    return response
                except urllib.error.HTTPError as error:
                    # Error payloads may be useful but must never include the upstream key.
                    detail = error.read().decode(errors='replace')[:3000].replace(self.key, '[REDACTED]')
                    receipt = dict(error_type='HTTPError', status=error.code, detail=detail,
                                   elapsed_s=time.monotonic()-start,
                                   cost_usd=0 if error.code==429 else None)
                    self.ledger.settle(rid, receipt, 'rate_limited' if error.code==429 else 'unresolved')
                    dump(job['out'] / ('receipt-'+rid+'.json'), receipt)
                    if error.code != 429 or attempt==2:
                        raise
                except Exception as error:
                    self.ledger.settle(rid, dict(error_type=type(error).__name__, cost_usd=None,
                                                elapsed_s=time.monotonic()-start))
                    raise
            time.sleep(2**attempt + random.Random(rid).random())

    def strong(self, job, body):
        body = dict(body, model=P['strong_model'], stream=False,
                    max_tokens=P['max_output_tokens'], usage={'include':True},
                    provider={'allow_fallbacks':False,'require_parameters':True})
        body.pop('stream_options', None)
        body.pop('max_completion_tokens', None)
        return self.call(job, P['strong_model'], body, '/v1/chat/completions')

    def start_server(self):
        collector = self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                parts = self.path.strip('/').split('/')
                size = int(self.headers.get('Content-Length',0))
                if not 0 < size <= P['max_input_bytes']:
                    self.send_error(413)
                    return
                try:
                    body = json.loads(self.rfile.read(size))
                    if parts[0]=='native':
                        job = collector.sessions.get(self.headers.get('x-intent-session') or body.get('session_id'))
                        token = collector.native_token
                    else:
                        job = collector.jobs.get(parts[0])
                        token = job['token'] if job else None
                    if job is None or self.headers.get('Authorization') != 'Bearer '+str(token):
                        self.send_error(403)
                        return
                    route = '/'.join(parts[1:])
                    if route.startswith('tools/'):
                        with job['lock']:
                            if len(job['tools']) >= P['max_retrieval_calls']:
                                raise RuntimeError('Retrieval call cap exceeded')
                            started = time.monotonic()
                            if route == 'tools/search':
                                query = str(body['query'])[:2000]
                                output = collector.retriever.search(query, P['retrieval_limit'])
                                record = dict(tool='search_examples', query=query, result=output)
                            elif route == 'tools/lookup' and body['intent'] in collector.catalog:
                                label = body['intent']
                                output = dict(intent=label, **collector.catalog[label])
                                record = dict(tool='lookup_intent', intent=label, result=output)
                            else:
                                raise ValueError('Unknown tool or intent')
                            record['elapsed_s'] = time.monotonic()-started
                            job['tools'].append(record)
                            dump(job['out']/'tools.json', job['tools'])
                        raw, content_type = encoded(output), 'application/json'
                    elif route == 'v1/chat/completions':
                        streaming = body.get('stream', False)
                        response = collector.strong(job, body)
                        if streaming:
                            choice = response['choices'][0]
                            msg = choice['message']
                            delta = dict(role='assistant', content=msg.get('content') or '')
                            if msg.get('reasoning'):
                                delta['reasoning'] = msg['reasoning']
                            if msg.get('tool_calls'):
                                delta['tool_calls'] = [dict(call,index=i) for i,call in enumerate(msg['tool_calls'])]
                            chunk = dict(id=response['id'], object='chat.completion.chunk',
                                         created=response.get('created',int(time.time())),model=response['model'],
                                         choices=[dict(index=0,delta=delta,finish_reason=None)])
                            final = dict(chunk,choices=[dict(index=0,delta={},finish_reason=choice['finish_reason'])],usage=response.get('usage',{}))
                            raw = ('data: '+json.dumps(chunk)+'\n\ndata: '+json.dumps(final)+'\n\ndata: [DONE]\n\n').encode()
                            content_type = 'text/event-stream'
                        else:
                            raw, content_type = encoded(response), 'application/json'
                    else:
                        self.send_error(404)
                        return
                    self.send_response(200)
                    self.send_header('Content-Type',content_type)
                    self.send_header('Content-Length',str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                except Exception as error:
                    with job['lock']:
                        job['errors'].append(dict(type=type(error).__name__, message=str(error).replace(collector.key,'[REDACTED]')[:300]))
                    self.send_error(400, 'Bounded request failed')
        server = http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        return server

    def agent(self, job, utterance):
        text = self.native_pool.run(job,utterance)
        return validate_agent(text,self.catalog,job['tools'])

    def run(self, row, split, condition):
        out = self.base/split/row['id']/condition
        if (out/'result.json').exists():
            result = read(out/'result.json')
            if result['signature'] != self.signature or result['input_hash'] != digest(row['text']):
                raise RuntimeError('Resume signature mismatch')
            return dict(result,resumed=True)
        # Never silently replay partially paid attempts.
        if out.exists():
            raise RuntimeError('Incomplete job requires explicit audit: '+str(out))
        out.mkdir(parents=True)
        job = dict(id=self.signature[:16]+'/'+split+'/'+row['id']+'/'+condition,
                   route=secrets.token_hex(16),token=secrets.token_urlsafe(24),out=out,
                   phase=split,condition=condition,tools=[],errors=[],lock=threading.Lock())
        with self.lock:
            self.jobs[job['route']] = job
        started = time.monotonic()
        result = dict(signature=self.signature,id=row['id'],split=split,condition=condition,
                      input_hash=digest(row['text']),source_sha256=digest(Path(__file__).read_bytes()),status='failed',prediction=None)
        dump(out/'input.json',dict(id=row['id'],utterance=row['text']))
        try:
            if condition=='jev':
                body = dict(model=P['jev_model'],state={'user_utterance':row['text']},
                    questions={'intent':{'type':'choice','instructions':P['decision_instructions'],
                      'criteria':{k:dict(description=v['description'],example=v['example']) for k,v in self.catalog.items()}}})
                result.update(parse_jev(self.call(job,P['jev_model'],body,'/alpha/decisions'),self.catalog))
            elif condition=='direct':
                body = dict(messages=[dict(role='system',content=P['direct_instructions']+'\nCatalog: '+json.dumps(self.catalog,ensure_ascii=False)),
                                      dict(role='user',content=json.dumps({'user_utterance':row['text']},ensure_ascii=False))])
                response = self.strong(job,body)
                result['prediction'] = parse_prediction(response['choices'][0]['message']['content'],self.catalog)['intent']
            else:
                result.update(self.agent(job,row['text']))
            result['status'] = 'complete'
        except Exception as error:
            result['error'] = dict(type=type(error).__name__,message=str(error).replace(self.key,'[REDACTED]')[:500])
        records = self.ledger.records(job['id'])
        result.update(elapsed_s=time.monotonic()-started,cost_usd=sum(r['amount'] for r in records),
            unresolved_calls=sum(r['state'] in ('reserved','unresolved') for r in records),
            calls=len(records),retrieval_calls=len(job['tools']),adapter_errors=job['errors'])
        dump(out/'result.json',result)
        return result

    def collect(self, split, conditions, limit, workers, offset=0):
        rows = read(CACHE/(split+'.json'))
        if split=='test':
            frozen = read(RUNS/'frozen_protocol.json')
            if frozen['signature'] != self.signature or frozen['source_sha256'] != digest(Path(__file__).read_bytes()) or frozen['native_sha256'] != digest((ROOT/'intent_native.py').read_bytes()):
                raise RuntimeError('Frozen implementation changed')
            ids = set(frozen['test_ids'])
            rows = [r for r in rows if r['id'] in ids]
        if split=='certification':
            selection = read(RUNS/'threshold_selection.json')
            if selection['signature'] != self.signature:
                raise RuntimeError('Threshold selection is from another implementation')
        rows = rows[offset:None if limit==0 else offset+limit]
        plan = [(row,cond) for row in rows for cond in conditions]
        started, completed, failures = time.monotonic(), [], 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self.run,row,split,cond):(row['id'],cond) for row,cond in plan}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                completed.append(result)
                failures += result['status']!='complete'
                if len(completed)%100==0 or result['status']!='complete' or len(completed)==len(plan):
                    print(json.dumps(dict(done=len(completed),total=len(plan),failures=failures,
                        last={k:result.get(k) for k in ('id','condition','status','elapsed_s','cost_usd','error')},
                        wall_s=round(time.monotonic()-started,1),budget=self.ledger.status())),flush=True)
        report = dict(split=split,conditions=conditions,offset=offset,limit=limit,workers=workers,
                      wall_s=time.monotonic()-started,completed=len(completed),failures=failures,
                      signature=self.signature,budget=self.ledger.status())
        dump(self.base/f'collection-{split}-{time.time_ns()}.json',report)
        return report

    def close(self):
        self.native_pool.close()
        self.server.shutdown()
        self.server.server_close()

    def live(self):
        frozen=read(RUNS/'frozen_protocol.json')
        assert frozen['signature']==self.signature
        rows={r['id']:r for r in read(CACHE/'development.json')}
        # Warm only the native runtime, without a model call; no queue in this check.
        self.native_pool.start()
        outputs=[]
        for rid in frozen['analysis']['live_ids']:
            out=self.base/'live'/rid/'routed.json'
            if out.exists():
                outputs.append(read(out))
                continue
            started=time.monotonic()
            jev=self.run(rows[rid],'live','jev')
            use_jev=accepted(jev,frozen['effective_threshold'])
            agent=None if use_jev else self.run(rows[rid],'live','agent')
            prediction=jev['prediction'] if use_jev else agent['prediction']
            result=dict(id=rid,route='jev' if use_jev else 'agent',prediction=prediction,
                        elapsed_s=time.monotonic()-started,cost_usd=jev['cost_usd']+(0 if use_jev else agent['cost_usd']),
                        correct=prediction==rows[rid]['label'],signature=self.signature)
            dump(out,result)
            outputs.append(result)
            print(json.dumps(result),flush=True)
        dump(RUNS/'live_evidence.json',dict(note='12 predeclared development examples, serial live cascade; runtime warmed without model calls. Separate from paired test replay latency.',rows=outputs))


def protocol_signature():
    return digest(dict(protocol=P,data=read(CACHE/'data_receipt.json'),
                       tools=digest((ROOT/'intent_tools.js').read_bytes())))


def results(split, condition):
    base = RUNS/protocol_signature()[:16]/split
    return {p.parent.parent.name: read(p) for p in base.glob('*/'+condition+'/result.json')}


def select_threshold():
    rows = read(CACHE/'development.json')
    predictions = results('development','jev')
    if set(predictions) != {r['id'] for r in rows}:
        raise RuntimeError('Complete development Jev collection is required')
    grid = []
    for threshold in P['threshold_grid']:
        chosen = [r for r in rows if accepted(predictions[r['id']],threshold)]
        errors = sum(predictions[r['id']]['prediction']!=r['label'] for r in chosen)
        grid.append(dict(threshold=threshold,accepted=len(chosen),errors=errors,risk=errors/len(chosen) if chosen else None))
    feasible = [g for g in grid if g['accepted'] >= P['min_dev_accepted'] and g['risk'] <= P['threshold_dev_risk']]
    chosen = max(feasible,key=lambda g:(g['accepted'],-g['threshold'])) if feasible else dict(threshold=1.01,accepted=0,errors=0,risk=None)
    report = dict(signature=protocol_signature(),chosen=chosen,grid=grid,
                  rule='Maximize development coverage with empirical risk <= 3%, minimum 100 accepted; one independent certification follows.',
                  selected_at=dt.datetime.now(dt.timezone.utc).isoformat())
    path = RUNS/'threshold_selection.json'
    if path.exists() and read(path)['chosen'] != chosen:
        raise RuntimeError('Threshold already selected; do not overwrite')
    dump(path,report)
    print(json.dumps({k:v for k,v in report.items() if k!='grid'},indent=2))


def freeze():
    signature = protocol_signature()
    selected = read(RUNS/'threshold_selection.json')
    assert selected['signature']==signature
    rows = read(CACHE/'certification.json')
    predictions = results('certification','jev')
    if set(predictions) != {r['id'] for r in rows}:
        raise RuntimeError('Complete independent certification is required')
    threshold = selected['chosen']['threshold']
    chosen = [r for r in rows if accepted(predictions[r['id']],threshold)]
    errors = sum(predictions[r['id']]['prediction']!=r['label'] for r in chosen)
    upper = binomial_upper(errors,len(chosen))
    passed = upper <= P['accepted_risk_target']
    effective = threshold if passed else 1.01
    costs = {c:list(results('development',c).values()) for c in ('jev','direct','agent')}
    means = {c:sum(r['cost_usd'] for r in rs)/len(rs) for c,rs in costs.items()}
    if any(len(rs)<30 for rs in costs.values()):
        raise RuntimeError('At least 30 paired development baseline runs required')
    if any(sum(r['status']!='complete' for r in rs)/len(rs)>.05 for rs in costs.values()):
        raise RuntimeError('Development integration failures require audit before freezing')
    # Conservative 25% projection margin; freeze a balanced sample before any test calls.
    count = next((n for n in [P['preferred_test_count']]+P['alternate_test_counts']
                  if n*sum(means.values())*1.25 <= P['final_budget_projection_usd']),None)
    if count is None:
        raise RuntimeError('No planned sample fits the final budget')
    test = read(CACHE/'test.json')
    ids = []
    for label in sorted({r['label'] for r in test}):
        ids += [r['id'] for r in ordered([r for r in test if r['label']==label],P['seed'])[:count//77]]
    observed = collections.defaultdict(set)
    for call in Ledger(RUNS/'ledger.sqlite3').records():
        if call['job'].startswith(signature[:16]+'/') and call['state']=='complete':
            observed[call['model']].add(call['receipt'].get('provider'))
    frozen = dict(signature=signature,source_sha256=digest(Path(__file__).read_bytes()),native_sha256=digest((ROOT/'intent_native.py').read_bytes()),
        harness_binary_sha256=digest((ROOT/'.runtime/opencode').read_bytes()),
        observed_providers={m:sorted(str(p) for p in ps) for m,ps in observed.items()},
        execution='OpenCode 1.19.5 native server, two isolated worker databases, up to six independent sessions per worker, explicit session titles, sessions deleted only after raw messages/receipts are saved; host model-request concurrency at most 24.',
        at=dt.datetime.now(dt.timezone.utc).isoformat(),protocol=P,
        data=read(CACHE/'data_receipt.json'),models=read(RUNS/'model_snapshot.json')['models'],
        selected_threshold=threshold,effective_threshold=effective,
        certification=dict(n=len(rows),accepted=len(chosen),errors=errors,one_sided_95_upper=upper,passed=passed),
        sample_count=count,test_ids=sorted(ids),development_mean_costs=means,
        projected_final_usd=count*sum(means.values()),projection_with_25pct_margin=count*sum(means.values())*1.25,
        analysis=dict(conditions=['jev','direct','agent','hybrid','random_matched'],
                      random_seeds=list(range(32977,32997)),bootstrap_seed=32977,bootstrap_replicates=2000,
                      accuracy_margin=.02,risk_target=.05,cost_reduction_target=.30,
                      failures='Count all frozen examples, including invalid output, timeout, provider errors, and missing predictions, as incorrect. Costs include all attempts and conservative unresolved reservations.',
                      paired_bootstrap='Stratified by intent, same resampled IDs for all policies; one-sided 95% lower accuracy-difference bound for the 2-point target.',
                      live_ids=[r['id'] for r in read(CACHE/'development.json')[:12]]))
    path=RUNS/'frozen_protocol.json'
    if path.exists():
        old=read(path)
        assert old['signature']==signature and old['test_ids']==sorted(ids) and old['effective_threshold']==effective
        print('Existing frozen protocol retained')
        return
    dump(path,frozen)
    dump(ROOT/'intent_frozen.json',frozen)
    print(json.dumps({k:v for k,v in frozen.items() if k in ('signature','sample_count','certification','selected_threshold','effective_threshold','development_mean_costs','projected_final_usd','projection_with_25pct_margin')},indent=2))


def key_from_environment():
    key = os.environ.get('OPENROUTER_API_KEY')
    if key:
        return key
    path = ROOT/'.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith('OPENROUTER_API_KEY='):
                return line.split('=',1)[1].strip().strip('\"\'')
    raise RuntimeError('Set OPENROUTER_API_KEY or project .env; never commit the key')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','snapshot','collect','select','freeze','status','pack','live'])
    parser.add_argument('--split',choices=['development','certification','test'],default='development')
    parser.add_argument('--conditions',nargs='+',choices=['jev','direct','agent'],default=['jev','direct','agent'])
    parser.add_argument('--limit',type=int,default=30,help='0 means the complete partition/frozen sample')
    parser.add_argument('--offset',type=int,default=0)
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if args.action=='prepare':
        prepare()
    elif args.action=='snapshot':
        snapshot(key_from_environment())
    elif args.action=='select':
        select_threshold()
    elif args.action=='freeze':
        freeze()
    elif args.action=='status':
        print(json.dumps(Ledger(RUNS/'ledger.sqlite3').status(),indent=2))
        for split in ('development','certification','test'):
            print(split,json.dumps({c:dict(n=len(rs:=results(split,c)),failures=sum(r['status']!='complete' for r in rs.values())) for c in ('jev','direct','agent')}))
    elif args.action=='pack':
        archive=ROOT/'intent_runs.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for path in sorted(RUNS.rglob('*')):
                if path.is_file() and path.suffix not in ('.sqlite3','-wal','-shm') and not path.name.endswith(('-wal','-shm','.lock')):
                    z.write(path,path.relative_to(ROOT))
            for name in ('data_receipt.json','catalog.json'):
                z.write(CACHE/name,'intent_data/'+name)
        dump(ROOT/'intent_archive.json',dict(file=archive.name,sha256=digest(archive.read_bytes()),bytes=archive.stat().st_size))
        print(archive)
    else:
        if not 1 <= args.workers <= 24:
            raise ValueError('workers must be 1..24')
        RUNS.mkdir(parents=True,exist_ok=True)
        with (RUNS/'collector.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            collector=Collector(key_from_environment(),args.workers)
            try:
                if args.action=='live':
                    collector.live()
                else:
                    collector.collect(args.split,args.conditions,args.limit,args.workers,args.offset)
            finally:
                collector.close()


if __name__=='__main__':
    main()
