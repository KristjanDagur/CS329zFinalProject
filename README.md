# Rami’s BANKING77 experiment — November 12, 2026

Owner: Rami with Codex. Branch: `rami`; draft PR #3. Main synchronized and preserved. User authorized the full experiment with bounded parallel collection and a $120 total OpenRouter ceiling; no Tinker training.

Implemented `intent_probe.py`, `intent_native.py`, `intent_tools.js`, `intent_protocol.json`, and seven offline checks. Native OpenCode 1.19.5 runs two isolated server workers with fresh sessions (up to 12 concurrent agent sessions). Persistent workers reduced a 30-example baseline batch from 296 seconds to 29 seconds. An additional 30 examples confirmed bounded parallel collection; 60 paired development examples are retained. The full Jev development set (1,500) and independent certification set (1,464) are complete, with no API failures in those final collections.

**Certification finding:** development selected max-probability threshold 0.96 (882/1,500 accepted; 25 errors). On independent certification it accepted 872/1,464 with 34 errors; the one-sided 95% binomial upper bound is **5.157%**, so the proposed 5% target **failed certification**. The certified fallback has zero Jev coverage and always escalates. Keep the fixed 0.96 candidate as an **uncertified** comparison; do not retune on certification or test. See `intent_analysis_plan.json` for the pre-test continuation amendment.

**Frozen next stage:** all 3,080 official test examples, one Jev, one direct strong, and one native retrieval-agent trajectory each; routed policies reuse the paired trajectories. Development costs project $36.10 total final collection ($45.12 with 25% margin). Spending before test: $1.822 confirmed plus $0.156 conservatively reserved for four prototype transport failures; initial course-key balance $186.657. Current code and frozen settings were published at commit `2ff59fc` before test queries. Full collection is now running locally under an exclusive collector lock; raw evidence will be packaged after collection. No final test analysis has been performed.

Data: official pinned BANKING77, about 1.08 MB; 7,039 support / 1,500 development / 1,464 certification / 3,080 test. Normalized duplicate groups stay together within training. Keep all official test rows; flag 16 normalized support/test overlaps and report a secondary nonoverlap metric. Source license: CC BY 4.0. Retrieval has support access only; no evaluator labels are sent to models.

**Exact next action while collection is active:** `python3 intent_probe.py status` (no API calls). Do not launch a second collector. If the current process stops, resume with `python3 intent_probe.py collect --split test --limit 0 --workers 24`, with `OPENROUTER_API_KEY` loaded privately; completed results are skipped without paying again. Preserve all failures, the earlier development protocol, and the failed certification result. Then run the predeclared live development check, offline analysis, evidence packaging, and final README/report handoff. Teammates’ coding/Verified runners and frozen protocols are unchanged (Git blob hashes checked against main). The existing 27 checks plus 10 new intent/analysis checks pass; CI also prepares the pinned 1 MB data and runs the new checks without model calls.


---

# CS329Z Final Project: Replacing Repository Exploration with Jev Decisions

Team: Kristjan Dagur Egilsson, Ómar Ingi Halldórsson, Rami Ratl Mrad.

