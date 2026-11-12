# Rami's proposed workstream: BANKING77 intent decisions with agent escalation

Date: November 12, 2026. Owner: Rami with Codex. Branch: `rami`.
Status: recommendation and research plan, not an implemented experiment or frozen protocol. No paid calls or training were performed for this review. Teammates have not yet chosen their final individual workstreams. Review their choices before claiming exclusivity.

## 1. What has changed on main

Reviewed `main` at `de2bf383af89a61753248f9638e308d190d096ee`: 31 commits after the original Rami integration, 38 changed/added paths. Read the current README, instructions, protocols, runner changes and evidence JSONs. These are committed experiment records, not independently rerun results in this review.

- **Kristjan's official Verified pilot:** `verified_probe.py`, a frozen 50-task sample and Docker evaluation support. The completed 10-task, three-condition pilot reports native 9/10, Jev 9/10, search 8/10. Mean billed task cost is $0.10644 / $0.05573 / $0.05437 respectively. This supersedes the five-task local pilot as the stronger coding baseline; it does not establish equivalence from ten tasks.
- **Omar's v2 development experiment:** 164 runs over 41 locally validated pydicom issues, with native/Jev/search/oracle and phase timing. Success counts are 18/19/21/20 out of 41; Jev cost and elapsed time are about 35% below native. Oracle does not improve success here, indicating that later writer behavior matters substantially.
- **Localization experiments:** 225 dev issues across six repositories. Jev hit@3 is 85.3% versus search 70.2%. Larger 24/48-candidate lists and strong/cheap LLM selectors were also measured; the LLM comparisons use the same 12 candidates. This already covers a simple localization-only extension of Rami's original pilot.
- **Restricted writer v3:** 123 runs on the same 41 issues, with access limited to preselected files. Oracle/Jev/search solve 16/14/11. The Jev-versus-search paired success comparison has p=0.375: a useful direction, not a demonstrated significant improvement.
- **Engineering:** dotenv key loading, pinned Python 3.12 evaluator requirements, Linux support, protocol-aware batches/archives, per-run state in v3, phase timing, analyses, expanded offline checks, and a combined report.

Important handoff limits: the README still says Verified raw runs are not archived; `build_verified_report.py` needs local `runs/verified/`. `verified_probe.py` fingerprints `coding_probe.py`, so changing that file can invalidate resume/reproduction. The README contains old chronological statuses below its newer overview; use the newest overview and evidence. Current recorded project spend is about $34, not a verified current account balance. The shared 20-task Verified continuation is a recorded plan, not a completed result.

## 2. Recommendation and connection to the proposal

Use **BANKING77 as Rami's one primary dataset**. It was already in the original proposal. The instructor recommended an initial, narrow substitution in an existing harness before broader investigation; the team has now completed substantial coding-harness mechanical work. Returning to the original intent-decision question is a deliberate second application of the same System One cost/performance hypothesis, rather than another untested harness redesign.

Research question: **Can Jev handle sufficiently clear intent decisions directly and escalate uncertain cases to an existing retrieval-using agent, reducing total cost while preserving end-to-end intent accuracy?**

BANKING77 provides 77 intents, 10,003 training examples and 3,080 test examples. Official file metadata checked in this review: train.csv 839,073 bytes, test.csv 239,961 bytes, categories.json 2,036 bytes; total **1,081,070 bytes, about 1.08 MB**. No Docker images, repository builds, GPU, database server, or external web search are needed. Evaluation is comparison with the published intent ID.

Source revision: `PolyAI-LDN/task-specific-datasets@57ec275d8078af65b7731c2a98be812d844a6d6b`. File metadata was checked; this review did not inspect test utterances, run predictions, or measure performance. Reconfirm revision/license, validate data counts and save SHA-256 receipts during implementation.

CLINC150 remains a possible later transfer/out-of-scope study. It is not part of the primary workstream: it introduces 150 classes and a distinct OOS task, whereas BANKING77 is closed-set. Do not present BANKING77 results as evidence of rejecting unseen intents. Spider/SQL is a plausible compact alternative, but requires a new task adapter and careful execution/test-suite evaluation; it offers less direct continuity with the original proposal.

