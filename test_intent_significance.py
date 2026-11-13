"""Statistical boundary checks with unit fixtures, never new benchmark examples."""
import itertools
import math
import statistics
import unittest

import numpy as np
from scipy import stats

import intent_significance as s


class StatisticalChecks(unittest.TestCase):
    def test_t_test_uses_pairing_not_independent_samples(self):
        baseline=np.array([100,200,300,400],dtype=float)
        result=s.t_test(baseline+[1,2,3,4],baseline)
        expected=2.5/(statistics.stdev([1,2,3,4])/math.sqrt(4))
        self.assertAlmostEqual(result['t'],expected,places=12)
        self.assertEqual(result['df'],3)
        self.assertAlmostEqual(result['mean_difference'],2.5)
        with self.assertRaises(ValueError):
            s.t_test([1,2],[1])

    def test_mcnemar_exact_tail_and_agreement_invariance(self):
        x=[1]*2+[0]*23
        y=[0]*2+[1]*23
        result=s.mcnemar(x,y)
        expected=2*(1+25+math.comb(25,2))/2**25
        self.assertAlmostEqual(result['pvalue'],expected,places=15)
        self.assertEqual(result['candidate_only_correct'],2)
        self.assertEqual(result['agent_only_correct'],23)
        self.assertEqual(s.mcnemar(x+[0,1]*50,y+[0,1]*50)['pvalue'],result['pvalue'])
        self.assertEqual(s.mcnemar([1,0],[1,0])['pvalue'],1)
        named=s.mcnemar(x,y,left='cascade',right='direct')
        self.assertEqual(named['direct_only_correct'],23)
        self.assertNotIn('agent_only_correct',named)

    def test_cluster_se_matches_t_test_on_balanced_group_means(self):
        difference=np.array([0,1,-1,1,2,0,-1,2],dtype=float)
        labels=['a','a','b','b','c','c','d','d']
        result=s.cluster_mean_test(difference,labels)
        reference=stats.ttest_1samp([.5,0,1,.5],0)
        self.assertAlmostEqual(result['t'],reference.statistic,places=12)
        self.assertAlmostEqual(result['pvalue'],reference.pvalue,places=12)
        self.assertEqual(result['df'],3)

    def test_random_mask_sampler_matches_enumerated_gain_distribution(self):
        delta=np.array([-1,-1,0,1])
        exact=[sum(z) for z in itertools.combinations(delta,2)]
        sampled=s.random_gains(delta,2,40000,np.random.default_rng(1234))
        for value in set(exact):
            self.assertAlmostEqual(float(np.mean(sampled==value)),exact.count(value)/len(exact),delta=.015)
        self.assertTrue(np.all(s.random_gains(delta,0,10,np.random.default_rng(1))==0))
        self.assertTrue(np.all(s.random_gains(delta,4,10,np.random.default_rng(1))==-1))

    def test_holm_adjustment_is_monotone_in_rank(self):
        result=s.holm({'a':.01,'b':.04,'c':.03})
        self.assertEqual(result,{'a':.03,'c':.06,'b':.06})

    def test_bootstrap_keeps_pairing_and_ratio_of_means(self):
        correct=np.array([1.,0.])
        cost=np.array([.1,10.]);base=np.array([1.,10.])
        result=s.bootstrap(correct,correct,cost,base,['a','b'],30,1234)
        self.assertEqual(result['within_intent']['accuracy_difference']['ci95'],[0,0])
        expected=1-10.1/11
        for bound in result['within_intent']['cost_reduction']['ci95']:
            self.assertAlmostEqual(bound,expected)
        self.assertNotAlmostEqual(expected,(.9+0)/2)

    def test_underflow_is_not_reported_as_zero_probability(self):
        result=s.p_fields(0.)
        self.assertIsNone(result['pvalue'])
        self.assertTrue(result['numerical_underflow'])
        self.assertEqual(result['p_text'],'<1e-300')


if __name__=='__main__':
    unittest.main()
