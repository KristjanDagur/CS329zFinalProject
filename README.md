> **Active claim — November 6, 2026:** `SWE-bench Verified extension (verified-explore-v1) | Kristjan with Claude | kristjan | 2026-11-06 | dependency: frozen v1 method, Docker, swebench 5.0.2 | artifact: verified_protocol.json, verified_sample.json, verified_probe.py, 30-run pilot (10 tasks × 3 conditions)`. Agreed with Rami. Status: code drafted and offline-tested; **no Docker check, smoke run or paid run yet**. See the handoff entry below.

> **Integration handoff — November 6, 2026:** Rami authorized merging this implementation into `main`. Keep `rami` for subsequent development. The real-bug pilot is complete: 15 runs, preserved receipts/failures, four-page report draft, and passing offline checks. Remaining: teammate reproduction and report review; video work is deferred. No additional paid experiments are needed for this merge.

# CS329Z Final Project — Rami’s coding experiment

Team: Kristjan Dagur Egilsson, Ómar Ingi Halldórsson, and Rami Ratl Mrad.

**Active branch: `rami`. All further work by Rami’s coding agent stays here.**

The instructor advised starting with a small substitution in an existing coding harness and measuring its cost/performance before redesigning the agent. Our chosen experiment replaces OpenCode’s native `explore` subagent with Jev selecting relevant source files. OpenCode still delegates, reads, edits, and runs tests; the same strong coding model writes every patch. Choosing exploration and this benchmark is our design decision, not a specific prescription from the instructor.

**Current status (November 6):** the corrected 15-run experiment is complete on five authentic pydicom bugs from SWE-bench Lite’s official development split. These replace the invented fixtures as project evidence. The original synthetic outer-router pilot is retained below as historical work; its report/video do not describe this corrected experiment.

## What Jev actually does

The build agent invokes OpenCode’s existing `task` tool with `subagent_type="explore"`. A thin provider adapter changes only that explorer’s response. It searches implementation files deterministically, gives Jev the top 12 candidates with original code snippets, asks 12 typed file-relevance questions, and returns the three selected paths/snippets. Jev’s probabilities directly determine which files are returned. Jev does not generate code. On an API/validation error, the normal explorer is used and both costs are counted.

We compare three conditions with identical issues, writer (`openai/gpt-6.1-sol`), tools, limits and evaluator:

- `native`: OpenCode’s normal generative explorer, using the strong model.
- `jev`: deterministic retrieval plus `typesafe/jev-1.14` file selection at the internal explorer boundary.
- `search`: the same retrieval, returning its top three files without Jev. This tests whether Jev adds value over search alone.

The native explorer can search the whole repository; the replacement receives bounded candidates. This is a component substitution study, not a claim that Jev can replace every exploration behavior. See [the current plan](docs/PROJECT_PLAN.md) and [the frozen protocol](coding_protocol.json).

## Run the real-bug prototype

