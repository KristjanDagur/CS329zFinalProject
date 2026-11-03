# CS329Z Final Project

**Working title: Can System One routing reduce the cost of a coding agent?**

Team: Kristjan Dagur Egilsson, Ómar Ingi Halldórsson, and Rami Ratl Mrad.

We will test whether a small decision model can select when a cheaper coding model is sufficient, using one existing OpenCode harness. The main comparison is task success versus total cost against the same harness running a strong model on every task. The first experiment changes only model selection at task launch. It does not require a new agent architecture.

This is the proposed execution plan, informed by the submitted proposal and instructor feedback. Experimental choices below become final when recorded in a frozen experiment manifest. No empirical results exist yet.

## Start here

1. Read this status report and [the end-to-end plan](docs/PROJECT_PLAN.md).
2. Read [AGENTS.md](AGENTS.md) before using a coding agent.
3. Claim one task in the work queue below; record your name, branch, and date before starting.
4. Check dependencies and existing run manifests before implementing or running anything.
5. Update this README in every work PR and before handing work to another person or agent.

## Status report

Last updated: **2026-11-03, America/Los_Angeles**.

**Current stage:** planning published on `main` through the verified **ramimrad** browser session. Implementation and experiments have not started.

### Completed

- [x] Read the three-page proposal PDF, including the instructor feedback and both proposal pages.
- [x] Translate feedback into a linear sequence: existing harness, small intervention, strong baseline, cost/performance evaluation, then optional training.
- [x] Define the first experiment, baseline comparisons, data separation, evaluation metrics, budget gates, three-person workstreams, and final deliverables.
- [x] Check current primary documentation for OpenCode, Jev/OpenRouter, Kev, Tinker, and benchmark options; record sources and qualifications.
- [x] Publish this README, the detailed plan, midpoint checklist, source notes, agent handoff instructions, and a PR checklist on `main`. Preserve the starter `.env`/`.venv` ignore rules and extend them for experiment artifacts.

### Remaining work in dependency order

- [x] P0: Verify repository contents and the **ramimrad** identity; publish the planning files on `main`.
- [ ] M1–M4: Deliver the midpoint prototype, recording, runnable README, and 3–4 page report; see [the midpoint checklist](docs/MIDPOINT_CHECKLIST.md).
- [ ] P1: Confirm the exact final report cutoff, credit availability/expiry, execution machine, and workstream owners.
- [ ] P2: Freeze harness/model/provider revisions and run two unmodified baseline smoke tasks.
- [ ] P3: Build the task manifest, evaluation runner, raw trace logging, and cost accounting.
- [ ] P4: Run paired strong/cheap baselines on development tasks; test one Jev routing decision per task.
- [ ] P5: Fit calibration and select a threshold using development data only; freeze the primary protocol.
- [ ] P6: Run the locked evaluation, matched-coverage controls, uncertainty analysis, and error review.
- [ ] P7: If justified by development evidence and time, run ONE Tinker router-training extension.
- [ ] P8: Produce report, reproducible figures, demo, clean-checkout reproduction instructions, and final handoff.

### Active work and claims

No implementation tasks are claimed. Suggested workstream allocation, **not yet assigned**:

- **A / harness and runs:** proposed lead Kristjan; tasks P2 and harness portion of P3.
- **B / evaluation and analysis:** proposed lead Ómar; task/data portion of P3, then P5/P6.
- **C / decision models and integration:** proposed lead Rami; P4 and optional P7.
- All three: P1, protocol review, error analysis, final report, and P8.

Dependencies and acceptance criteria are in [the plan](docs/PROJECT_PLAN.md#7-work-queue-and-milestone-schedule). Claim format: `task ID | owner | branch | started date | expected artifact | dependency`.

### Blockers and unresolved decisions

- The Cal connector for **ramimrad** returns 404, but browser access now works as **ramimrad**. The private repository's `main` branch has a starter README and `.gitignore`; there is no implementation yet. Planning publication succeeded through the browser; future work may use that verified session while connector access is unresolved.
- Prototype-ready target: **Wednesday, November 4** per the team's request. The published course deadline for both midpoint submissions is **Friday, November 6, 11:59 p.m. Pacific**. Final live demo: **December 9, 3:30–6:30 p.m. Pacific**; final report cutoff remains TBA during **December 7–11**. Follow any newer instructor announcement.
- Model IDs, prices, provider routing, usable balances/expiry, and Docker/compute availability must be verified during P1/P2. The credits are user-reported allocations, not verified balances.
- The instructor suggests coding-harness experiments while the original proposal names intent datasets. The proposed primary track follows the instructor's coding focus; intent experiments are optional transfer diagnostics. Record a team decision before implementing a different primary scope.

### Validation and results

- Validation so far: proposal text extraction plus visual inspection of all three pages; primary documentation/course deadline review; local documentation link/content checks and archive integrity checks; browser verification of repository contents and the **ramimrad** identity.
- No implementation, installations, model API calls, training, benchmark runs, or compute purchases have been performed.
- No task success, calibration, risk, cost savings, or latency results have been measured.
- No credits have been spent by this planning session. There are no run IDs, checkpoints, or experiment artifacts to resume.
- The shared repository has been updated with planning and handoff documentation on `main`; no executable prototype exists yet.

### Exact next action

Claim M1–M4 in [the midpoint checklist](docs/MIDPOINT_CHECKLIST.md) and agree on the model pair/task execution interface. Start M1 with one unmodified OpenCode run per model; build the real routing prototype for November 4, then the recorded video/report for November 6. Full benchmark infrastructure and training follow the midpoint.

## Budget envelope

User-reported allocation: **3 × $250 = $750 Tinker**, and **3 × $200 = $600 OpenRouter**; total face value **$1,350**. These are separate service balances in three accounts, not one transferable pool.

- OpenRouter proposed caps: $30 access/smoke, $120 paired development runs, $270 locked evaluation, $60 targeted ablations, $120 reserve.
- Tinker proposed caps: $25 compatibility probe, $75 dataset/base-router pilot, $200 one SFT run, $150 evaluation/comparison, $150 conditional replication, $150 reserve.
- Caps are planning envelopes, not a commitment to spend. Reserve stays unallocated until a failed run or a specific scientific need justifies it. Each account owner retains control of their credentials and ledger.
- Start small, measure actual per-task cost, and reduce the task count before exceeding a cap. See [budget and accounting](docs/PROJECT_PLAN.md#6-credits-and-cost-controls).

## Handoff log

### 2026-11-03 — Initial planning

- Done: reviewed proposal/feedback; published the plan, midpoint checklist, source notes, README, agent instructions, PR checklist, and extended ignore rules on `main` as **ramimrad**.
- Evidence: [source notes](docs/SOURCES.md); no experiment artifacts exist.
- Left: midpoint tasks M1–M4, environment setup, and implementation/evaluation tasks P1–P8.
- Access: browser verified as **ramimrad** after user sign-in; connector access remains unresolved. Course milestones incorporated. Publication commits are listed in [repository history](https://github.com/KristjanDagur/CS329zFinalProject/commits/main); the setup concludes with commit message `docs: publish README status and agent handoff rules`.
- Resume: follow “Exact next action” above. Do not repeat proposal review or start with custom harness development/training.

## Updating the status

Keep the current state accurate, then append a short dated handoff entry. Include completed tasks and evidence, work in progress and owner/branch, remaining tasks and dependencies, commands/checks with outcomes, experiment IDs and artifact locations, spend and remaining balances if known, blockers, and one exact next action. Mark incomplete/failed/abandoned runs explicitly. A document or code change is not a successful experiment. A local draft is not a published repository change.
