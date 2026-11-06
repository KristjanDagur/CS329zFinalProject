"""Checks for the new experiment's important failure boundaries; no API calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import coding_probe as probe
from midpoint import Ledger


class ProbeChecks(unittest.TestCase):
    def test_invalid_decisions_cannot_be_used_as_file_scores(self):
        for value in (True, None, float('nan'), float('inf'), -0.1, 1.1, '0.8'):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                probe.choose({'answers': {'file_0': {'noul': value}}}, 1)

    def test_retrieval_cannot_read_benchmark_assets_or_tests(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'pydicom/tests').mkdir(parents=True)
            (root / 'pydicom/source.py').write_text('def repair_json(): return None\n')
            (root / 'pydicom/tests/test_secret.py').write_text('GOLD_PATCH_SECRET=' * 100)
            (root / 'gold_patch.py').write_text('GOLD_PATCH_SECRET=' * 100)
            found = probe.candidates(root, 'repair json GOLD_PATCH_SECRET')
            self.assertEqual([f['path'] for f in found], ['pydicom/source.py'])
            self.assertNotIn('GOLD_PATCH_SECRET', json.dumps(found))

    def test_bad_jev_response_falls_back_to_native_explorer(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            meter = probe.ExplorerMeter('fake-key', Ledger(out/'ledger', 1), out, out, 'jev',
                {probe.PROTOCOL['jev_model']: {'pricing': {'prompt': '0.000000042', 'completion': '0'}}})
            with patch.object(probe, 'candidates', return_value=[{'path': 'pydicom/source.py', 'snippet': 'x'}]), \
                 patch.object(probe, 'api_request', return_value={'answers': {}, 'usage': {'cost': .00001}}), \
                 patch.object(meter, 'native', return_value={'native': True}) as native:
                result = meter.exploration({'messages': [{'role': 'user', 'content': 'Find bug'}]})
            self.assertEqual(result, {'native': True})
            native.assert_called_once()
            self.assertTrue(json.loads((out/'localization-0.json').read_text())['fallback'])
            self.assertAlmostEqual(meter.ledger.charged, .00001)

    def test_budget_denial_happens_before_request(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            model = probe.PROTOCOL['writer_model']
            meter = probe.ExplorerMeter('fake-key', Ledger(out/'ledger', .001), out, out, 'native',
                {model: {'pricing': {'prompt': '.000002', 'completion': '.00001'}}})
            with patch.object(probe, 'api_request') as request, self.assertRaises(RuntimeError):
                meter.native({'messages': []}, 'build')
            request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
