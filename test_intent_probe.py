"""Offline checks for the experiment's important inference/accounting boundaries."""
import concurrent.futures
import math
from pathlib import Path
import tempfile
import unittest

import intent_probe as i


class IntentChecks(unittest.TestCase):
    def test_atomic_budget_under_parallel_reservations(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger=i.Ledger(Path(temp)/'ledger.db',total=.1,phases={'development':.1})
            def reserve(k):
                try:
                    return ledger.reserve(str(k),'development','test',.03,1)
                except RuntimeError:
                    return None
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
                receipts=list(pool.map(reserve,range(30)))
            self.assertEqual(sum(r is not None for r in receipts),3)
            self.assertAlmostEqual(ledger.status()['accounted_usd'],.09)
            rid=next(r for r in receipts if r)
            ledger.settle(rid,{'cost_usd':None})
            self.assertAlmostEqual(ledger.status()['accounted_usd'],.09)
            ledger.settle(rid,{'cost_usd':.005})
            self.assertAlmostEqual(ledger.status()['accounted_usd'],.065)

    def test_invalid_decisions_escalate(self):
        good={'answers':{'intent':{'choice':'a','probabilities':{'a':.8,'b':.2},'confidence':.4}}}
        result=i.parse_jev(good,['a','b'])
        self.assertEqual(result['score'],.8)
        self.assertFalse(i.accepted(dict(result,status='failed'),.5))
        self.assertFalse(i.accepted(dict(status='complete',prediction=None,score=1),.5))
        for bad in ({'a':1}, {'a':float('nan'),'b':0}, {'a':.4,'b':.6}, {'a':True,'b':0}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                i.parse_jev({'answers':{'intent':{'choice':'a','probabilities':bad}}},['a','b'])

    def test_exact_label_scoring(self):
        self.assertEqual(i.parse_prediction('{"intent":"a"}',['a'])['intent'],'a')
        with self.assertRaises(ValueError):
            i.parse_prediction('{"intent":"A"}',['a'])

    def test_agent_requires_actual_retrieval_and_valid_citations(self):
        tools=[{'tool':'search_examples','result':[{'support_id':'s1'}]},
               {'tool':'lookup_intent','result':{'support_id':'s2'}}]
        self.assertEqual(i.validate_agent('{"intent":"a","support_ids":["s2"]}',['a'],tools)['prediction'],'a')
        with self.assertRaises(ValueError):
            i.validate_agent('{"intent":"a","support_ids":["invented"]}',['a'],tools)
        with self.assertRaises(ValueError):
            i.validate_agent('{"intent":"a","support_ids":["s2"]}',['a'],tools[1:])

    def test_resume_returns_saved_result_without_model_call(self):
        with tempfile.TemporaryDirectory() as temp:
            collector=object.__new__(i.Collector)
            collector.base=Path(temp)
            collector.signature='frozen'
            out=collector.base/'development'/'train-1'/'jev'/'result.json'
            saved=dict(signature='frozen',input_hash=i.digest('example'),status='complete',prediction='a',cost_usd=.001)
            i.dump(out,saved)
            result=collector.run({'id':'train-1','text':'example'},'development','jev')
            self.assertTrue(result['resumed'])
            self.assertEqual(result['cost_usd'],.001)
            with self.assertRaises(RuntimeError):
                collector.run({'id':'train-1','text':'changed'},'development','jev')

    def test_binomial_bound(self):
        self.assertAlmostEqual(i.binomial_upper(0,59),1-.05**(1/59),places=10)
        self.assertLess(i.binomial_upper(0,59),.05)
        self.assertGreater(i.binomial_upper(0,58),.05)
        self.assertEqual(i.binomial_upper(0,0),1)

    def test_support_only_index_and_disjoint_splits(self):
        support=i.read(i.CACHE/'support.json')
        dev=i.read(i.CACHE/'development.json')
        cert=i.read(i.CACHE/'certification.json')
        sets=[{i.normalize(r['text']) for r in rows} for rows in (support,dev,cert)]
        self.assertFalse(sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2])
        retriever=i.Retriever(support)
        ids={r['id'] for r in support}
        for r in dev[:10]:
            self.assertTrue({x['support_id'] for x in retriever.search(r['text'])} <= ids)
        catalog=i.read(i.CACHE/'catalog.json')
        self.assertEqual(len(catalog),77)
        self.assertTrue({v['support_id'] for v in catalog.values()} <= ids)


if __name__=='__main__':
    unittest.main()
