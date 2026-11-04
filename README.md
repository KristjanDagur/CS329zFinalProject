# CS329Z Final Project

**Can System One routing reduce the cost of a coding agent?**

Team: Kristjan Dagur Egilsson, Ómar Ingi Halldórsson, and Rami Ratl Mrad.

The midpoint prototype is implemented and has completed real OpenRouter/OpenCode runs. Jev chooses the model for an existing OpenCode harness; a separate grader checks the resulting patch. This is a small synthetic development pilot, not a final benchmark result.

## Quick start

The implementation is on **`midpoint-prototype`** in [review PR #1](https://github.com/KristjanDagur/CS329zFinalProject/pull/1). Use that branch until it is merged. Artifact links below are pinned to the reviewed implementation commit, so they also work from the status-only `main` branch.

```bash
git clone https://github.com/KristjanDagur/CS329zFinalProject.git
cd CS329zFinalProject
git switch midpoint-prototype
python3 --version
python3 bootstrap.py
python3 -m unittest -v test_midpoint.py
python3 midpoint.py verify-fixtures
```

Python 3.11+ and Git are required. The prototype uses the Python standard library and a project-local, SHA-512-verified OpenCode **1.19.5** binary. The installer makes no global configuration changes. **macOS Apple Silicon is tested**; the installer supports macOS/Linux architectures, but Linux has not been validated. Windows is not supported by the current POSIX process/locking code.

Set your own OpenRouter key in the environment, then run one real task:

```bash
export OPENROUTER_API_KEY='your-openrouter-key'
python3 midpoint.py doctor
python3 midpoint.py run --task stable_unique --policy jev --run-id my-first-demo
```

The doctor command is read-only and reports the key's spending allowance, not the whole account balance. Do not commit your key. `.env.example` documents the variable; the CLI does not automatically load `.env` files. No Tinker key or credit is needed for the midpoint.

The default run has a **$0.50 task cap, $5 cumulative experiment cap, 180-second timeout, 8 agent steps, 10 API requests, 65,536 request bytes, and 2,048 output tokens/request**. Its output names the selected model, gate score, independent test result, cost, elapsed time, and artifact directory. Real runs require outbound OpenRouter access and permission to bind a loopback metering server. OpenCode starts and executes trusted synthetic task code locally; its tool permissions are not an OS security sandbox for hostile repositories.

Use `--policy cheap` or `--policy strong` for unchanged-harness baselines. The provisional Jev threshold is **0.90**, with strong fallback on invalid/unavailable gate responses. `--threshold 0.75` reproduces the *separately labeled development demonstration* of a cheap route; it is not a calibrated production threshold. Three other fixtures are reserved and require `--allow-sanity` explicitly; do not use them casually for prompt/threshold tuning.

## Reproduce the saved pilot without paid calls

The supplied archive contains sanitized traces, manifests, request-cost receipts, patches, grader outcomes, the spending ledger, and failed setup attempts. Machine-local paths are replaced; its `archive_manifest.json` hashes the sanitized bytes. It contains no credential file or runtime cache.

```bash
python3 -m zipfile -e midpoint_runs.zip .
python3 pilot_analysis.py
```

This regenerates [midpoint_evidence.json](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/midpoint_evidence.json) from the nine declared primary run IDs. Failed integration attempts, the lower-threshold demonstration, and clean-source reproduction are retained and separately labeled. `python3 midpoint.py summarize` instead summarizes **all** completed runs, including the failed integration run and supplementary runs; do not use that unfiltered summary as the primary comparison.

Reusing an identical completed `--run-id` returns its saved result without another API call. Changed protocol/source settings under the same ID are rejected. Incomplete runs are preserved and require inspection before a new ID is used. Keep the same `--runs-dir` for a shared cumulative budget. Different run directories have separate ledgers; they are not an account-wide spending control.

## Measured midpoint result

Nine post-integration primary runs: the same **3 synthetic development tasks × 3 policies**, one rollout per task and policy. All nine passed. The independent graders contain 6, 7, and 8 tests for `stable_unique`, `chunked`, and `merge_intervals`.

- **Always cheap:** 3/3 successful; mean billed cost **$0.002593/task**; mean time **9.39 s**.
- **Always strong:** 3/3 successful; mean billed cost **$0.017650/task**; mean time **11.48 s**.
- **Jev at 0.90:** 3/3 successful; mean billed cost **$0.018397/task**; mean time **12.11 s**. Scores **0.79 / 0.59 / 0.58** routed every task strong. Cheap coverage is **0%**; selective risk is **undefined**.

The gate averaged **0.245 s**. These tasks do not establish routing value: the cheap baseline already solved all of them. The routed bill also varies with stochastic coding trajectories, so its entire difference from the strong baseline is not gate overhead. There is no calibrated 5% risk guarantee, noninferiority finding, or general savings claim.

A separate post-hoc 0.75-threshold run selected the cheap model and passed six tests. A fresh source copy installed the pinned binary, passed the 11 offline checks, and completed another real cheap-model repair. Those checks verify execution/reproduction mechanics, not additional independent benchmark tasks.

**Total session model spend: $0.126075004**, including the failed integration run and both supplementary checks. All request reservations are settled. The course key had a $200 spending limit with $196.06760495 remaining before this session; earlier usage is unrelated to this project work. This is key-limit information, not a verified team-wide credit balance. Tinker spend: **$0**.

## Midpoint report and demo

- [ICLR-format midway report draft](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/report/main.pdf): **3 body pages plus 1 page for references and AI-use disclosure**; source [report/main.tex](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/report/main.tex). It compiles and has been rendered for visual inspection. The draft requires team review before submission.
- [74-second silent execution replay](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/demo_replay.mp4) and [walkthrough/narration script](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/DEMO_SCRIPT.md). The video is explicitly labeled as a replay of real saved execution, not a live run or screen capture. Decide whether to submit it or record a live terminal walkthrough; check any portal video-length requirement.
- [Full project plan](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/docs/PROJECT_PLAN.md), [midpoint checklist](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/docs/MIDPOINT_CHECKLIST.md), and [source notes](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/docs/SOURCES.md).

Optional artifact rebuilds:

```bash
python3 build_report.py
python3 -m pip install -r requirements-demo.txt
python3 build_demo.py
```

The report needs a full TeX distribution with Times, Helvetica, and Courier fonts, or the included sources can be imported into Overleaf. The app's built-in LaTeX compiler also compiled them successfully. Video rebuilding needs the unpacked trace archive and the pinned optional media dependencies. Neither rebuild makes model calls. `python3 package_evidence.py` rebuilds the sanitized trace ZIP from local runs.

## Status report

Last updated: **2026-11-03, America/Los_Angeles**.

**Current stage:** working midpoint prototype and submission drafts prepared on `midpoint-prototype`; review, final video choice, and course submission remain. Read [AGENTS.md](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/AGENTS.md) before modifying anything.

### Completed

- [x] P0: proposal/feedback review, research plan, milestone schedule, repository handoff conventions.
- [x] M1: pinned OpenCode install; real cheap/strong baselines; independent grader; tested quick-start path.
- [x] M2: real Jev gate, explicit fallback, actual upstream model verification, request-level cost metering and durable budgets.
- [x] M3 implementation: six frozen synthetic fixtures, reserved sanity split, paired development pilot, immutable artifacts, analysis script.
- [x] M3 draft: ICLR-format report with measured findings, limitations, references, and AI-use disclosure.
- [x] M4 preparation: clean-source agent reproduction, 74-second labeled replay, narration script, portable trace archive.
- [x] Validation: 11 offline checks pass; all six fixture starters rejected/references accepted; nine primary plus two supplementary real runs pass; credential scan and archive checks pass.
- [x] GitHub Actions offline checks passed on Ubuntu with Python 3.11 and 3.12; no model calls or API key are used in CI.

### Remaining work and dependencies

- [ ] Teammate review/merge of `midpoint-prototype`; independently follow this README once and record the result.
- [ ] Review the paper, references, author names/contributions, and AI-use disclosure; check current course submission rules.
- [ ] Confirm the course graders can access the private repo; choose/record the final demo video.
- [ ] Submit the video, report, and repo link through the course portal; nothing has been submitted automatically.
- [ ] P1: confirm the exact final report cutoff, team ownership, other account allowances/expiry, and execution machine.
- [ ] P2/P3 final-study extension: provision Docker/SWE-bench, freeze tasks/evaluator/provider revisions, obtain useful calibration data.
- [ ] P4–P6: heuristic/random controls, calibration, locked meaningful evaluation, uncertainty and failure analysis.
- [ ] P7 optional: Tinker training only if justified by enough data and development evidence.
- [ ] P8: final paper, safety/authorship statements, live demo, and final reproduction review.

### Active claims and handoff

`M1–M3 / M4 preparation | Rami with Codex | midpoint-prototype | 2026-11-03 | prototype, evidence, draft report/video | completed for review`.

No experiment is running and no teammate task has been assigned. Proposed future workstreams remain Kristjan/harness, Ómar/evaluation, Rami/routing; confirm the owners before claiming new work. Do not rerun the pilot or rebuild a harness from scratch. Fetch the archived artifacts first.

### Known limitations and obstacles

- No Docker is installed on the development machine. The current data is **synthetic-midpoint-v1**, not SWE-bench. The three sanity tasks have not been model-run.
- The first socket-bound attempt was blocked by the execution sandbox. A subsequent paid attempt had a directory/path-permission integration failure. Both are preserved; the failed paid attempt is excluded from the post-fix comparison and included in spending.
- The default threshold is uncalibrated and produced zero cheap coverage. Provider selection is not yet frozen for the final study; observed providers are recorded.
- The Cal GitHub connector still returns 404 for this private repo; browser publication is verified as **ramimrad**. Use proper GitHub authentication in your own checkout.
- Prototype target: November 4. Published midpoint report/video deadline: **November 6, 11:59 p.m. Pacific**. Final live demo: **December 9, 3:30–6:30 p.m. Pacific**; final report cutoff TBA during December 7–11. Follow newer course announcements.

### Exact next action

A teammate should check out `midpoint-prototype`, run the quick start and one low-cost task with their own key, review the draft report/video, and record that review here. Then finalize and submit the midpoint package. The next research implementation step is the SWE-bench execution environment and a development set where cheap-model success varies.

## Budget envelope

User-reported allocations remain **$750 Tinker + $600 OpenRouter** across three separate accounts. This session used **$0.126075004 OpenRouter**, leaving **$29.873924996** of the proposed $30 team midpoint-smoke envelope. Other balances/expiry and transferability are unverified. Keep account/service ledgers separate; do not share keys. The final-study allocations and spend gates remain in [the plan](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/docs/PROJECT_PLAN.md#6-credits-and-cost-controls).

## Handoff log

### 2026-11-03 — Midpoint implementation and pilot

- Done: root CLI/fixtures/installer/tests, model-price snapshot, metering/ledger, nine-run paired pilot, separate cheap-route demonstration, clean-source reproduction, evidence analysis/archive, report source/PDF, and labeled video/script. Published for review in [PR #1](https://github.com/KristjanDagur/CS329zFinalProject/pull/1); offline CI passed on Python 3.11 and 3.12.
- Evidence: `midpoint_evidence.json`, `midpoint_runs.zip`, `report/main.pdf`, `demo_replay.mp4`. Primary source hash and every primary/supplementary/excluded run ID are in the evidence JSON.
- Checks: `python3 -m unittest -v test_midpoint.py` (11 pass), `python3 midpoint.py verify-fixtures` (six valid fixtures), actual model/tool/grader traces, identical primary source hashes, completed cost receipts, archive integrity/credential scan, and rendered report/video inspection.
- Spend: $0.126075004 OpenRouter; no Tinker training or spending. No active jobs/checkpoints.
- Left: teammate reproduction/review, final video choice, private-repo grader access, portal submission, and all final-study extensions above.
- Resume: follow “Exact next action.” Preserve failed runs and the uncalibrated-threshold finding; do not count supplementary runs as new benchmark tasks.

### 2026-11-03 — Initial planning

- Done: reviewed proposal/feedback; published the plan, midpoint checklist, source notes, README, agent instructions, PR checklist, and extended ignore rules on `main` as **ramimrad**.
- Evidence: [source notes](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/docs/SOURCES.md); no experiment artifacts exist.
- Left: midpoint tasks M1–M4, environment setup, and implementation/evaluation tasks P1–P8.
- Access: browser verified as **ramimrad** after user sign-in; connector access remains unresolved. Course milestones incorporated. Publication commits are listed in [repository history](https://github.com/KristjanDagur/CS329zFinalProject/commits/main); the setup concludes with commit message `docs: publish README status and agent handoff rules`.
- Resume: follow “Exact next action” above. Do not repeat proposal review or start with custom harness development/training.

## Updating the status

Update the current state and append a dated entry in every work PR and before handoff. Record completed work with evidence, active owners/branches, remaining dependencies, checks and outcomes, run/checkpoint/artifact locations, spend, blockers, and one exact next action. Distinguish implementation from experiments, local from published files, draft artifacts from submissions, and empirical estimates from guarantees.
