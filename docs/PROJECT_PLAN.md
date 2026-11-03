# End-to-End Project Plan

Planning date: 2026-11-03. Status: proposed protocol; no experiments executed. Immediate priority: November 4 prototype target and November 6 midpoint submissions.

## 1. Research question and scope

**Question:** In a fixed OpenCode coding harness, can a Jev decision gate route some tasks to a cheaper coding model while retaining the strong-model harness's task success at lower total cost?

**Primary hypothesis:** A frozen confidence-gated router yields a better task-success/cost tradeoff than always using the strong model, always using the cheap model, and random routing at the same cheap-model coverage. A strong result would retain performance within a predeclared 5 percentage-point margin while reducing mean inference cost by at least 20%. These are proposed decision targets, not predicted results.

**Secondary hypothesis:** Measured confidence in cheap-model task success identifies a useful subset of tasks with at most 5% observed failure among cheap-accepted tasks. Statistical support and coverage must be reported alongside that rate. This is distinct from being within 5 percentage points of the strong baseline.

The contribution is a controlled empirical study of where a System One decision model helps an existing coding harness, including its failures and overhead. It is not a new general-purpose agent, a broad router leaderboard, or a claim that Jev's probabilities guarantee correctness.

### Proposal and instructor feedback translated into decisions

The proposal, “Is an expensive agent always the way to go?”, proposes fast Jev/Kev decisions, escalation to an agent that can retrieve evidence/use tools/revise decisions, calibration to a 5% accepted-error target, and cost/time/risk-coverage evaluation. It names BANKING77 and CLINC150, agent-only and random-escalation controls, threshold transfer, and high-confidence error inspection.

The instructor awarded 4/4 and recommended small mechanical substitutions in an existing open harness such as OpenCode, linear experimentation before redesign, a strong-model reference, a tighter cost/performance frontier, focused exploration, and a formal final report.

Our proposed bridge is one bounded model-selection decision at task launch. Jev receives the issue and permitted repository metadata and estimates whether the fixed cheap coding setup can solve it. High-scoring tasks use the cheap coding model; all others use the strong coding model in the same harness. This preserves confidence-gated escalation while making the first experiment small. It is an outer routing layer around an existing harness, not yet a substitution for an internal tool-planning call. Describe that limitation accurately in the report.

If the instructor specifically requires an internal harness decision, the next candidate is choosing the model for an existing exploration subagent at its delegation boundary. Pursue that only after a small integration probe proves that boundary exists and is measurable; replace the primary intervention through a recorded team decision rather than adding another full experiment track.

### Scope boundaries

- Primary: one harness, one cheap/strong coding-model pair, one Jev gate, one coding benchmark, one locked primary threshold.
- Optional: one Kev substitution OR one Tinker-trained router comparison after the primary pipeline works. Prefer the Tinker extension if it answers a demonstrated calibration/routing failure.
- Optional appendix: BANKING77-to-CLINC150 transfer; use it as a decision-model diagnostic, not proof about coding-agent success.
- Defer: RL, end-to-end coding-agent training, multiple harnesses, many frontier models, custom datasets as a major track, repeated redesigns, and several in-loop decision sites.

## 2. Minimal architecture and interfaces

At task launch: **task-visible state → Jev score → frozen calibration/threshold → cheap or strong model → unchanged OpenCode harness → patch → independent evaluator**.

Use deterministic code for execution, budgets, and logging. Jev selects a finite option; it does not generate a patch, a shell command, or tool arguments. No strong-model prescreen is allowed in the primary router: it would add cost and confound the comparison.

### State and gate