## 3. Concrete system

1. Give Jev the incoming utterance and the complete 77-intent catalog. Use canonical intent names with fixed descriptions and, if chosen on development data, one fixed real support example per intent. Never invent benchmark examples. Jev returns a typed **Choice** plus per-intent probabilities. The documented limit is 255 options, so 77 does not require a lossy candidate shortlist.
2. Accept Jev's selected intent if its maximum class probability meets the frozen threshold. Otherwise escalate. Treat the vendor's distribution-concentration `confidence` separately; it is not automatically correctness probability. Invalid responses, unknown IDs and API failures escalate and retain their costs.
3. The fallback is a bounded native OpenCode agent with a read-only `search_examples(query)` tool over the support partition and an intent-catalog lookup. It retrieves real labeled training examples, reasons about confusing intents, and returns an intent ID with supporting example IDs. This must exercise actual tools; a single strong classification call is separately labeled below.
4. Use OpenCode's existing loop and request metering. Add a separate intent runner/adapter; do not rewrite the coding loop or modify `coding_probe.py`, `verified_probe.py`, or their frozen protocols. Per-run state and task/service ledgers should follow the team's newer isolation practices. Pin the served model/provider revision, prompts and tool limits before evaluation.

Provisional fallback caps: four generative calls, two retrieval calls returning at most eight short examples each, 1,024 output tokens/call, 120 seconds/task, explicit dollar cap and no silent retries. Validate these limits on training-derived development cases; freeze or amend them before final evaluation, not after observing final failures. Retrieval latency and indexing cost belong in the accounting.

## 4. Splits and acceptance policy

- Seeded stratified partition of the official **training** set: 70% support/retrieval, 15% prompt/threshold development, 15% independent threshold certification. Group normalized duplicate utterances before partitioning. Audit any official train/test overlap and disclose the treatment before freezing; do not quietly rewrite the official test set.
- Jev and direct-strong classification receive the same frozen catalog/exemplars. Support records used by the fallback come only from the 70% support partition. Development/certification examples must never enter its index.
- Pick one threshold on development data, maximizing coverage with a conservative accepted-error target. Then freeze prompts, model, score definition, threshold and retriever. On the untouched certification partition, report accepted count, errors and a one-sided 95% binomial error bound for this one fixed policy. If certification fails, report failure; do not search new thresholds on that partition. A separately declared all-agent fallback is permitted, with zero Jev coverage reported honestly.
- Target: no more than 5% error among Jev-accepted cases, at least 30% total cost reduction, and end-to-end accuracy within a proposed 2 percentage points of the always-agent comparator. These are decision targets, not predicted results. Claim the risk bound/noninferiority only if the held-out evidence and sampling assumptions support them; otherwise report an inconclusive or negative outcome.
- Prefer the complete 3,080-example official test set. Choose the affordable count using measured development costs **before any test outcomes**. If necessary, predeclare a seeded 1,540-example sample (20 per intent) or 770 (10 per intent); disclose that it is a subset evaluation. Freeze IDs and exclusions before querying models.

## 5. Comparisons that make the result meaningful

- **Jev only:** always use its 77-way decision.
- **Strong direct:** one strong-model classification call with the same catalog/exemplars, no tools. Essential: a cascade must be competitive with this cheap strong baseline, not just with a multi-step agent.
- **Strong tool-using agent:** always execute the same fallback workflow.
- **Jev + confidence-based escalation:** the primary policy.
- **Random acceptance at matched coverage:** accept exactly as many Jev predictions as the main policy, but choose them randomly without using Jev's scores; escalate the rest to the identical fallback. Use fixed random seeds and report variation. This tests whether confidence is informative.
- Optional zero-inference-cost reference: nearest-example/BM25 classification over the support corpus. It cannot use held-out labels in retrieval.

Record one Jev prediction, one direct-strong output and one always-agent trajectory per final example. Keep the fallback prompt independent of Jev's prediction/score, so cached always-agent trajectories are valid counterfactuals for both routed policies. Offline selection estimates deployment cost; it is not another live agent run. Do not add both selected and unselected trajectories to one deployed task's cost, but do report all actual research spending. Verify orchestration and live latency on a small, predeclared development subset; report replay and live latency separately.

