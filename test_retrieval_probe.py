import json, tempfile, unittest
from pathlib import Path
import intent_probe as i
import retrieval_probe as r


class RetrievalChecks(unittest.TestCase):
    def test_matched_evidence_and_gold_exclusion(self):
        catalog={'a':dict(description='a',example='support exemplar',support_id='train-1')}
        evidence=[dict(support_id='train-2',text='real support',intent='a',score=1)]
        jb=r.make_body('jev_retrieved','held out text',catalog,evidence)
        sb=r.make_body('sol_retrieved','held out text',catalog,evidence)
        self.assertEqual(jb['state'],json.loads(sb['messages'][1]['content']))
        self.assertEqual(set(jb['state']),{'user_utterance','retrieved_examples'})
        self.assertEqual(set(jb['questions']['intent']['criteria']),set(catalog))
        self.assertNotIn('retrieved_examples',r.make_body('jev_static','x',catalog,evidence)['state'])

    def test_balanced_panels_and_support_only(self):
        rows=r.balanced('development',2)
        from collections import Counter
        self.assertEqual(set(Counter(x['label'] for x in rows).values()),{2})
        support=i.read(i.CACHE/'support.json')
        allowed={x['id'] for x in support}
        self.assertFalse(allowed & {x['id'] for x in rows})
        search=i.Retriever(support)
        for x in rows[:10]:
            self.assertTrue({v['support_id'] for v in search.search(x['text'],8)}<=allowed)

    def test_resume_and_partial_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            c=object.__new__(r.Collector)
            c.base=Path(temp); c.signature='abc'
            row=dict(id='test-1',text='input')
            out=c.base/'test'/'test-1'/'jev_retrieved'
            out.mkdir(parents=True)
            with self.assertRaises(RuntimeError):
                c.run(row,'test','jev_retrieved')
            i.dump(out/'result.json',dict(signature='abc',input_hash=i.digest('input'),status='complete'))
            self.assertTrue(c.run(row,'test','jev_retrieved')['resumed'])
            with self.assertRaises(RuntimeError):
                c.run(dict(row,text='changed'),'test','jev_retrieved')

    def test_original_evidence_intact(self):
        self.assertEqual(i.digest((i.ROOT/'intent_evidence.json').read_bytes()),'d4494ff3f7207512e23a7abc8cd0b8299048c3272c80dc9b3c6e9fb9ad329390')
        self.assertEqual(i.digest((i.ROOT/'intent_runs.tar.xz').read_bytes()),'aa01262f6810b77e5f9d58c1c49c9924fc3ace74f3d389750e58a774822e857f')


if __name__=='__main__':
    unittest.main()