- State includes issue text, public task metadata, and a reproducible, size-capped repository summary if needed. Identical information budgets apply across routers. Include the summary generation cost and latency.
- Exclude gold patches, benchmark evaluation tests/labels, future tool results, and baseline success outcomes from inference state.
- Start with one Noul-style question: whether the pinned cheap model, fixed harness, and fixed resource limit can solve this task. Store the raw yes probability; compare it with observed cheap-run success on development data.
- If Choice is used instead, retain the full probability vector. The vendor's `confidence` statistic describes distribution concentration; it is not automatically the probability that the cheap coding agent succeeds. Calibrate against the actual outcome being gated [S3].
- Route cheap only when the calibrated score meets threshold. Invalid response, timeout, missing required state, or unsupported input routes strong and is charged to the gate's overhead.
- One route per task. No hidden rerouting after failed tests in the primary experiment. A cheap-first retry cascade is a separate future intervention with different cost accounting.

### Implementation layout to create during P2/P3

- `configs/`: pinned models/providers, harness revision, resource caps, prompts, frozen experiment protocols.
- `src/providers/`: Jev adapter and generative-model usage normalization; add Kev/Tinker adapters only when needed.
- `src/harness/`: thin OpenCode invocation wrapper and trace collection.
- `src/routing/`: raw scores, calibration, thresholding, deterministic controls.
- `src/evaluation/`: task manifest, evaluator integration, paired statistics, cost aggregation.
- `scripts/`: smoke, development, frozen evaluation, and figure commands.
- `tests/`: meaningful checks for split leakage, routing failover, evaluator correctness, resume/deduplication, and nonzero cost capture.
- `manifests/`: immutable task splits, configs, run IDs, artifact checksums, completed status.
- `reports/figures/`: generated plots and report sources. Large traces, images, and checkpoints live outside git, with accessible artifact pointers.

Prefer Python for orchestration and analysis. Keep OpenCode integration limited to config/CLI invocation first. Do not add a web app or replace the harness's execution loop. Pin package/runtime versions and publish exact commands once they have been tested; there is no runnable project package yet.

## 3. Dataset, labels, and leakage controls

### Coding benchmark

Default candidate: SWE-bench Lite, which provides 300 test tasks and 23 development tasks [S7]. Use the official evaluator; ensure the execution machine can build/run its task environments. Credits cover model services, not necessarily Docker hosting or general GPU compute.

1. Start with two official development tasks to validate patch extraction, clean repository state, and evaluator execution. These are smoke tasks and remain outside the final test set.
2. Use the official development instances for engineering and routing development. Partition these by task into calibration-fit and threshold-selection portions before fitting; with only 23 tasks, keep the method simple and label estimates exploratory. No Tinker training on this tiny collection alone.
3. Before opening test outcomes, create a seeded, repository-stratified manifest for a primary 60-task subset of the official test set. Choose the final affordable count using development costs, never test success. Freeze inclusion/exclusion rules and IDs.
4. Expand toward 100 tasks only if the cost projection fits the evaluation cap BEFORE test outcomes are inspected. A smaller study must report its uncertainty and limited power; it cannot establish equivalence merely because significance is absent.
5. If the cheap model rarely solves development tasks or the gate cannot select useful coverage, report that diagnostic. Do not tune on the test subset. Consider a cheaper/easier primary benchmark only through a recorded protocol change before final evaluation.

A 23-task development set cannot substantiate a 5% risk guarantee. For example, even zero errors need at least 59 independent accepted calibration cases for a single pre-specified threshold's one-sided 95% binomial upper bound to fall below 5%. Threshold search and correlated coding tasks require additional care. Use the coding track's 5% target as exploratory unless a larger independent calibration sample supports a formal bound. If stronger calibration is needed, add separately sourced training/development tasks with explicit overlap checks; never repurpose the locked test set.

### Outcomes and baseline data

- Task success is the official evaluator's test outcome for the produced patch; strong-model output is a reference condition, not ground truth.
- Collect one paired cheap and strong rollout per development task under identical task prompts, tools, caps, and harness revision. Store both outcomes, costs, and traces.
- Cheap outcome is the binary target for the gate. Strong outcome establishes the actual reference performance and reveals tasks on which neither setup succeeds.
- One rollout per task estimates that run protocol, not a task's inherent solvability. If affordable, repeat a preselected development subset to quantify stochasticity.
- Preserve unresolved tasks, malformed patches, timeouts, and model failures in the declared end-to-end denominator. Mark infrastructure errors separately and apply one fixed retry rule to every condition.
- Isolate task working directories. Keep hidden evaluator assets unavailable to the agent and router. Keep the final test labels inaccessible to training/calibration scripts.

