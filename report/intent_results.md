# BANKING77 results

Rami’s individual experiment. All 3,080 official test examples; settings frozen before test collection. The fixed 0.96 cascade is **uncertified**: independent certification gave a 5.157% one-sided upper error bound, exceeding the 5% target. No positive-coverage Jev policy was certified. The predeclared fallback always invokes the agent; the certification test does not certify the agent’s own error rate.

| Condition | Correct / 3,080 | Accuracy | Macro-F1 | Mean USD |
|---|---:|---:|---:|---:|
| Jev only | 2626 | 85.26% | 0.8493 | $0.000152 |
| Strong direct | 2740 | 88.96% | 0.8865 | $0.000592 |
| Native retrieval agent | 2926 | 95.00% | 0.9501 | $0.010956 |
| 0.96 cascade (uncertified) | 2905 | 94.32% | 0.9432 | $0.004537 |
| Default all-agent fallback + Jev overhead | 2926 | 95.00% | 0.9501 | $0.011108 |
| Matched random acceptance (seed 32977) | 2740 | 88.96% | 0.8891 | $0.004450 |
| Nearest support example (BM25) | 2388 | 77.53% | 0.7745 | $0.000000 |

The fixed candidate accepted 1872/3080 (60.8%), with 62 accepted errors (3.31%). Its observed cost reduction against the always-agent condition was 58.6%. Its accuracy difference was -0.68 percentage points (paired stratified bootstrap 95% interval -1.01 to -0.39).

The one-sided 95% lower accuracy-difference bound is -0.94 points; the predeclared 2-point noninferiority target is met under this bootstrap analysis. This does not undo the failed independent risk certification.

Across 20 matched-coverage random seeds, mean accuracy was 89.17% (seed range 88.86%–89.71%). On escalated examples the fallback corrected 301 Jev errors and introduced 22 regressions.

Actual research spending, including development/prototype attempts: $37.9919 confirmed plus $0.1556 unresolved reservations. Deployment policy costs in the table count only the calls that policy uses, not every research comparator.

## Interpretation and limitations

Observed prompt-cache exposure is part of the measured cost comparison. Token and reasoning totals are recorded per condition in `intent_evidence.json`; do not interpret these batch prices as uncached API prices.

- The 0.96 candidate failed independent certification and remains uncertified; the default certified policy always escalates and offers no savings.
- One rollout per example, one public closed-set dataset, and one served model pair; no OOS or production banking claim.
- Binomial intervals assume independent exchangeable errors; stratification, utterance similarity, and grouped duplicates limit population-risk interpretation.
- Public benchmark pretraining contamination cannot be ruled out. Local held-out splitting does not establish absence of pretraining contamination.
- Replay/load elapsed times include concurrency and queue effects; they are not measured deployed-cascade latency. Serial live development results are separate.
- Prompts/catalog and native-agent overhead differ from the direct baseline by design. A cascade must be assessed against direct strong as well as the agent.
- Costs are observed OpenRouter charges including cache/reasoning where billed; unresolved transport attempts remain conservatively reserved.
- Stored tool traces reproduce the actual retrieval decisions. Floating-point lexical ties and model sampling can vary in a new live run; reproduction of reported numbers uses the saved trajectories.

## Reproduction

Prepare the pinned official data, unpack `intent_runs.tar.xz` into the repository root, and run `python3 intent_analysis.py`. No API key or model calls are needed for analysis. `intent_evidence.json` contains the full metrics, uncertainties, confusion pairs, error rows, provider counts and cost reconciliation.

## AI-use and authorship

Rami selected this workstream and directed the implementation and evaluation. Codex implemented the runner, checks, data collection, analysis, and this draft report text. The team must review the interpretation and authorship before incorporating it into the final report. No report or video has been submitted.

Data attribution: PolyAI/PolyAI-LDN, BANKING77, task-specific-datasets revision `57ec275d8078af65b7731c2a98be812d844a6d6b`, CC BY 4.0. Original study: Casanueva et al., “Efficient Intent Detection with Dual Sentence Encoders,” 2020, https://arxiv.org/abs/2003.04807.
