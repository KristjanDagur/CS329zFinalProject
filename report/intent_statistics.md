# Paired statistical analysis: Jev cascade versus retrieval Sol

The fixed 0.96 cascade is **significantly cheaper and slightly less accurate** than always using the retrieval agent. The loss is small enough to meet the originally specified two-percentage-point margin. These are compatible conclusions: a detectable loss can still be within a practical tolerance. We cannot claim equal accuracy or successful risk certification.

This is a **post-hoc follow-up requested after the main results were observed**. It reuses the same 3,080 frozen paired questions, predictions, threshold and receipts. No test example, gate or model was changed; no new model calls or spending occurred. The two requested t-tests use questions as paired observations. Holm correction controls their two-endpoint family; both remain significant. Additional tests below are labeled sensitivity or secondary analyses.

## Requested paired t-tests

- **Accuracy:** 94.32% cascade versus 95.00% agent; difference **-0.682 percentage points**. Paired t(3079) = -4.2114, two-sided p = **2.61073e-05**, Holm-adjusted p = 2.61073e-05. The t-based 95% difference interval is -0.999 to -0.364 points. The difference favors the always-agent condition.
- **Cost:** $0.004537 versus $0.010956 per query; difference **$-0.006419/query**. Paired t(3079) = -67.3451, two-sided **p <1e-300** (numerical underflow; not p=0). The mean savings are $6.419 per 1,000 queries, with 95% t interval $6.232–$6.606. This tests no mean cost difference, not whether the reduction equals exactly 59%.

Relative savings are defined as **1 − mean(cascade cost)/mean(agent cost)**, not the average of per-question percentages. Observed reduction: **58.59%**. The 10,000-replicate paired within-intent bootstrap 95% interval is **57.066 to 60.031%**. Resampling whole intents gives **53.016 to 64.284%**. Neither interval includes zero or the originally specified 30% savings target.

## Exact accuracy check and practical tolerance

Accuracy is binary, so the exact paired McNemar test is a more natural check than a normal approximation. The cascade alone is correct on **2** questions; the agent alone on **23**. Both are correct on 2903; both wrong on 152. The exact two-sided p-value is **1.94311e-05**, confirming the small accuracy loss. Questions on which both methods agree do not drive this test.

The two-point accuracy margin was specified before test collection. Testing H0: accuracy(cascade) − accuracy(agent) ≤ −0.02 against a larger difference gives one-sided p = **2.79229e-16**. The one-sided 95% t lower bound is **-0.948 points**, above −2. Whole-intent cluster inference gives a lower bound of **-1.115 points** and p = 1.35857e-06. This supports noninferiority relative to that chosen margin, not equivalence. The original analysis, using a bootstrap rule specified before test collection, is preserved unchanged in intent_evidence.json.

## Dependence and data sensitivity

Similar questions within an intent may be dependent. We therefore use an intercept-only CR1 cluster standard error with intents as 77 clusters and a t reference with 76 degrees of freedom. At equal class sizes this is equivalent to a paired t-test on the 77 intent-level mean differences. The cluster accuracy p-value is **0.0105316**, with 95% interval **-1.200 to -0.164 points**. The cluster cost p-value is **4.29208e-33**. The whole-intent bootstrap gives an accuracy-difference interval of **-1.234 to -0.227 points**. This permits dependence within intents but still assumes independent intent clusters; it is a sensitivity analysis, not proof of generalization to unseen banking domains.

Excluding normalized support/test overlap leaves 3,064 questions; exact McNemar p = 1.94311e-05. Keeping one deterministic row per normalized test utterance leaves 3,076, removing 4 duplicates; exact p = 1.94311e-05. Neither operation alters the primary official-test result.

## Does confidence help beyond accepting a random subset?

We shuffle the acceptance mask while retaining the same accepted count, condition on the existing Jev/agent predictions, and ask whether a random mask reaches at least the observed cascade accuracy. Among 20,000 random masks, 0 match or exceed it; plus-one Monte Carlo p = 4.99975e-05. A stricter shuffle preserves each intent's accepted count, testing whether selection helps within intents rather than only choosing easy categories: 0 exceedances; p = 4.99975e-05. These are finite Monte Carlo p-values at the reported resolution, not exact tiny tail probabilities. They support confidence-based selection on these recorded trajectories, not a calibrated 5% risk guarantee.

## Other comparators and limits

The supplemental JSON includes Jev-only versus the retrieval agent, and the cascade versus direct Sol, each with paired t-tests and exact McNemar tests. Their two exact accuracy tests receive a separate Holm correction. They distinguish the cheap standalone classifier from the cascade and keep the lower-cost direct baseline visible. They are secondary analyses, not independent replications.

The certification failure remains unchanged: its one-sided upper accepted-error bound was 5.157%, above 5%. Later tests cannot erase it. Statistical significance does not certify safety, establish zero quality loss, or account for future model/provider changes. There is one model rollout per example; inference concerns variability across comparable questions, not uncertainty in these already observed finite-benchmark totals. Cached common fallback trajectories produce the intended pairing. Dollar results include Jev overhead and actual fallback charges; current cache exposure and provider prices may not transfer to a different deployment. Latency was collected under parallel load or on only 12 live development cases, so no deployed-latency significance claim is added.

## Reproduction and references

Install requirements-intent-stats.txt, prepare the pinned data, and unpack the existing intent_runs.tar.xz archive. Run `python3 intent_significance.py`; `--figures` optionally uses matplotlib 3.11.2. Results are intent_significance.json and this report. Seeds, input hashes, exact contingencies and package versions are recorded. The original evidence, source fingerprints and archive remain unchanged.

Methods: [SciPy paired t-test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_rel.html), [SciPy one-sample/one-sided tests](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_1samp.html), [statsmodels exact McNemar documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html), [cluster covariance documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html). The exact McNemar calculation uses SciPy's binomial test on discordant counts, avoiding an additional statsmodels dependency.

AI-use disclosure: Rami requested this follow-up; Codex implemented the offline tests and drafted the interpretation. Team review is required before incorporation into the final paper.