### Optional intent-transfer diagnostic

If the main coding result and report are on schedule, use official BANKING77 and CLINC150 data [S8, S9]. Split BANKING77 training data into disjoint training, calibration, and threshold-selection sets; evaluate its untouched official test set. Freeze the calibration map and threshold, then apply them to CLINC150 with its appropriate label descriptions and explicit out-of-scope outcome. Report in-scope accuracy, OOS false acceptance, and per-domain risk/coverage separately. Different label sets mean this tests policy transfer, not identical predictions across datasets.

If demonstrating agent escalation on intent tasks, define versioned knowledge-base tools and a bounded tool-using fallback agent. A single strong-model classification call is a simpler comparator and must be labeled as such. Public datasets may have appeared in pretraining or Kev fine-tuning; audit available model cards and never claim contamination-free results merely because the local split is held out.

## 4. Experiment sequence and controls

### E0 — Mechanical feasibility, before calibration or training

Run the unchanged harness on smoke tasks with both coding models. Log Jev scores on the same task-visible states in shadow mode, then check that the route selects the intended configured model on a small development sample. Verify evaluator outcomes and billed usage. Success means a traceable, bounded, reproducible run; it does not mean the router improves quality.

### E1 — Development and frozen primary study

Compare these conditions on exactly the same tasks:

1. **Always strong:** unchanged OpenCode with one strong tool-capable model. The instructor's GPT-6.1-Sol/Claude Opus 5.5 suggestions are candidates; use one accessible, affordable, pinned model, not an invented API ID.
2. **Always cheap:** identical harness with one cheaper tool-capable model. Select from live available models during P2; keep that pair fixed thereafter.
3. **Heuristic route:** a deterministic rule based on task-visible features, chosen on development data, to test whether a learned/decision-model gate is necessary.
4. **Random route:** random cheap/strong assignments with the same cheap-task count as the frozen Jev policy. Repeat random assignments offline and report their distribution. Also compare cost-matched routing because equal coverage does not imply equal cost.
5. **Jev route:** one frozen score/prompt/calibration/threshold choosing cheap versus strong.

Choose threshold on development data, maximizing cheap coverage subject to the declared risk target and reporting whether that target has only empirical or statistical support. If no positive-coverage threshold qualifies, the conservative policy routes everything strong; report its overhead and zero cheap coverage honestly.

With tiny development data, start with the raw probability and one simple monotone calibration alternative only. Do not search many prompts, feature sets, and calibrators. Record every tried configuration, including failures. Lock the chosen primary method before final evaluation.

Collect paired strong/cheap outcomes for the held-out subset. Since the primary router chooses before generation and never changes trajectories, replaying its selections over these paired runs supports controlled offline evaluation. Count only the selected trajectory plus gate/state cost as estimated deployment cost; record all actual experiment spending separately. Execute a small preselected live routed subset to verify orchestration and latency; never sum both counterfactual trajectories as one deployed task.

### E2 — One targeted extension, conditional

**Preferred use of Tinker:** train one supported small generative model as a binary decision router using a separately collected training set of task-visible states and cheap-run outcomes. Compare its untuned base and fine-tuned version on the same frozen protocol. Use a dedicated fit/calibration split and do not touch final test outcomes for checkpoint choice. Check provider/output terms before using generated labels.

Do not assume Tinker supports Kev's custom architecture or classification head. Confirm supported models and loss/output interfaces first. For a generative binary router, prefer normalized label-token probabilities when supported; self-reported JSON confidence alone is not calibrated probability. Include sampling/logprob requests in cost accounting. A standard LoRA/SFT router is a distinct model family and must not be called Jev or Kev.

A training gate requires enough independent training data to justify it, measured routing failures, a simple untuned comparator, a projected bill within the cap, and time to analyze the result. If those conditions fail, leave the credits unused. An optional Kev substitution is an alternative extension; pin its source and weight revisions, verify local hardware, and measure local runtime separately [S4].

