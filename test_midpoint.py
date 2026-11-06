"""Offline correctness checks. These never consume API credits."""
import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import midpoint as m
from fixtures import TASKS


class MidpointTests(unittest.TestCase):
    def test_independent_grader_rejects_starters_and_accepts_references(self):
        result = m.verify_fixtures()
        self.assertEqual(len(result), 6)
        self.assertTrue(all(r['tests'] >= 4 for r in result.values()))

    def test_false_success_exit_is_not_a_pass(self):
        result = m.evaluate(TASKS['stable_unique'], 'raise SystemExit(0)\n')
        self.assertFalse(result['passed'])

    def test_fixture_data_never_enters_gate_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = m.Ledger(root/'ledger', 1)
            with patch.object(m, 'api_request', return_value={'answers': {'cheap_success': {'noul': .91}}, 'usage': {'cost': .00001}}) as request:
                result = m.gate(TASKS['chunked'], 'secret-not-persisted', .9, ledger, 'r1', root)
            state = request.call_args.args[2]['state']
            self.assertNotIn('tests', state)
            self.assertNotIn('reference', state)
            self.assertNotIn(TASKS['chunked']['reference'], json.dumps(state))
            self.assertEqual(result['selected_model'], m.CHEAP)
            self.assertNotIn('secret-not-persisted', (root/'gate.json').read_text())

    def test_malformed_gate_falls_back_without_claiming_free_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); ledger=m.Ledger(root/'ledger',1)
            with patch.object(m, 'api_request', side_effect=RuntimeError('unavailable')):
                result=m.gate(TASKS['chunked'],'secret',.9,ledger,'r1',root)
            self.assertEqual(result['selected_model'],m.STRONG)
            self.assertEqual(result['cost_status'],'reserved')
            self.assertGreater(result['cost_accounted_usd'],0)

    def test_invalid_probabilities_cannot_route_cheap(self):
        for score in [float('nan'),float('inf'),True,-1,1.01,'0.99']:
            with self.subTest(score=score), self.assertRaises(ValueError):
                m.route_from_response({'answers':{'cheap_success':{'noul':score}}},.9)

    def test_threshold_boundary_and_low_score(self):
        self.assertEqual(m.route_from_response({'answers':{'cheap_success':{'noul':.9}}},.9)['selected_model'],m.CHEAP)
        self.assertEqual(m.route_from_response({'answers':{'cheap_success':{'noul':.899}}},.9)['selected_model'],m.STRONG)

    def test_reservations_survive_restart_and_prevent_overspend(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'ledger'
            ledger=m.Ledger(path,1); token=ledger.reserve(.8,'r')
            restarted=m.Ledger(path,1)
            with self.assertRaises(RuntimeError): restarted.reserve(.21,'other')
            restarted.settle(token,.1,'r')
            self.assertAlmostEqual(m.Ledger(path,1).charged,.1)

    def test_proxy_enforces_model_bytes_output_and_task_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); ledger=m.Ledger(root/'ledger',1)
            meter=m.Meter(m.CHEAP,'secret',ledger,'r',.5,root)
            raw,record=meter.reserve({'model':m.CHEAP,'messages':[],'max_tokens':999999})
            self.assertEqual(json.loads(raw)['max_tokens'],m.MAX_OUTPUT)
            with self.assertRaises(ValueError): meter.reserve({'model':m.STRONG})
            with self.assertRaises(ValueError): meter.reserve({'model':m.CHEAP,'messages':['x'*70000]})
            tiny=m.Meter(m.STRONG,'secret',ledger,'r2',.001,root)
            with self.assertRaises(ValueError): tiny.reserve({'model':m.STRONG,'messages':[]})

    def test_proxy_missing_usage_retains_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); ledger=m.Ledger(root/'ledger',1)
            meter=m.Meter(m.CHEAP,'secret',ledger,'r',.5,root)
            _,record=meter.reserve({'model':m.CHEAP,'messages':[]})
            meter.finish(record)
            self.assertEqual(record['cost_status'],'reserved')
            self.assertGreater(ledger.charged,0)

    def test_sanity_split_requires_explicit_override(self):
        args=argparse.Namespace(task='rolling_mean',allow_sanity=False)
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':'fake'}),self.assertRaisesRegex(ValueError,'reserved'):
            m.run(args)

    def test_completed_run_resume_does_not_call_models(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); binary=root/'opencode'; binary.touch()
            args=argparse.Namespace(task='stable_unique',allow_sanity=False,opencode=str(binary),threshold=.9,
                budget_usd=.5,experiment_budget_usd=5,runs_dir=str(root/'runs'),run_id='existing',
                policy='cheap',timeout_s=180,account='test')
            protocol={'task':args.task,'fixture_hash':m.digest(TASKS[args.task]),'policy':args.policy,
                'cheap':m.CHEAP,'strong':m.STRONG,'jev':m.JEV,'threshold':args.threshold,
                'opencode_version':m.VERSION,'steps':8,'max_output_tokens':m.MAX_OUTPUT,
                'max_requests':m.MAX_REQUESTS,'timeout_s':180,'budget_usd':.5,
                'source_hash':m.digest({p:(m.ROOT/p).read_text() for p in ['midpoint.py','fixtures.py','model_snapshot.json']})}
            out=root/'runs'/'existing';out.mkdir(parents=True)
            m.dump(out/'manifest.json',{'protocol_hash':m.digest(protocol)})
            m.dump(out/'result.json',{'passed':True})
            with patch.dict(os.environ,{'OPENROUTER_API_KEY':'fake'}),patch.object(m,'api_request') as request:
                m.run(args)
                request.assert_not_called()

    def test_key_is_read_from_env_file_without_exporting_it(self):
        with tempfile.TemporaryDirectory() as temp:
            env_file=Path(temp)/'.env'
            env_file.write_text('# comment\nOTHER=x\nexport OPENROUTER_API_KEY="sk-test-123"\n')
            clean={k:v for k,v in os.environ.items() if k!='OPENROUTER_API_KEY'}
            with patch.dict(os.environ,clean,clear=True):
                self.assertEqual(m.key_from_environment(env_file),'sk-test-123')
                self.assertNotIn('OPENROUTER_API_KEY',os.environ)
            with patch.dict(os.environ,{'OPENROUTER_API_KEY':'shell-override'}):
                self.assertEqual(m.key_from_environment(env_file),'shell-override')
            with patch.dict(os.environ,clean,clear=True),self.assertRaisesRegex(RuntimeError,'OPENROUTER_API_KEY'):
                m.key_from_environment(Path(temp)/'missing.env')


if __name__=='__main__': unittest.main()