We replace one component of an existing coding agent, the repository-exploration subagent of [OpenCode](https://github.com/anomalyco/opencode) 1.19.5, with deterministic file retrieval plus one typed **Jev** decision that picks the files to inspect, and measure repair success, cost and time on real SWE-bench issues. The same strong model (`openai/gpt-6.1-sol`) writes every patch. The midway report is [`report/coding_midpoint.pdf`](report/coding_midpoint.pdf).

## Results at a glance

| Experiment | Data | Finding |
|---|---|---|
| Development pilot (v1) | 5 pydicom issues, SWE-bench Lite dev | Native, Jev and search each fixed 2/5; Jev cheaper than native. |
| Extended development run (v2) | 41 pydicom issues, SWE-bench dev; native, Jev, search, **oracle** | Jev 35% faster (−16.3 s per issue, 95% CI −19.1 to −13.7) and 35% cheaper than native; success unchanged (18–21/41) in every condition, oracle included. |
| Verified pilot | 10 SWE-bench Verified tasks, official Docker grader | Native 9/10, Jev 9/10, search 8/10; Jev 48% cheaper than native; writer edited the gold file in all 30 runs. |
| File-selection study | All 225 SWE-bench dev issues, 6 repositories | Jev picks a gold file in its top 3 for 85.3% of issues vs 70.2% for search (+15.1 points, 95% CI 9.8–20.4). |
| Shortlist sweep | Same 225 issues, 24 and 48 candidates | 24 candidates: 90.2%, no latency tail; 48: 91.1% but 44/225 decisions take ~8 s. |
| LLM selectors | Same 225 issues and Jev's exact 12 candidates and questions | gpt-6-luna 85.8% (ties Jev) and GPT-6.1-Sol 88.0% (+2.7 points over Jev, 95% CI 0.4–5.3), but 5–6× slower per decision (1.5–1.8 s vs 0.29 s); Sol costs 58× as much. |
| Restricted writer (v3, option A) | 41 pydicom issues; writer may only read/edit the files chosen before launch, no grep/glob | Oracle 16/41 > Jev 14/41 > search 11/41; a wrong file choice is now nearly always fatal (0/5 Jev and 1/13 search runs passed after a miss); search runs 6.9 s slower than Jev. Directions as expected but not yet significant (Jev vs search 4 wins/1 loss, p = 0.38). |

Summary: replacing the generative explorer saves about a third of the time and cost without changing success, and Jev selects files better than search, about as well as a cheap LLM and nearly as well as a strong one, at a fraction of their latency. With free search tools the writer recovers from poor selections, so selection quality does not change outcomes; once the writer is restricted to the chosen files, it does (oracle > Jev > search), although 41 issues are not yet enough for significance.

## Repository map

| Path | What it is |
|---|---|
| `coding_probe.py` | Runner for the development experiments: `prepare`, `check`, `snapshot`, `run`, `batch`, `pack`. `--protocol FILE` selects v1 (default), v2 or v3. |
| `coding_protocol.json`, `coding_protocol_v2.json`, `coding_protocol_v3.json` | Frozen protocols (v1 pilot, v2 extended run with oracle and timing, v3 restricted writer). |
| `verified_probe.py`, `verified_protocol.json`, `verified_sample.json` | SWE-bench Verified runner (official Docker harness), protocol and frozen 50-task sample. |
| `localization_study.py`, `localization_protocol.json`, `localization_sweep_protocol.json`, `localization_llm_protocol.json` | Offline file-selection study, shortlist sweep and LLM-selector baselines. |
| `analyze_agent_runs.py` | Analysis of the v2 extended run. |
| `build_coding_report.py`, `build_verified_report.py` | Frozen analyses of the v1 and Verified pilots. |
| `*_evidence.json`, `*.zip` | Computed results and portable run archives (receipts, patches, test logs, traces). |
| `report/` | Midway report (`coding_midpoint.tex`) and generated result macros (`*_results.tex`). |
| `test_*.py` | Offline checks (27), run by CI. |

## Quick start

Requirements: Git, [uv](https://docs.astral.sh/uv/), an OpenRouter API key, macOS or Linux. The orchestration scripts use only the Python standard library; `uv` supplies Python 3.12 for them and for the evaluator environment.

```bash
git clone https://github.com/KristjanDagur/CS329zFinalProject.git && cd CS329zFinalProject
echo 'OPENROUTER_API_KEY=your-key-here' > .env            # gitignored; never commit it
uv run --no-project --python 3.12 python bootstrap.py      # pinned OpenCode 1.19.5, SHA-512 verified
uv venv --python 3.12 .runtime/coding-venv
uv pip install --python .runtime/coding-venv/bin/python -r requirements.txt
uv run --no-project --python 3.12 python -m unittest test_coding_probe.py test_midpoint.py test_verified_probe.py
```

**Run one task** (v1 protocol, pydicom issue 1256, Jev condition; about $0.05 and 30 s):

```bash
uv run --no-project --python 3.12 python coding_probe.py prepare     # task rows and upstream snapshots (free)
uv run --no-project --python 3.12 python coding_probe.py check       # broken base fails, upstream fix passes (free)
uv run --no-project --python 3.12 python coding_probe.py snapshot    # model catalog, prices, key status (free)
uv run --no-project --python 3.12 python coding_probe.py run --task pydicom__pydicom-1256 --condition jev --run-id my-1256-jev-01
```

The run writes `runs/coding/my-1256-jev-01/`: `result.json` (pass/fail, cost, time), `patch.diff`, `evaluation.json` (test log), `localization-0.json` (candidates, Jev scores, selection), `events.jsonl` (agent trace) and every model request/response with its billed usage. Use `--condition native` or `--condition search` for the other conditions, and a new `--run-id` for every fresh run.

The other protocols use the same commands with `--protocol coding_protocol_v2.json` (or `_v3`); `batch --lane N` runs one lane of a protocol's plan. SWE-bench Verified runs need Docker and the official harness; see the Verified handoff entry below and `requirements-swebench.txt`.

## Reproduce the reported results offline (no API calls)

Each command rebuilds its evidence file and report macros from the committed archives. Every reported number matches; raw floating-point values in the JSON can differ from the committed files below 1e-14 because summation order is not fixed.

| Result | Command | Output |
|---|---|---|
| v1 development pilot | `uv run --no-project --python 3.12 python build_coding_report.py` | `coding_evidence.json`, `report/coding_results.tex` |
| v2 extended run (41 issues, oracle, timing) | `uv run --no-project --python 3.12 python analyze_agent_runs.py` | `agent_runs_evidence.json`, `report/agent_results.tex` (restores from `agent_runs_v2.zip`) |
| v3 restricted writer (41 issues) | `uv run --no-project --python 3.12 python analyze_agent_runs.py --protocol coding_protocol_v3.json` | `agent_runs_v3_evidence.json`, `report/agent_v3_results.tex` (restores from `runs_internal-explore-v3-restricted.zip`) |
| File-selection study (225 issues) | `uv run --no-project --python 3.12 python localization_study.py analyze` | `localization_evidence.json`, `report/localization_results.tex` (restores from `localization_runs.zip`) |
| Shortlist sweep (12/24/48) | `uv run --no-project --python 3.12 python localization_study.py sweep` | `localization_sweep_evidence.json`, `report/sweep_results.tex` |
| LLM selectors (Sol, Luna) | `uv run --no-project --python 3.12 python localization_study.py llm` | `localization_llm_evidence.json`, `report/llm_results.tex` |
| Verified pilot | `uv run --no-project --python 3.12 python build_verified_report.py` | `verified_evidence.json`, `report/verified_results.tex` (needs the local `runs/verified/` directory; not yet archived) |
| Report PDF | `cd report && pdflatex coding_midpoint.tex && pdflatex coding_midpoint.tex` | `report/coding_midpoint.pdf` |

## Current status (November 6)

- **Done:** v1 pilot (15 runs), v2 extended run (164 runs), v3 restricted run (123 runs), Verified pilot (30 runs), file-selection study, sweep and LLM-selector baselines (1,125 decisions); combined midway report; 27 offline checks pass.
- **Done, option A (v3 restricted writer):** 123 runs, $10.80, no errors. The first smoke run stalled because OpenCode's shared session database (162 MB after v2) blocked session creation; an amendment recorded before any v3 outcome gives each run its own OpenCode state directory, and the stalled run is preserved as `runs/coding-v3/v3-793-jev-stalled-before-amendment`. About 60% of runs in each condition attempted a refused read or search, so the restriction was exercised.
- **Next, Verified arm of option A:** Kristjan's `shared_subset_20` (his sampling rule at N = 20: the 10 pilot tasks plus astropy-13398, django-12965/13516/16100/16333, pylint-8898, pytest-6197, sphinx-10449, sympy-22456, xarray-3095), both arms rerun from the same commit; needs Docker on the machine that runs it.
- **Team decisions open:** (1) whether to move the v2/v3 runner code into a separate `coding_probe_v2.py` so the Verified runner's fingerprint of `coding_probe.py` stays unchanged; (2) whether the course-issued OpenRouter key is the intended key for project runs (Ómar's runs used it).
- **Spend:** v1 $1.23 and synthetic pilot $0.13 (Rami); Verified $2.21 (Kristjan); file selection and sweep $0.29, LLM selectors $2.98, v2 $16.71, v3 $10.80 plus about $0.001 for the stalled smoke and debug runs (Ómar); project total about $34.

## Detailed handoff log

The sections below are the team's chronological working notes, kept unchanged.

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

### November 6 handoff — end-to-end agent runs on 41 more pydicom issues (Omar, `omar`)

- **Protocol `internal-explore-v2`** (`coding_protocol_v2.json`, committed 512e9e4 before any run; one amendment before outcomes, recorded in the file): 51 further pydicom dev issues; 41 pass the environment controls (10 need older numpy/Python and are dropped and listed). Four conditions per issue: native, Jev (12 candidates, as v1), search, and an **oracle** given the gold implementation files (upper bound, paths only). Writer, limits and evaluator unchanged from v1. 164 runs, all complete.
- **Results (41 issues, paired):**

| Condition | Repairs | Mean cost | Mean agent time | Exploration time | Explorer named a gold file |
|---|---|---|---|---|---|
| native | 18/41 | $0.139 | 46.5 s | 21.6 s | 98% |
| Jev | 19/41 | $0.091 | 30.2 s | 1.6 s | 93% |
| search | 21/41 | $0.087 | 28.7 s | 1.4 s | 63% |
| oracle | 20/41 | $0.091 | 27.4 s | 0.0 s | 100% |

- **Time and cost:** Jev vs native −16.3 s per issue (−35%; 95% paired bootstrap −19.1 to −13.7 s) and −35% cost. Search and the oracle are similar. Jev vs search: no clear difference (+1.4 s, −0.2 to +3.1; cost +5%).
- **Repairs:** no condition differs (discordant issues: Jev vs native 1/0, search vs native 3/0, oracle vs native 2/0). Even the oracle does not repair more, so on these issues localization is not the limiting step; the patch writing is. When search's files missed the gold file, 4 of 15 runs passed, against 17 of 26 when they hit, but this is confounded with issue difficulty.
- **Spend:** $16.71 of the $25 cap (HW1 course key). Two runs were refused by a lane's conservative budget guard and then completed on lane 3's ledger with the same run IDs and settings.
- **Reproduce offline:** `python3 analyze_agent_runs.py` (restores from `agent_runs_v2.zip` in a fresh clone). The full archive with every request payload (52 MB) is kept outside git.
- **Changed:** `coding_probe.py` (`--protocol`, oracle, per-phase timing, lanes, `batch`; v1 unchanged by default, 16 offline tests pass), `coding_protocol_v2.json`, `analyze_agent_runs.py`, `agent_runs_evidence.json`, `agent_runs_v2.zip`, `report/agent_results.tex`. Note: `coding_probe.py pack` still writes `coding_runs.zip` (the v1 archive); do not run it with the v2 protocol.
- **Next action:** add these results to the report; consider repeated rollouts and a harder repository where localization matters more.
- **Shared-code note (needs a team decision):** `coding_probe.py` gained the v2 options on this branch. v1 behaviour is unchanged when no `--protocol` is given, and all 27 offline checks (including `test_verified_probe.py`) pass. However, `verified_probe.source_hash()` fingerprints `coding_probe.py`, so new Verified runs would carry a different source hash than the 30 frozen `vpilot-*` runs (their recorded results are unaffected). If the team wants the Verified fingerprint unchanged, move the v2 code into a separate `coding_probe_v2.py` and restore `coding_probe.py` to its pre-v2 version.
- **Merge (November 6):** `main` (Kristjan's Verified extension) was merged into `omar`; the report now combines the Verified pilot, the extended run, the file-selection study and the sweep (5 body pages, over the 4-page midway limit; trimming pending).

### November 6 handoff — shortlist sweep, 24 and 48 candidates (Omar, `omar`)

- **Question:** does a longer shortlist let Jev recover gold files that search ranks just below 12, and at what cost in time? Protocol `localization_sweep_protocol.json` committed before outcomes; 12-candidate results reused.
- **Result (225 issues):** Jev hit@3 **85.3% / 90.2% / 91.1%** at 12 / 24 / 48 candidates (search 70.2%). 24 vs 12: +4.9 points (95% bootstrap 1.3 to 8.4; 14 wins, 3 losses, p = 0.013). 48 vs 12: +5.8 points (2.2 to 9.8; 16/3, p = 0.004). Of the 25 issues whose gold file was outside the 12 candidates, Jev recovers 13 at 24 and 15 at 48 (2 are files created by the fix). Of the 192 issues already right at 12, 189 stay right at 24 and 48. Accuracy when a gold file is listed dips slightly (96.0 / 94.9 / 93.6%).
- **Time and cost per decision:** median latency 0.29 / 0.34 / 0.40 s; at 48 candidates 44 of 225 calls took about 8 s (none above 0.63 s at 24). Mean cost $0.00022 / $0.00039 / $0.00069.
- **Recommendation:** 24 candidates — almost all of the gain, no latency tail.
- **Spend:** $0.088 (24) + $0.156 (48); study total including v1 $0.293. HW1 course key, no failures.
- **Changed:** `localization_sweep_protocol.json`, `localization_study.py` (`run --candidates`, `sweep`), `localization_sweep_evidence.json`, `report/sweep_results.tex`, `localization_runs.zip`.
- **Next action:** end-to-end agent runs on the 51 further pydicom dev issues (native, Jev, search, oracle), logging wall time per run.

### November 6 handoff — offline file-selection study (Omar, `omar`)

- **Question:** does Jev choose the right files more often than search alone? Measured directly, without the coding agent, on all 225 SWE-bench dev issues (six repositories). Protocol `localization_protocol.json` was committed (0562636) before any Jev request.
- **Result:** Jev hit@3 **85.3%** vs search **70.2%** (+15.1 points, 95% paired bootstrap 9.8 to 20.4; 38 wins vs 4 losses, sign test p < 0.001); 96% vs 79% when retrieval found a gold file. Retrieval recall@12 is 88.9%. In the 15 pilot runs every final patch edited the gold file, even when the explorer's report missed it, so end-to-end success hides localization quality.
- **Verified:** the generalized retrieval reproduces all 10 archived pilot candidate lists exactly (`python3 localization_study.py verify`). Analysis reproduces offline from `localization_runs.zip` with `python3 localization_study.py analyze`.
- **Spend:** $0.049086 for 225 Jev decisions, on the HW1 course OpenRouter key at the user's choice (team should confirm this is allowed); no failures or retries.
- **Changed:** `localization_protocol.json`, `localization_study.py`, `localization_evidence.json`, `localization_runs.zip`, `report/localization_results.tex`, `report/coding_midpoint.tex`/`.pdf` (new metric, Table 2, revised control interpretation, uncertainty plan, AI disclosure), `docs/DATA_SOURCES.md`.
- **Next action:** end-to-end runs on the 51 further pydicom dev issues under a new protocol version (needs `coding_probe.py prepare` generalized to the full dev split).

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