## 5. Metrics, uncertainty, and interpretation

For N tasks, let S/C denote the strong/cheap coding run, A the tasks routed cheap, and g_i the complete gate/state cost. For each task, the deployment-cost estimate is `g_i + cost(C_i)` when accepted cheap, otherwise `g_i + cost(S_i)`. The strong baseline has no artificial router overhead.

- **Task success:** successful official evaluations / all declared tasks; paired difference relative to always strong.
- **Cost:** mean billed-equivalent dollars/task, dollars per successful task, and total actual experimental spend. Include prompts, completions/reasoning, cache charges, retries, failed calls, routing, and state construction.
- **Coverage:** `|A| / N`. **Selective risk:** cheap-run failures within A / `|A|`. With no accepted tasks, risk is undefined, not zero.
- **Latency:** live end-to-end median/p95, router latency, and task runtime with stated concurrency and hardware. Offline route replay alone cannot establish live latency savings.
- **Calibration:** Brier score, reliability plot, and a predeclared coarse-bin ECE for cheap-success scores. Avoid elaborate binning conclusions on 23 development tasks.
- **Error analysis:** all high-confidence cheap failures, strong-only successes, cheap-only successes, and failure categories such as missing context, long-horizon edits, tool misuse, and evaluator/infrastructure failure.

Use paired bootstrap intervals resampling tasks for cost and success differences. For multiple rollouts, cluster by task; add a repository-level sensitivity analysis where feasible. Give binomial intervals for risk and clearly separate point estimates from confidence bounds. Check whether the lower confidence bound for `success(Jev) - success(strong)` exceeds -0.05 before claiming the proposed noninferiority target. If the study is underpowered, say “inconclusive,” not “matched performance.”

Primary figures: cost versus task success with uncertainty; risk versus coverage; cost versus coverage; reliability diagram; end-to-end latency distribution; compact breakdown of high-confidence mistakes. Threshold sweeps on the test set are descriptive curves, not a way to select a new primary threshold. Explain which configurations are dominated and which improve the measured Pareto frontier.

Negative results are valid: the gate might cost more than it saves, fail to find a reliable cheap subset, or lose to the heuristic/random control. Report these outcomes directly. Typed outputs prevent a class of format errors; they do not establish semantic correctness.

## 6. Credits and cost controls

Starting allocations supplied by the team: $750 Tinker and $600 OpenRouter, spread across three accounts. Verify current balances, expiry, eligible services, rate limits, and checkpoint visibility before scheduling runs. Keep separate service/account ledgers; do not assume credits or checkpoints transfer.

### Proposed OpenRouter allocation — $600

- Access, logging, evaluator smoke: **$30**.
- Paired strong/cheap development and calibration calls: **$120**.
- Locked test evaluation, including paid counterfactual baselines: **$270**.
- One targeted ablation/live routing check: **$60**.
- Reserved reruns/contingency: **$120**.

Each $200 account can use the same proportional envelope: $10 / $40 / $90 / $20 / $40. Assign disjoint task IDs per account, balanced by repository, and run every condition for a task in the same account where possible. Do not confound model condition with account or execution machine. Shared artifacts contain outcomes and manifests, never API keys.

### Proposed Tinker allocation — $750, conditional on E2

- Compatibility and pricing probe: **$25**.
- Dataset/tokenization and untuned-router pilot: **$75**.
- One supervised router-training run: **$200**.
- Calibration and comparison: **$150**.
- One scientifically justified replication: **$150**.
- Reserve: **$150**.

These are team-level envelopes. Before E2, distribute each run to an account whose remaining $250 allocation can cover it, including inference/storage. Do not start a job that requires balances from multiple accounts. Reuse a checkpoint only through supported access/export mechanisms [S5, S6]. If the account split makes replication impractical, reduce scope instead of duplicating work blindly.

### Spend gates