Metrics: end-to-end accuracy/macro-F1, total dollars/query and dollars/correct query, accepted coverage and accepted error with intervals, p50/p95 live latency, retrieval/call counts, score reliability, and fallback corrections versus regressions. Analyze high-confidence errors and confusable intent pairs. Use paired comparisons and show uncertainty; never assume the fallback is always correct.

## 6. End-to-end execution and budget

1. **Day 1: data/evaluation.** Pin sources, construct grouped splits and label catalog, build the training-only index, establish deterministic label scoring, and check for leakage. No paid models needed.
2. **Day 2: real smoke test.** Run about 30 training-derived examples through all actual execution paths. Verify 77-choice schema, real retrieval calls, metering, fallback, invalid-output handling and resume behavior. Record the native/direct-strong baselines before gating changes. Initial spending cap: $5.
3. **Days 3–4: development and certification.** Develop on the designated partition, select the threshold once, certify it independently, and project final spending. Freeze a machine-readable protocol and final IDs. Additional budget allowance: $15.
4. **Day 5: final paired evaluation.** Run the three required trajectories on the frozen set, with checkpoint/resume and bounded concurrency. Final-evaluation allowance: $80. At 3,080 test examples this requires a measured combined mean cost below about $0.026/example for Jev + direct strong + always agent. If the development projection exceeds this, reduce the frozen sample before test outcomes, not halfway through it.
5. **Days 6–7: analysis and handoff.** Recompute both routed policies without duplicate paid calls; verify a small live development subset; create error analysis, cost/accuracy and risk/coverage figures, report section, source/data hashes and portable evidence. Keep $20 contingency for failures/reproduction.

Proposed total ceiling: **$120 OpenRouter on Rami's account**, including development and contingency, subject to checking actual remaining allowance before execution. It is a planning ceiling; replace the unit-cost assumptions with smoke-run receipts before final evaluation. No Tinker training is needed. Use Tinker only later if a distinct trained-router comparison is justified by data and time; Jev's architecture is not assumed trainable through Tinker. Do not pool teammates' credits or assume unused balances.

Stop conditions: no reliable positive-coverage threshold; a strong direct call dominates the cascade; retrieval does not help; projected cost exceeds the cap; or baseline/evaluator checks fail. Preserve and report these outcomes rather than adding datasets until something wins.

## 7. How this combines with teammates' work

The common claim is: which generative decisions can a System One model replace, and under what cost/quality tradeoff? Existing coding studies cover file selection; this work covers accepting an intent decision versus invoking retrieval/reasoning. Final individual assignments remain undecided; those are existing work areas, not assignments made here.

Use common run fields: dataset/version/split, task ID, seed, condition, model/provider revisions, harness/source hash, decision/score/threshold, selected route, correctness, cost components, latency components, tool calls and failure category. Report each dataset's success and normalized cost relative to its strong baseline separately. Do not average coding repair success and intent accuracy into a single pooled percentage. Share the paper's methods/accounting conventions and merge the independent result sections/artifacts at the end.

Before implementation, bring `rami` up to current `main` without losing any branch-only work. This review's connector could read but could not write/fast-forward the branch; no successful sync has been claimed. Documentation changes are isolated on `rami`; `main` and teammates' branches should remain untouched.

Sources: [reviewed team main](https://github.com/KristjanDagur/CS329zFinalProject/tree/de2bf383af89a61753248f9638e308d190d096ee), [official BANKING77 source](https://github.com/PolyAI-LDN/task-specific-datasets/tree/57ec275d8078af65b7731c2a98be812d844a6d6b/banking_data), [BANKING77 paper](https://arxiv.org/abs/2003.04807), [CLINC150 source](https://github.com/clinc/oos-eval), [TypeSafe Choice](https://docs.typesafe.ai/primitives/choice), [Jev API guide](https://openrouter.ai/docs/guides/community/jev).
