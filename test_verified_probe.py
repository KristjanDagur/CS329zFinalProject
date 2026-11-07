"""Offline checks for the SWE-bench Verified extension; no Docker, network or API calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import coding_probe as v1
import verified_probe as vp

BASE = 'b93a0e34d9b9b99d41103782b7e7aeabf47517e3'
EVAL_SCRIPT = f"""#!/bin/bash
set -uxo pipefail
source /opt/miniconda3/bin/activate
conda activate testbed
cd /testbed
export LANG=en_US.UTF-8
git config --global --add safe.directory /testbed
git status
git show
git -c core.fileMode=false diff {BASE}
python -m pip install -e .
git checkout {BASE} tests/queries/test_query.py
git apply -v - <<'EOF_1'
SECRET_TEST_BODY
EOF_1
: '>>>>> Start Test Output'
./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1 queries.test_query
: '>>>>> End Test Output'
git checkout {BASE} tests/queries/test_query.py
"""
ROW = {'instance_id': 'django__django-1', 'repo': 'django/django', 'base_commit': BASE, 'eval_script': EVAL_SCRIPT}


class VerifiedChecks(unittest.TestCase):
    def test_method_settings_are_identical_to_v1(self):
        vp.assert_method_unchanged()
        with patch.dict(vp.PROTOCOL, {'selected_files': 4}), self.assertRaises(RuntimeError):
            vp.assert_method_unchanged()

    def test_retrieval_matches_v1_for_a_single_root(self):
        with tempfile.TemporaryDirectory() as temp:
            ws = Path(temp)
            (ws / 'pydicom' / 'sub').mkdir(parents=True)
            (ws / 'pydicom' / 'tests').mkdir()
            body = '\n'.join(f'def helper_{i}():\n    return {i}' for i in range(40))
            (ws / 'pydicom' / 'jsonrep.py').write_text(body + '\ndef from_json(bulk_data_uri):\n    sequence = 1\n' + body)
            (ws / 'pydicom' / 'dataelem.py').write_text('class DataElement:\n    def from_json(self): pass\n')
            (ws / 'pydicom' / 'sub' / 'short.py').write_text('x = 1\n')
            (ws / 'pydicom' / 'empty.py').write_text('')
            (ws / 'pydicom' / 'tests' / 'test_json.py').write_text('from_json bulk sequence ' * 50)
            query = 'Locate from_json handling of BulkDataURI in sequence elements'
            self.assertEqual(vp.candidates(ws, query, ['pydicom']), v1.candidates(ws, query))

    def test_retrieval_spans_roots_and_skips_tests(self):
        with tempfile.TemporaryDirectory() as temp:
            ws = Path(temp)
            for d in ('lib/matplotlib', 'lib/mpl_toolkits/axes_grid1/tests', 'other'):
                (ws / d).mkdir(parents=True)
            (ws / 'lib/matplotlib/axes.py').write_text('def inset_axes(): pass\n')
            (ws / 'lib/mpl_toolkits/axes_grid1/inset_locator.py').write_text('def inset_axes(): pass\n')
            (ws / 'lib/mpl_toolkits/axes_grid1/tests/test_x.py').write_text('inset_axes ' * 99)
            (ws / 'other/inset.py').write_text('inset_axes ' * 99)
            paths = {c['path'] for c in vp.candidates(ws, 'inset_axes', ['lib/matplotlib', 'lib/mpl_toolkits'])}
            self.assertEqual(paths, {'lib/matplotlib/axes.py', 'lib/mpl_toolkits/axes_grid1/inset_locator.py'})

    def test_runner_prefix_discards_benchmark_targets(self):
        prefix = vp.runner_prefix(ROW)
        self.assertEqual(prefix, './tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1')
        self.assertNotIn('queries', prefix)
        with self.assertRaises(ValueError):
            vp.runner_prefix(dict(ROW, eval_script=EVAL_SCRIPT.replace('./tests/runtests.py', 'python runtests.py')))

    def test_setup_stops_before_any_gold_content(self):
        setup = vp.setup_lines(ROW)
        joined = '\n'.join(setup)
        for leaked in ('SECRET_TEST_BODY', 'test_query', 'git apply', 'git status', 'git show'):
            self.assertNotIn(leaked, joined)
        self.assertIn('python -m pip install -e .', setup)
        session = vp.session_prefix(ROW)
        self.assertNotIn('pip install', session)
        self.assertTrue(session.endswith('cd /testbed'))

    def test_run_tests_rejects_options_and_shell_syntax_without_docker(self):
        self.assertTrue(vp.valid_targets(['queries.test_query', 'lib/x/tests/test_a.py::TestA::test_b[1-2]']))
        for bad in ([], ['-k', 'x'], ['a;rm -rf /'], ['$(id)'], ['a b'], ['x|y'], ['`id`']):
            self.assertFalse(vp.valid_targets(bad), bad)
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'c.json'
            config.write_text(json.dumps({'workspace': temp, 'roots': ['django'], 'container': 'none',
                                          'session': 'true', 'prefix': 'true', 'timeout': 1, 'tail': 10,
                                          'log': str(Path(temp) / 'log')}))
            with patch.object(vp.subprocess, 'run') as run:
                self.assertEqual(vp.run_tests_main(config, ['a;b']), 2)
                run.assert_not_called()

    def test_test_command_is_unbuffered_and_quotes_targets(self):
        command = vp.test_command({'session': 'cd /testbed', 'prefix': 'pytest -rA'}, ['a/test_x.py::T::t[1]'])
        self.assertEqual(command, "cd /testbed && export PYTHONUNBUFFERED=1 && pytest -rA 'a/test_x.py::T::t[1]'")

    def test_forbidden_paths_and_edit_permissions(self):
        roots = ['lib/matplotlib', 'lib/mpl_toolkits']
        changed = ['lib/matplotlib/axes.py', 'lib/matplotlib/tests/test_axes.py', 'setup.py',
                   'lib/mpl_toolkits/axes_grid1/tests/test_a.py', 'lib/mpl_toolkits/axes_grid1/a.py']
        self.assertEqual(vp.forbidden_paths(changed, roots),
                         ['lib/matplotlib/tests/test_axes.py', 'setup.py', 'lib/mpl_toolkits/axes_grid1/tests/test_a.py'])
        rules = vp.edit_permissions(Path('/ws'), ['django'])
        self.assertEqual(rules['*'], 'deny')
        self.assertEqual(rules['django/**'], 'allow')
        self.assertEqual(rules['/ws/django/**/tests/**'], 'deny')
        self.assertLess(list(rules).index('django/**'), list(rules).index('django/tests/**'))

    def test_frozen_sample_is_consistent(self):
        sample = vp.SAMPLE
        ids = [t['instance_id'] for t in sample['tasks']]
        self.assertEqual(len(ids), 50)
        self.assertEqual(len(set(ids)), 50)
        pilot = sample['pilot_subset']['instance_ids']
        self.assertEqual(len(pilot), 10)
        self.assertTrue(set(pilot) <= set(ids))
        self.assertEqual(vp.instance_ids(), pilot)
        self.assertEqual(sample['dataset_revision'], vp.PROTOCOL['dataset_revision'])
        self.assertTrue({t['repo'] for t in sample['tasks']} <= set(vp.PROTOCOL['source_roots']))

    def test_v2_protocol_changes_only_the_task_list_and_cap(self):
        v1p = json.loads((vp.ROOT / 'verified_protocol.json').read_text())
        v2p = json.loads((vp.ROOT / 'verified_protocol_v2.json').read_text())
        bookkeeping = {'protocol', 'status', 'derived_from', 'selection', 'changes_from_v1'}
        self.assertEqual({k for k in set(v1p) | set(v2p) if v1p.get(k) != v2p.get(k)} - bookkeeping,
                         {'sample', 'experiment_budget_usd'})
        shared = vp.SAMPLE[v2p['sample']]['instance_ids']
        self.assertEqual(len(shared), 20)
        self.assertTrue(set(vp.SAMPLE['pilot_subset']['instance_ids']) <= set(shared)
                        <= {t['instance_id'] for t in vp.SAMPLE['tasks']})
        with patch.dict(vp.PROTOCOL, v2p):
            self.assertEqual(vp.instance_ids(), shared)

    def test_image_setup_commit_permission_changes_are_not_content(self):
        a, b = 'a' * 40, 'b' * 40
        raw = (f':100644 100755 {a} {a} M\tdjango/conf/locale/af/LC_MESSAGES/django.mo\n'
               f':100644 100644 {a} {b} M\tsetup.py\n'
               f':100644 100755 {a} {b} M\ttox.ini\n')
        self.assertEqual(vp.content_changed_paths(raw), ['setup.py', 'tox.ini'])

    def test_empty_patch_is_unresolved_without_grading_it(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(vp, 'tasks', return_value={'t1': {'instance_id': 't1'}}), \
                patch.object(vp.subprocess, 'run') as run:
            run.return_value.stdout, run.return_value.stderr, run.return_value.returncode = '', '', 0
            result = vp.grade(['t1'], {'t1': '   '}, 'r1', Path(temp))
        self.assertEqual(result['t1'], {'resolved': False, 'status': 'empty_patch'})


if __name__ == '__main__':
    unittest.main()