Estimate phase cost from actual development usage: `tasks × (mean strong run + mean cheap run + all router requests)`, plus planned retries, evaluation infrastructure, and contingency. Use p90 development task costs as a sensitivity check. Gate later phases on the measured forecast, remaining account balances, and report deadline.

Every job needs a run/task token cap, time/step cap, bounded retry count, concurrency cap, account ID, phase dollar cap, and resumable run IDs. Enforce the phase cap conservatively using completed cost plus reserved cost for in-flight requests. Stop when the forecast would exceed the cap; do not launch speculative full-benchmark runs. Rate limits are constraints, not reasons to rotate accounts invisibly.

Jev is currently documented on OpenRouter, billed to the same OpenRouter account [S2]. Tinker prices are per-token and include separate sampling/training rates plus checkpoint storage [S5]. Capture actual provider invoices/usage and a dated price snapshot. Free credits reduce cash outlay; they do not make deployed inference economically free. Local Kev compute is not zero-cost either. Docker hosting/GPU costs may require a separate plan.

## 7. Work queue and milestone schedule

**Immediate milestone:** working prototype by Wednesday, November 4 as the team's target; midpoint recorded video and 3–4 page ICLR-format report submitted by Friday, November 6 at 11:59 p.m. Pacific according to the published course deadline table [S10]. Follow the concrete M1–M4 sequence in [MIDPOINT_CHECKLIST.md](MIDPOINT_CHECKLIST.md). This is a prototype milestone, not a requirement to finish the study overnight.

**Final milestone:** live demo Wednesday, December 9, 3:30–6:30 p.m. Pacific. The public final report window is December 7–11 with the exact cutoff TBA [S10]. Keep the full reproducible package ready by December 6 and verify the instructor's final cutoff before submitting. The calendar gives about five weeks from this planning date; do not compress it based on an approximate week count.

Suggested calendar after the midpoint: November 7–13 for P2/P3 and paired development; November 14–20 for P4/P5 and protocol lock; November 21–29 for P6, allowing for Thanksgiving availability; November 30–December 6 for P8/reproduction. P7 may proceed only if it preserves the November 30 analysis/report start. The week labels below refer to these post-midpoint work blocks, not course week numbers.

### P0 — Repository publication; now

Dependency: verified **ramimrad** browser access, now available; the connector still returns 404. The repository has a starter README and `.gitignore` on `main`. Publish the planning bundle, preserving existing ignore rules; do not initialize it again. Exit: committed files/PR visible to teammates and README publication status updated. Recheck for concurrent edits before replacing the starter README.

### P1 — Team and resource decisions; first working day

Suggested owner: all three. Record the known milestone dates, confirm the exact final report cutoff, owners, machine/containers, credit expiry, available balances, and primary coding scope. Exit: short decision record with named owners, dates, account assignments, and an agreed experiment envelope. This is project coordination, not a need to repeat approval for routine implementation.

### P2 — Unmodified harness smoke; week 1

Suggested owner A, reviewed by C. Pin OpenCode and runtime; verify accessible strong/cheap model IDs and tool behavior; run two development tasks through the official evaluator; verify nonzero cost capture against provider usage. Exit: exact setup commands, two task traces per model, evaluator results, pinned config, and an actual cost forecast. If Docker is unavailable, resolve the execution environment before collecting unscorable model outputs.

### P3 — Reproducible runner/data; week 1, after P2 interface stabilizes

Suggested owner B for manifests/evaluation, A for run/resume tooling. Freeze development partitions and held-out task-selection rules; implement independent evaluator integration, immutable manifests, artifact storage, deduplication/resume, and usage ledgers. Exit: a colleague can reproduce a smoke result from a clean checkout, and interrupted runs resume without duplicate successful tasks or erased failures.

### P4 — Jev probe and paired development; week 2

Suggested owner C, with A running paired baselines. Implement one gate question, explicit strong fallback, raw score retention, and one model-selection point. Do shadow runs before live routing. Exit: cheap/strong development outcomes, gate scores, costs, and a concise feasibility finding. Compare the deterministic heuristic before expanding the gate.

