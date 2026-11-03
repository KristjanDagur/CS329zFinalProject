# Midpoint Prototype and Submission Plan

Status: planned; no prototype or experiments have been implemented yet.

Target working prototype: **Wednesday, November 4, 2026**, as requested by the team. The published deadline for the midpoint video and report is **Friday, November 6, 2026, 11:59 p.m. Pacific** [course deadline table](https://cs329z.stanford.edu/index.html#deadlines). Treat the earlier date as the internal target; a newer instructor announcement takes precedence.

## Minimum working prototype

One command accepts a coding task, calls Jev for a cheap-versus-strong decision, launches the existing OpenCode harness with the selected model, lets that harness inspect/edit/run tests in an isolated task directory, and records the patch, independently checked outcome, route, time, and measured model cost. An API error must route strong through an explicit, logged fallback.

Use two development tasks initially. The full coding benchmark, trained router, calibrated 5% risk target, and demonstrated savings are final-study goals; they are not claims the midpoint prototype can make without evidence. Use a clearly labeled provisional threshold in the demo and disclose that it has not been calibrated.

## M1 — Establish a real agent execution path

Suggested lead: Kristjan / workstream A. Start immediately after claiming ownership.

- [ ] Pin/install OpenCode; configure one accessible cheap/strong tool-capable model pair using environment credentials.
- [ ] Run one task with each model in the unchanged harness; collect traces and produced patches.
- [ ] Verify that the task's independent tests actually execute and detect a deliberately wrong patch.
- [ ] Record exact install/config/run commands and limitations in the README.

Prefer two official SWE-bench development tasks. If task containers consume the available prototype time, use a small local fixture repository with at least six independently testable repair tasks: three visible demonstration/development tasks and three reserved sanity-check tasks. Record their construction and keep their tests separate from router inputs. Label this as a synthetic prototype dataset, not SWE-bench or a meaningful final evaluation. Resolve the official execution environment after the midpoint.

## M2 — Add the one-decision router and logging

Suggested lead: Rami / workstream C. Work from M1's agreed invocation/config interface.

- [ ] Implement one Jev request on task-visible state; persist its raw score.
- [ ] Use a configurable provisional threshold to select the cheap or strong M1 invocation.
- [ ] Add a logged strong fallback for malformed responses/timeouts.
- [ ] Save a machine-readable result with task/model IDs, score/route, patch path, evaluator outcome, cost, and elapsed time.
- [ ] Check model selection explicitly in the trace. A printed route label without changing the actual model is not a working router.

Do not train a model, implement a new agent loop, or tune against final test data for this milestone. Synthetic/mock provider responses may test routing code, but the recorded working prototype must include real model calls and actual tool execution; label any mocked segment explicitly.

## M3 — Evaluation scaffold and midway paper

Suggested lead: Ómar / workstream B, with factual contributions from all three.

- [ ] Freeze a small development-task manifest and a result schema shared with M1/M2.
- [ ] Compare the actual strong-only, cheap-only, and routed prototype runs on the same development tasks, within the $30 team smoke envelope. Report the small sample as a sanity check, not established savings.
- [ ] Record what the final benchmark and independent grader will be, how task selection will work, and the final metrics/baselines from the main plan.
- [ ] Draft the **3–4 page ICLR-format midway report** with these required sections:
  1. Research Questions / Problem Specification: one paragraph on the routing question and coding-agent use case.
  2. Environment & Data: existing harness, tool permissions, task source/construction, independent tests, proposed final splits, success and cost metrics.
  3. Methods: gate, provisional threshold, chosen model pair, unchanged harness, fallback and instrumentation; distinguish implemented components from planned calibration/training.
  4. Summary of Progress: measured work, trace/artifact evidence, remaining tasks, access/environment issues, and risks to completion.
  5. References: proposal-style entries; verify metadata and alphabetical ordering.
  6. AI-Use Disclosure: actual roles of AI in planning, writing, code/debugging, data/experiments, and analysis.

Prior-work discussion is not required at this stage. Environment & Data, Methods, and Progress are the grading focus. Never fill a results paragraph with invented numbers while implementation is in progress.

## M4 — Reproduction, recording, and submission

All three; finish the working path by November 4, then use November 5–6 for fixes, recording, and submission.

- [ ] A teammate follows the README from a clean environment: install, set credential environment variables, run one task, and reproduce its saved result.
- [ ] Record a short, clear video showing the input task, actual Jev decision/model selection, actual coding-agent tool execution, resulting patch/test outcome, and measured cost/latency. The course text supplied here does not specify a video length; check the submission portal rather than inventing one.
- [ ] Explain the strong reference and final study briefly, including that the threshold is provisional and the pilot is too small for a performance claim.
- [ ] Ensure the private repo is accessible to the graders as required by the course; do not change repository visibility without a team decision.
- [ ] Submit the recorded video, repository link, and report through the designated course submission channels before the deadline. Submission itself remains the team's task.
- [ ] Update README status, tested commands, run IDs, artifact links, costs, remaining work, and the exact next action.

The milestone is complete only when the prototype runs, its README has been independently followed, and the team confirms submission. Planning files alone do not satisfy it.