Check out **`rami`** in your own clone. Required: Git, [uv](https://docs.astral.sh/uv/), an OpenRouter key in `.env`, and the OpenCode binary. The team's reference machine is Arch Linux x86_64 with system Python 3.14; the orchestrator scripts are standard-library only and run on the system `python3` (verified on 3.14 and 3.12). The evaluator venv must be Python 3.12, which uv downloads automatically; [requirements.txt](requirements.txt) pins its exact packages. The existing `bootstrap.py` installs the pinned OpenCode 1.19.5 **runtime being evaluated**; your Claude/GPT coding assistant is separate and needs no repository bootstrap.

```bash
git switch rami
python3 bootstrap.py
uv venv --python 3.12 .runtime/coding-venv
uv pip install --python .runtime/coding-venv/bin/python -r requirements.txt
python3 coding_probe.py prepare
python3 coding_probe.py check
python3 -m unittest -v test_coding_probe.py
```

`prepare` downloads official task metadata and exact upstream repository commits into `.runtime/coding/`. `check` applies the benchmark-owned added tests in separate evaluator copies and verifies the broken base fails and upstream fix passes. None of those gold assets is copied into the agent’s workspace. All five environments passed locally (41, 23, 304, 27 and 5 selected/expanded regression cases). Historical tests need pytest 7’s nose-style setup support. Three malformed parameter IDs in task 1413 expand to their whole test functions rather than dropping regressions.

Put your key in a project-root `.env` file (gitignored) as `OPENROUTER_API_KEY=...`; the scripts read it from there automatically. A shell variable with the same name, if set, takes precedence (useful for CI). The key is never exported to `os.environ`, so OpenCode and task tests cannot inherit it. Then verify models/prices and launch a fresh run. Never commit `.env` or paste your key into a committed command.

Do not install `requirements.txt` into Python 3.13+: `numpy==1.26.4` has no wheels there, and newer numpy/pytest break the historical pydicom tests. Changing those pins changes the evaluator and requires a new protocol version.

```bash
python3 coding_probe.py snapshot
python3 coding_probe.py run --task pydicom__pydicom-1256 --condition native --run-id teammate-1256-native-01
python3 coding_probe.py run --task pydicom__pydicom-1256 --condition jev --run-id teammate-1256-jev-01
python3 coding_probe.py run --task pydicom__pydicom-1256 --condition search --run-id teammate-1256-search-01
```

Outputs are in `runs/coding/<run-id>/`: `manifest.json`, `events.jsonl`, actual model requests/responses and usage receipts, `localization-0.json` (Jev/search only), `patch.diff`, `evaluation.json`, and `result.json`. Existing completed run IDs resume without another API call only when source/protocol/task/condition match; incomplete runs require inspection and a new ID. Never delete paid failures to rerun silently.

The shared ledger caps this pilot at **$15 total**, **$2/run**, 32 requests, 4,096 output tokens/request and 480 seconds/run. It retains unresolved reservations. Use different IDs for teammate reproduction while sharing your local ledger. The credit allocations are three separate $200 OpenRouter and three separate $250 Tinker accounts; credits are not assumed transferable.

## Results and artifacts

All three conditions solved the **same 2/5 real development issues** (1256 and 1694). Mean total cost per issue was **$0.110382 native**, **$0.072762 Jev**, and **$0.062014 search-only**; mean agent wall time was 37.64, 25.93, and 24.90 seconds respectively. Jev replaced **23 native explorer generation calls with five actual decision calls**, with no fallback. Its direct decision bill was $0.001097208; total repair cost includes the writer and auxiliary calls.

Jev cost 34.1% less than the native explorer in this pilot, but **search-only was cheaper still with the same observed success**. We have not established added value over retrieval, performance equivalence, calibration, or a 5% accepted-error guarantee. Writer trajectories differ, so the Jev-versus-search bill difference is not all direct Jev overhead.

- [Frozen evidence JSON](coding_evidence.json): exact 15 run IDs, source/data/archive hashes, paired issue outcomes, component counts/costs and limitations.
- [Raw evidence archive](coding_runs.zip): actual requests/responses, Jev scores/selections, OpenCode traces, patches, test logs, environment controls, exact experiment source and upstream license. It excludes repository working copies and credentials.
- [Corrected four-page midway report draft](report/coding_midpoint.pdf), [LaTeX source](report/coding_midpoint.tex), and its [LaTeX results source](report/coding_results.tex). These supersede the old synthetic report/video for this branch.

Recompute the **frozen** comparison offline from the archive, without models, dependencies or another paid run:

```bash
python3 build_coding_report.py
```

This selects only the 15 declared primary IDs; teammate/demo runs cannot silently enter the published results. With LaTeX installed, `python3 build_coding_report.py --compile` rebuilds the report PDF. `coding_probe.py summarize` is only a generic summary of all local runs, not the frozen analysis.

## Status and handoff

- **Done / owner:** Rami’s coding agent on `rami`; official development IDs/base commits frozen before outcomes; all five broken-base/gold-fix controls validated; native baseline followed by Jev and search-only runs; all 15 results and billed receipts preserved; corrected four-page report drafted and visually checked; runnable commands provided. Video work is deferred at the user’s request.
- **Verified:** 11 existing plus four new offline checks pass; all 15 primary runs share source hash `5d106f20e205e4101bab9b46ce421c7c9620457ec131ecb1018c3a459e7b96c6`; every bill settled; Jev exercised on all five tasks with no fallback; all unsuccessful repairs remain in the denominator. The evidence builder validates hashes, expected IDs, controls and receipt totals before producing results. CI now runs the four new checks and offline evidence reconstruction alongside the existing checks.
- **Remaining for midpoint:** independent teammate reproduction; review of report/AI disclosure; verify course graders can access the private repository; submit report/video/repository link in the portal. Video work is deferred at the user’s request. The old `demo_replay.mp4` is historical and does not show this corrected system.
- **Remaining for final:** reproduce with the official Docker evaluator on suitable compute; broaden repositories and development tasks; investigate file selection and parent recovery; compare a generative ranker on identical candidates; freeze independent evaluation; report uncertainty/failure analysis and prepare final paper/live demo. Do not tune on final outcomes.
- **Deferred direction 1:** original BANKING77/CLINC150 intent decisions with tool-using escalation remain a later option. The user chose the coding-harness experiment first.
- **Spend / jobs:** corrected pilot **$1.225791308 OpenRouter**; historical synthetic pilot $0.126075004; combined recorded project total **$1.351866312**. **$0 Tinker**, no training/checkpoints, no active paid jobs. These are recorded project expenses, not account-wide usage. The last key allowance snapshot before this pilot was $195.809830466; other account activity may affect it.
- **Exact next action:** a teammate follows the setup above, runs `python3 build_coding_report.py` offline, then launches one fresh Jev run on task 1256 with a unique ID and checks its decision receipt, patch and 23 benchmark regression cases. Review the report against the actual results. Video work is deferred at the user’s request.

### November 6 handoff — shared 20-task comparison, unrestricted arm (Kristjan with Claude, `kristjan`)

- Plan agreed in the team: on the same 20 SWE-bench Verified tasks, Kristjan runs the writer exactly as in the pilot (read/grep/glob allowed) and a teammate runs a restricted writer without those tools. The teammate's arm needs its own protocol version, its own OpenRouter key/ledger, and the same commit otherwise.
- `verified_sample.json` gains `shared_subset_20`, drawn by the same rule (re-fetched index verified against the recorded `index_sha256`): django 9, sympy 3, sphinx 2, and one each from astropy, matplotlib, pylint, pytest, scikit-learn, xarray. It contains the 10 pilot tasks and is contained in the 50-task sample.
- Added `verified_protocol_v2.json` (`verified-explore-v2`): identical to v1 except the task list and a $15 experiment cap on the shared ledger. `verified_probe.py` now selects a protocol with `VERIFIED_PROTOCOL=...` (default remains the frozen pilot file, which is unchanged) and hashes the selected file. 28 offline tests pass.
- Started: `VERIFIED_PROTOCOL=verified_protocol_v2.json` prepare → check → `batch --prefix v20` (60 runs, images kept on disk), log `runs/verified/v20-batch.log`. Results pending.

### November 6 handoff — SWE-bench Verified extension drafted (Kristjan with Claude, `kristjan`)

- Decisions (Kristjan, agreed with Rami): move from five pydicom Lite dev tasks to SWE-bench Verified, keep the v1 method unchanged, let the agent run tests inside each task's official image (option b), and start with a **10-task pilot × 3 conditions = 30 runs**. Reason: Verified's human screening removes vague issues and tests that check behaviour the issue never requested.
- Added `verified_sample.json`: 50 tasks from Verified revision `78f471b…`, stratified by repository with a recorded hash ordering, plus a nested 10-task pilot subset (django 5, sympy 2, matplotlib 1, scikit-learn 1, sphinx 1). Selected from instance IDs and repository names only, before any run.
- Added `verified_protocol.json` (status: draft until the checks below pass), `verified_probe.py`, `test_verified_probe.py`, `requirements-swebench.txt`; CI now runs the new tests. `coding_probe.py` and `coding_protocol.json` are unchanged; `verified_probe.py` imports v1's proxy/Jev code and refuses to run if any shared method setting differs from v1.
- Agent testing: one container per run from the task image; setup runs online, then the network is disconnected and upstream git history is replaced by one fresh commit. `run_tests <targets>` applies the workspace diff to a clean `/testbed` and runs the repository's standard runner; targets are validated and quoted. The benchmark's own test targets, `test_patch` and gold patch never reach the agent. Grading uses the official `swebench` 5.0.2 harness; it has no `--cache_level`, so `batch --remove-images` deletes each task's image after its three runs.
- Verified: 25 offline tests pass on Python 3.14 and 3.12, including v1-identical retrieval and leakage boundaries; runner prefix and setup parsing checked against all 10 real eval scripts (no test targets or test bodies in the agent-side commands). `swebench` 5.0.2 installed in `.runtime/swebench-venv`; 10 pinned rows in `.runtime/verified/tasks.json`.
- `python3 verified_probe.py check` passed for all 10 tasks (after a fix, below): every image is the base commit plus one SWE-bench setup commit with no later upstream history; that commit is empty or permission-only except sphinx-8056 (dependency pins in `setup.py`/`tox.ini`), and none touches source or tests; test_patch and gold patch are absent from every image; all 10 gold patches resolve under the official harness. Images total 32.2 GB on disk (shared layers); 124 GB free afterwards.
- Fix during check: the first version required image HEAD == base commit and failed all 10 tasks; it now accepts base == HEAD or HEAD^ provided the setup commit changes no content under source roots or tests (blob comparison, since permission-only changes on binary files look like edits in `--numstat`). New offline test added; 26 pass.
- Smoke run `vsmoke-django-12050-jev-01` failed before any model call ($0): `data_receipt.json` was missing because the task rows had been fetched ad hoc instead of with `prepare`. Preserved with `setup_failure.json`. Fixed by running `prepare` (rows identical to those used by `check`) and by making `run()` read all inputs before creating a container or run directory.
- Smoke run `vsmoke-django-12050-jev-02` **resolved** under the official harness: one-line fix in `django/db/models/sql/query.py`, 1 Jev call (no fallback), 1 `run_tests` call, 8 requests, **$0.0407**, 19.1 s agent time. Retrieval over Django took 0.21 s; largest request 53,633 of 196,608 bytes; container setup succeeded, network was disconnected and the container removed.
- Fix after the smoke run: `run_tests` output kept only the last 12,000 characters, and Django's buffered stdout was flushed last, so the test summary was cut off. Commands now run with `PYTHONUNBUFFERED=1`. Verified free against a real container: output ends with `Ran 508 tests … OK`, an injected breaking edit propagates and fails, network is blocked. 27 offline tests pass. Protocol marked frozen.
- Spend: $0.040709422 OpenRouter on this protocol (`runs/verified/spend_ledger.jsonl`).
- **Pilot complete (30 runs, `vpilot-*`, single source hash `4a7e17cb6476…`):** all graded by the official harness, all costs settled, no timeouts, forbidden edits, fallbacks or incomplete runs. Resolved: **native 9/10, Jev 9/10, search 8/10**. Mean cost/task: **native $0.106, Jev $0.056, search $0.054**; mean agent time 42.9 s / 26.0 s / 25.3 s. Native used 48 explorer generation calls; Jev used 10 decision calls. Pilot spend $2.165 (protocol total $2.206 incl. smoke runs) of the $10 cap.
- Interpretation: Jev cost 48% less than native with the same observed success, but search-only matched Jev on cost and was within one task on success. The single search failure (django-15695) was not a retrieval failure: search returned the gold file and the writer edited it but placed the fix after an index lookup. The gold-modified file was in the returned top 3 for Jev 7/10 and search 6/10, yet the writer edited the gold file in all 30 runs. As in the pydicom pilot, the writer recovers localization itself; the saving comes from not running the generative explorer. Ten tasks with one rollout each support no equivalence or superiority claim.
- Note: `verified_probe.py summarize` counts every run directory, including the smoke run; use only `vpilot-*` results. `python3 build_verified_report.py` is the frozen analysis: it selects exactly the 30 declared pilot IDs, asserts one source hash and complete grading, and writes `verified_evidence.json` and `report/verified_results.tex`. It needs the local `runs/verified/` directory, which is not yet packaged into a portable archive (unlike `coding_runs.zip`).
- Report: `report/coding_midpoint.tex` revised with the Verified pilot as the main result and pydicom as the development pilot; compiled with `python3 build_coding_report.py --compile` to a 4-page PDF (3 body pages + references/AI disclosure), no LaTeX warnings. Needs team review before submission; the OpenAI "Introducing SWE-bench Verified" reference URL has not been re-checked.
- Next action: decide the next protocol version with the team: add a no-explorer control condition, and/or extend to the remaining 40 sampled tasks (~$8.6 projected from measured costs).

### November 6 handoff — Linux setup and `.env` key loading (Kristjan, `kristjan`)

- Agreed with Rami: the team standardizes on Kristjan's machine (Arch Linux, system Python 3.14 for the orchestrator; uv-managed Python 3.12 evaluator venv). Added `requirements.txt` (exact freeze of the verified venv, same pins as `coding_protocol.json`), switched setup docs to uv, and added Python 3.14 to the CI matrix. Teammates: install uv and recreate `.runtime/coding-venv` with the commands above.
- Changed: `midpoint.py` `key_from_environment()` now reads `OPENROUTER_API_KEY` from the project `.env` (shell variable overrides) without exporting it; new offline test in `test_midpoint.py`; this README. The experiment source hash (`coding_probe.py` + `coding_protocol.json`) is unchanged, so new runs remain comparable with the frozen 15.
- Verified on Arch Linux x86_64: `bootstrap.py` installs and runs OpenCode 1.19.5 (first Linux validation); Python 3.12.15 coding venv via `uv` with pinned deps; `python3 -m unittest test_midpoint.py test_coding_probe.py` — 16 pass on Python 3.14 and 3.12; `build_coding_report.py` reproduces the frozen evidence.
- Not yet verified on Linux: `coding_probe.py prepare`/`check` and a paid smoke run. No paid calls made; spend unchanged. `.env.example` comment still says "set in your shell" and needs a manual update.
- Next action: run `python3 coding_probe.py prepare && python3 coding_probe.py check`, then `python3 midpoint.py doctor`, then one Jev run on 1256 with run ID `kristjan-linux-1256-jev-01`.

### November 6 handoff

Changed files: `.github/workflows/offline.yml`, `coding_probe.py`, `coding_protocol.json`, `test_coding_probe.py`, `coding_runs.zip`, `coding_evidence.json`, `build_coding_report.py`, corrected report sources/PDF, this README, and `docs/PROJECT_PLAN.md`/`MIDPOINT_CHECKLIST.md`. Commands verified: prepare/check, all 15 bounded real-model runs, `python3 -m unittest -v test_midpoint.py test_coding_probe.py`, and offline evidence/report reconstruction. No test outcomes were used to alter the frozen retrieval settings, model pair, prompts or selection policy. Branch-local only; main and teammates’ branches were not edited.

Local pytest uses published `FAIL_TO_PASS`/`PASS_TO_PASS` tests, with broken/gold controls, on macOS/Python 3.12. **This is not the official Docker SWE-bench score.** Five convenience-selected development issues and one rollout each cannot establish statistical equivalence or generalize to all repositories. Tool permissions restrict benchmark writes; they are not an operating-system sandbox.

Sources: [SWE-bench Lite dataset](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite), [pinned OpenCode exploration tool](https://github.com/anomalyco/opencode/blob/v1.19.5/packages/opencode/src/tool/task.ts), [Jev typed decisions](https://openrouter.ai/docs/guides/community/jev).

---

<details>
<summary>Historical synthetic outer-router pilot and earlier handoff notes</summary>

# CS329Z Final Project

**Can System One routing reduce the cost of a coding agent?**

Team: Kristjan Dagur Egilsson, Ómar Ingi Halldórsson, and Rami Ratl Mrad.

The midpoint prototype is implemented and has completed real OpenRouter/OpenCode runs. Jev chooses the model for an existing OpenCode harness; a separate grader checks the resulting patch. This is a small synthetic development pilot, not a final benchmark result.

## Quick start

The implementation is on **`main`**, merged in [PR #1](https://github.com/KristjanDagur/CS329zFinalProject/pull/1). Clone via SSH using a GitHub account with repository access and a configured SSH key. The default checkout is `main`; no branch switch is needed. Artifact links below are pinned to the reviewed implementation commit.

```bash
git clone git@github.com:KristjanDagur/CS329zFinalProject.git
cd CS329zFinalProject
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

Last updated: **2026-11-05, America/Los_Angeles**.

**Current stage:** working midpoint prototype and submission drafts merged into `main` in PR #1 (merge commit `e0a4705`). Independent teammate reproduction, report/video review, final video choice, and course submission remain unrecorded. The SSH setup and branch instructions were corrected on November 5 in the documentation commit `updated the readme file`. Read [AGENTS.md](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/AGENTS.md) before modifying anything.

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

- [ ] Independently follow this README from `main` once and record the teammate reproduction result; PR #1 is already merged.
- [ ] Review the paper, references, author names/contributions, and AI-use disclosure; check current course submission rules.
- [ ] Confirm the course graders can access the private repo; choose/record the final demo video.
- [ ] Submit the video, report, and repo link through the course portal; nothing has been submitted automatically.
- [ ] P1: confirm the exact final report cutoff, team ownership, other account allowances/expiry, and execution machine.
- [ ] P2/P3 final-study extension: provision Docker/SWE-bench, freeze tasks/evaluator/provider revisions, obtain useful calibration data.
- [ ] P4–P6: heuristic/random controls, calibration, locked meaningful evaluation, uncertainty and failure analysis.
- [ ] P7 optional: Tinker training only if justified by enough data and development evidence.
- [ ] P8: final paper, safety/authorship statements, live demo, and final reproduction review.

### Active claims and handoff

`README setup correction | Codex for Kristjan | main | 2026-11-05 | dependency: merged prototype and current checkout | artifact: corrected README and discrepancy notes | completed; included in the documentation commit`.

`M1–M3 / M4 preparation | Rami with Codex | midpoint-prototype | 2026-11-03 | prototype, evidence, draft report/video | completed for review`.

No experiment is running and no teammate task has been assigned. Proposed future workstreams remain Kristjan/harness, Ómar/evaluation, Rami/routing; confirm the owners before claiming new work. Do not rerun the pilot or rebuild a harness from scratch. Fetch the archived artifacts first.

### Known limitations and obstacles

- The opening status in `docs/PROJECT_PLAN.md` still says no experiments have executed. Treat it as the November 3 planning snapshot; the recorded midpoint pilot and current status are documented here and in `midpoint_evidence.json`.
- No Docker is installed on the development machine. The current data is **synthetic-midpoint-v1**, not SWE-bench. The three sanity tasks have not been model-run.
- The first socket-bound attempt was blocked by the execution sandbox. A subsequent paid attempt had a directory/path-permission integration failure. Both are preserved; the failed paid attempt is excluded from the post-fix comparison and included in spending.
- The default threshold is uncalibrated and produced zero cheap coverage. Provider selection is not yet frozen for the final study; observed providers are recorded.
- The Cal GitHub connector still returns 404 for this private repo; browser publication is verified as **ramimrad**. Use proper GitHub authentication in your own checkout.
- Prototype target: November 4. Published midpoint report/video deadline: **November 6, 11:59 p.m. Pacific**. Final live demo: **December 9, 3:30–6:30 p.m. Pacific**; final report cutoff TBA during December 7–11. Follow newer course announcements.

### Exact next action

A teammate should clone `main` via SSH, run the quick start and one low-cost task with their own key, review the draft report/video, and record that review here. Then finalize and submit the midpoint package. The next research implementation step is the SWE-bench execution environment and a development set where cheap-model success varies.

## Budget envelope

User-reported allocations remain **$750 Tinker + $600 OpenRouter** across three separate accounts. This session used **$0.126075004 OpenRouter**, leaving **$29.873924996** of the proposed $30 team midpoint-smoke envelope. Other balances/expiry and transferability are unverified. Keep account/service ledgers separate; do not share keys. The final-study allocations and spend gates remain in [the plan](https://github.com/KristjanDagur/CS329zFinalProject/blob/6b084a23639c645d0f856aaa5d5f3e364f2ae58e/docs/PROJECT_PLAN.md#6-credits-and-cost-controls).

## Handoff log

### 2026-11-05 — README setup correction

- Changed: `README.md` now uses the repository's SSH clone URL and the default `main` checkout. Removed obsolete branch-switch and pending-merge instructions; retained historical branch references. Included in the documentation commit `updated the readme file`, prepared for push to `origin/main` at Kristjan's request. Codex made this documentation edit for Kristjan.
- Verified: `git status --short` initially showed a clean checkout; `git branch -a` showed only local `main` and remote `origin/main`; `git remote -v` confirmed the SSH URL; `git log -3 --oneline` confirmed PR #1 was merged as `e0a4705`. Inspected tracked files and `midpoint_evidence.json`; the pinned artifact commit exists locally. `git diff --check` passed. No runtime tests were needed for this documentation-only change.
- Discrepancy: the project plan's opening status predates the recorded experiments; flagged above without changing the historical plan. No teammate reproduction or submission outcome was inferred from the merge.
- Runs/artifacts/budget: no experiments, downloads, or paid calls launched; existing run IDs, artifacts, and recorded balances are unchanged. No new checkpoint or run ID.
- Remaining/dependencies/blockers: teammate reproduction requires repository SSH access and an OpenRouter key for the paid task; report/video review and submission remain unrecorded. No blocker to this documentation correction; no active claim remains from this session.
- Next action: follow the quick start from `main` and record the reproduction result.

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

</details>