### P5 — Calibration/protocol lock; end of week 2

Suggested owner B; all three review. Select score/calibration/threshold and controls from development data; assess uncertainty; compute affordable test count; freeze model/provider/config/task manifest and analysis rules. Exit: signed-off protocol record and immutable manifest hashes, with empirical versus statistically supported risk claims distinguished.

### P6 — Locked evaluation and analysis; week 3

All three run disjoint task shards under one protocol; B combines analysis. Track spend and run status centrally. Exit: complete declared task-condition outcomes, raw artifact links/checksums, paired intervals, plots, random/heuristic controls, live routed validation, and an error audit. Any protocol amendment is versioned and cannot replace the original result silently.

### P7 — Optional training/transfer; only after primary development works

Suggested owner C, reviewed by B. Use training/development evidence to choose at most one E2 extension and freeze its data/model choices before final outcomes. This can run alongside P6 only if it does not use P6 labels and does not delay P8. Exit: untuned versus trained/alternative comparison with full training cost and artifact provenance, or a recorded decision to skip. Skipping does not block completion.

### P8 — Report, demo, and reproduction; final week

All three. Deliver an **8-page ICLR-format paper** with Introduction, Related Work, Environment & Data, Methods, Results, Discussion/Conclusion, Safety & Ethical Considerations, Authorship Statement, References, and AI-Use Disclosure. Place the disclosure after the authorship statement, and verify current template/page-limit rules [S11]. Results carry 10 report points, Methods 5, and reproducibility a separate 5, so prioritize evaluation and a working quick start over optional models. Track actual contributions for the authorship statement.

Address coding-agent sandbox boundaries, allowed tool actions, prompt injection from repository/issue content, credential protection, data/model licensing, dataset contamination, and compute costs in the required safety section. These are report/evaluation topics, not reasons to delay the prototype with unrelated infrastructure.

Verify every reference and number, explain the scope change from the proposal, and include an accurate AI-use disclosure. Rehearse a real live system demonstration for December 9, with archived traces as backup. Show a cheap-routed and a strong-routed task when the measured system supports them; do not force outcomes or present a replay as live. Exit: report and figures regenerate from archived outputs; a classmate can follow the README for installation, API configuration, one task, and evaluation reproduction; final README identifies completed tasks, unfinished limitations, artifact locations, costs, and follow-up work.

## 8. Run records and handoff contract

Every experiment manifest must record: run ID, task ID, split, owner/account label, code commit, harness version, container/base repository revision, model/provider/checkpoint ID, prompt/config hash, temperature/seed where supported, limits, route score/decision/threshold, timing, usage/cost including failed calls, evaluator result, retry history, artifact URI/checksum, and completion status. Distinguish missing outcomes from failure and from intentionally unrun conditions.

Use branch-per-task work with small PRs. Claim ownership in the README; inspect current branch state and manifests before resuming. Do not rerun completed experiments simply because local raw files are missing; fetch the recorded artifacts first. Teammates review another workstream's evaluator/config changes before a protocol lock.

Every work session must leave the README with evidence-backed completed work, remaining tasks/dependencies, active claims/branches, checks and outcomes, run IDs/checkpoints and accessible artifact pointers, cost status, blockers, and one next action. A final reproduction command must refer to actual implemented scripts. Until those exist, label commands as planned.

## 9. Completion criteria

- One well-defined, small intervention in an existing harness, with a strong/cheap reference and matched-coverage random/heuristic controls.
- A frozen, test-independent protocol and an independently scored coding dataset.
- End-to-end cost/performance results with uncertainty, calibration/risk analysis, and honest failure cases.
- A reproducible artifact trail and verified setup/evaluation/figure commands.
- A recorded midpoint demo and 3–4 page midway report; an 8-page formal final report, live final demo, required safety/authorship/AI-use sections, and verified citations.
- A current README that lets any teammate's coding agent resume without reconstructing history.

Sources [S1]–[S11] and important qualifications are in [SOURCES.md](SOURCES.md).
