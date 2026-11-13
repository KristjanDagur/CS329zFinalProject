"""Exact metric/accounting examples; these are unit fixtures, not benchmark tasks."""
import unittest
import intent_analysis as a


class AnalysisChecks(unittest.TestCase):
    def test_failures_remain_in_accuracy_and_macro_f1(self):
        result=a.metrics(['a','a','b','b'],['a',None,'a','b'],[.01]*4,[1,2,3,4],['a','b'])
        self.assertEqual(result['accuracy'],.5)
        self.assertEqual(result['missing_predictions'],1)
        self.assertAlmostEqual(result['macro_f1'],(.5+2/3)/2)
        self.assertAlmostEqual(result['usd_per_correct'],.02)

    def test_counterfactual_cost_uses_only_selected_agent(self):
        jev=[dict(prediction='a',cost_usd=.001,elapsed_s=.2,calls=1),dict(prediction='b',cost_usd=.001,elapsed_s=.3,calls=1)]
        agent=[dict(prediction='b',cost_usd=.02,elapsed_s=3,calls=2),dict(prediction='a',cost_usd=.03,elapsed_s=4,calls=3)]
        result=a.compose(jev,agent,[True,False])
        self.assertEqual(result['pred'],['a','a'])
        self.assertAlmostEqual(sum(result['cost']),.032)
        self.assertEqual(result['calls'],[1,4])
        self.assertEqual(result['latency'],[.2,4.3])

    def test_paired_bootstrap_retains_pairing(self):
        rows=[dict(label='a'),dict(label='a'),dict(label='b'),dict(label='b')]
        shared=dict(pred=['a','b','b',None],cost=[.01]*4)
        result=a.paired_bootstrap(rows,['a','a','b','b'],{'agent':shared,'same':shared},'agent',30,32977)
        self.assertEqual(result['same']['accuracy_difference_95'],[0,0])
        self.assertEqual(result['same']['cost_ratio_95'],[1,1])


if __name__=='__main__':
    unittest.main()
