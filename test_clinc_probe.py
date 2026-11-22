"""Offline checks for the CLINC150 Jev-in-the-loop study; no network or model calls."""
import math
import unittest

import clinc_probe as cp

LABELS = [f'intent_{i}' for i in range(150)] + ['oos']


def jev_response(choice, top=0.97):
    rest = (1 - top) / (len(LABELS) - 1)
    probs = {l: (top if l == choice else rest) for l in LABELS}
    return {'answers': {'intent': {'choice': choice, 'probabilities': probs}}}


class ClincChecks(unittest.TestCase):
    def test_protocol_fixes_threshold_and_two_conditions(self):
        self.assertEqual(cp.P['threshold'], 0.96)
        self.assertEqual(set(cp.P['conditions']), {'agent', 'jev', 'with_jev'})
        self.assertEqual(set(cp.P['phase_budget_usd']), {'smoke', 'test'})

    def test_jev_parsing_accepts_151_labels_and_rejects_bad_ones(self):
        parsed = cp.parse_jev(jev_response('oos'), LABELS)
        self.assertEqual(parsed['prediction'], 'oos')
        self.assertAlmostEqual(parsed['score'], 0.97)
        bad = jev_response('intent_3')
        bad['answers']['intent']['probabilities'].pop('oos')
        with self.assertRaises(ValueError):
            cp.parse_jev(bad, LABELS)
        wrong_argmax = jev_response('intent_3')
        wrong_argmax['answers']['intent']['choice'] = 'intent_4'
        with self.assertRaises(ValueError):
            cp.parse_jev(wrong_argmax, LABELS)

    def test_with_jev_uses_jev_only_when_confident_and_escalates_failures(self):
        rows = [dict(id=f'r{i}', label=l) for i, l in enumerate(['a', 'b', 'oos', 'c'])]
        jev = {'r0': dict(status='complete', prediction='a', score=0.99, cost_usd=0.0002),
               'r1': dict(status='complete', prediction='x', score=0.80, cost_usd=0.0002),
               'r2': dict(status='failed', prediction=None, cost_usd=0.0002),
               'r3': dict(status='complete', prediction='c', score=0.96, cost_usd=0.0002)}
        agent = {f'r{i}': dict(status='complete', prediction=p, cost_usd=0.01, elapsed_s=5)
                 for i, p in enumerate(['wrong', 'b', 'oos', 'c'])}
        out = {o['id']: o for o in cp.combine(rows, jev, agent, 0.96)}
        self.assertTrue(out['r0']['used_jev'])
        self.assertEqual(out['r0']['with_jev'], 'a')
        self.assertAlmostEqual(out['r0']['with_jev_cost'], 0.0002)
        self.assertFalse(out['r1']['used_jev'])
        self.assertEqual(out['r1']['with_jev'], 'b')
        self.assertAlmostEqual(out['r1']['with_jev_cost'], 0.0102)
        self.assertFalse(out['r2']['used_jev'])
        self.assertEqual(out['r2']['with_jev'], 'oos')
        self.assertTrue(out['r3']['used_jev'])

    def test_failed_agent_counts_as_incorrect(self):
        rows = [dict(id='r0', label='a')]
        out = cp.combine(rows, {}, {'r0': dict(status='failed', prediction=None, cost_usd=0.01)}, 0.96)
        summary = cp.summarize(out, 'agent')
        self.assertEqual(summary['accuracy'], 0.0)
        self.assertEqual(summary['missing'], 1)

    def test_summary_splits_in_scope_and_out_of_scope(self):
        out = [dict(gold='a', oos=False, agent='a', agent_cost=1.0), dict(gold='oos', oos=True, agent='b', agent_cost=1.0)]
        s = cp.summarize(out, 'agent')
        self.assertEqual((s['accuracy'], s['in_scope_accuracy'], s['oos_accuracy']), (0.5, 1.0, 0.0))

    def test_mcnemar_exact_known_values(self):
        self.assertEqual(cp.mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(cp.mcnemar_exact(0, 6), 2 / 64)
        self.assertAlmostEqual(cp.mcnemar_exact(10, 2), 2 * sum(math.comb(12, i) for i in range(3)) / 4096)
        self.assertAlmostEqual(cp.mcnemar_exact(5, 5), 1.0)

    def test_paired_t_and_bootstrap(self):
        r = cp.paired_t([-0.01] * 50 + [-0.012] * 50)
        self.assertLess(r['mean'], 0)
        self.assertLess(r['p_normal_approx'], 1e-6)
        lo, hi = cp.bootstrap_ci([1.0] * 10 + [0.0] * 10, seed=1, reps=500)
        self.assertLessEqual(lo, 0.5)
        self.assertGreaterEqual(hi, 0.5)

    def test_progress_line_reports_eta_and_projected_spend(self):
        class FakeLedger:
            spent = 0.0
            def status(self):
                return {'accounted_usd': self.spent}
        ledger = FakeLedger()
        progress = cp.Progress(10, ledger, 'test')
        progress.tty = False
        progress.started -= 20          # pretend 20 s have passed
        for _ in range(4):
            ledger.spent += 0.5
            progress.update({'status': 'complete'})
        line = progress.line()
        self.assertIn('4/10 (40.0%)', line)
        self.assertIn('ETA 00:30', line)            # 4 jobs in 20 s -> 6 left take 30 s
        self.assertIn('spent $2.00 → ~$5.00', line)
        progress.update({'status': 'complete', 'resumed': True})
        self.assertIn('(1 resumed)', progress.line())
        self.assertEqual(cp.clock(3725), '1:02:05')

    def test_agent_must_cite_retrieved_support(self):
        tools = [dict(tool='search_examples', result=[dict(support_id='train-00001')])]
        ok = cp.validate_agent('{"intent": "oos", "support_ids": ["train-00001"]}', {'oos': {}}, tools)
        self.assertEqual(ok['prediction'], 'oos')
        with self.assertRaises(ValueError):
            cp.validate_agent('{"intent": "oos", "support_ids": ["invented"]}', {'oos': {}}, tools)
        with self.assertRaises(ValueError):
            cp.validate_agent('{"intent": "oos", "support_ids": ["train-00001"]}', {'oos': {}}, [])


if __name__ == '__main__':
    unittest.main()
