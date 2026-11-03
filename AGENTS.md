# Instructions for Project Coding Agents

These instructions apply to all work in this repository.

1. Read `README.md` and `docs/PROJECT_PLAN.md` before starting. Inspect current files, branches, task claims, and run manifests; do not assume this plan describes already implemented code.
2. Claim a task with owner, branch, date, dependency, and expected artifact in the README before substantial work. Avoid editing another person's active work without coordination.
3. Update the README status report in every work PR and before ending a session or handing off. Include what changed, what is verified, what remains, dependencies, active claims, blockers, and one exact next action.
4. Append a dated handoff entry with changed files, checks/commands and outcomes, run IDs/checkpoint/artifact locations, and spend/remaining balances when known. Keep the current status accurate as well as the history.
5. Never claim code works without evidence. Distinguish local drafts from published changes, implementation from experiments, empirical estimates from statistical guarantees, and planned commands from tested commands.
6. Follow the task dependencies. Establish the unchanged harness and strong/cheap baselines before routing changes. Do not build a custom harness or train models as the first experiment.
7. Keep the primary experiment narrow. Record significant protocol/scope changes with a reason and affected manifests. Preserve original results after amendments.
8. Freeze data splits, prompts, model/provider revisions, thresholds, and analysis rules before final evaluation. Never tune on test outcomes or expose evaluator gold assets to the agent/router.
9. Look up existing run records before launching work. Resume or retrieve artifacts before rerunning completed tasks. Record failures and partial runs instead of deleting them.
10. Use separate per-account/service budgets with bounded steps, tokens, time, retries, and concurrency. Include gate, retries, reasoning, caching, training, storage, and state-construction costs. Credits are not zero deployment cost.
11. Keep credentials out of git, logs, model inputs, and handoffs. Use the explicitly selected GitHub account; do not switch accounts silently to work around access failure.
12. Preserve raw traces and immutable manifests with accessible artifact pointers/checksums. Keep large data, checkpoints, and task working copies outside git.
13. Run checks appropriate to the change. For runner/evaluator work, verify leakage prevention, cost capture, routing fallback, and resumability using meaningful small checks before expensive jobs.
14. Use formal, precise language in the report, verify references, and maintain an accurate AI-use disclosure.
