# Sources and Planning Provenance

Reviewed 2026-11-03. Service availability, model families, prices, and interfaces can change; pin them during implementation.

## Proposal and feedback

Local source: `/Users/ramimrad/cs329z/project/cs329z_project_proposal.pdf` (three pages). Page 1 contains grading and instructor feedback; pages 2–3 contain the two-page proposal. The proposal pages are raster content, so text extraction alone missed them. All three pages were rendered and visually inspected.

The proposal received 4/4. The feedback asks for linear experiments, small substitutions in an existing harness such as OpenCode, comparison with a strong full-harness reference, a cost/performance focus, limited scope, and formal writing. The proposal names Jev/Kev, tool-using escalation, BANKING77/CLINC150, a 5% accepted-error target, random and agent-only controls, confidence transfer, and high-confidence mistakes.

The primary coding track and task-launch routing choice in the plan are recommendations interpreting that feedback. They are not presented as an instructor-approved revised scope. The original bibliography has not been independently verified in full; verify its papers, metadata, and claims before the final report. The graded PDF is not included in the repository bundle.

## Primary implementation references

- **[S1] [OpenCode plugin documentation](https://opencode.ai/docs/plugins/) and [provider documentation](https://docs.opencode.ai/docs/providers/).** OpenCode documents extension hooks and provider configuration. A supported hook does not itself prove that arbitrary per-step model replacement is available in the selected version. Start with task-launch configuration and test any internal integration before promising it.
- **[S2] [OpenRouter Jev documentation](https://openrouter.ai/docs/guides/community/jev).** Documents typed decisions, versioned Jev availability, Decisions/System One API surfaces, and billing through the OpenRouter account. Verify access and current pricing with the team's account during the first probe; course-credit eligibility has not been checked.
- **[S3] [TypeSafe introduction](https://docs.typesafe.ai/introduction) and [confidence documentation](https://docs.typesafe.ai/confidence).** Explains typed question outputs and the distinction between probability distributions and derived confidence. Our cheap-task success target still requires outcome-specific validation.
- **[S4] [Kev source repository and README](https://github.com/jaredpalmer/kev).** Current upstream offers multiple model sizes and a TypeSafe-compatible interface, with local serving and versioned weights. Pin source/weights and audit training data/hardware requirements; do not assume the proposal's earlier model description still matches the selected release or that Kev is trainable through Tinker unchanged.
- **[S5] [Tinker models and pricing](https://tinker-docs.thinkingmachines.ai/tinker/models/models_and_pricing/).** Documents supported models, sampling/training token prices, and checkpoint storage charges. No actual team balances have been inspected; no price in this plan is a quote for an executed job.
- **[S6] [Tinker OpenCode integration](https://tinker-docs.thinkingmachines.ai/tinker/opencode/).** Documents an OpenAI-compatible integration and sampler checkpoints. Capability does not establish support for custom Kev heads. Configured display-cost placeholders must not replace actual billing measurements.
- **[S7] [Official SWE-bench Lite overview](https://www.swebench.com/lite).** Describes the 300 test instances and 23 development instances. Final task IDs, data revision, evaluator revision, exclusions, and execution images remain to be frozen.
- **[S8] [BANKING77 original dataset repository](https://github.com/PolyAI-LDN/task-specific-datasets).** Provides bank-query intents and dataset licensing/citation information. Preserve attribution and record the exact data revision for any optional diagnostic.
- **[S9] [CLINC150 original dataset repository](https://github.com/CLINC/oos-eval).** Describes in-scope and out-of-scope splits and the single-intent setting. Include OOS outcomes explicitly in any transfer study.
- **[S10] [CS329Z course deadline table](https://cs329z.stanford.edu/index.html#deadlines).** As checked November 3: midpoint video/report due November 6 at 11:59 p.m. Pacific; final live demo December 9 at 3:30–6:30 p.m.; final report date/time TBA within December 7–11. The team's November 4 prototype target is earlier than the published midpoint deadline. Recheck announcements for changes.
- **[S11] [CS329Z project requirements](https://cs329z.stanford.edu/project.html).** Reviewed alongside the user-supplied requirements: midway 3–4 pages and recorded prototype demo; final 8-page ICLR report and live demo; required report sections and a README that supports a reproducible quick start. Report requirements in the plan/checklist also derive directly from the user's supplied text.

## Access and publication evidence

Selected connection: GitHub **Cal account**, login **ramimrad**. The connector returned 404 for repository metadata and README; installed-repository search returned no match and repository search reported no visibility. This does not prove the repository is absent. An unauthenticated `git ls-remote` required unavailable credentials. The `gh` CLI was not installed. All connector requests used the Cal account. The browser initially used the Stanford identity; after the user signed in, the browser identity was verified as ramimrad before publishing. Initial access probes made no repository changes.

After the user signed into the browser as **ramimrad**, browser inspection confirmed the private repository and its `main` branch, containing only a starter `README.md` and `.gitignore`. The browser identity was verified through the user menu. The connector still returned 404 after browser login. Publication can therefore proceed through the browser; success must be verified from the repository after committing.

The detailed plan was committed to `main` through the browser as **ramimrad** with message `docs: add end-to-end research plan and milestone schedule`. Supporting files and the current README are published in the same documentation setup session. No model experiments were run.

## Midpoint implementation evidence — November 3

The prototype uses OpenCode 1.19.5 from the official npm platform package, validated against npm SHA-512 integrity. The request-time model price/capability snapshot is `model_snapshot.json`; actual costs/providers are in the saved request receipts. Models: `qwen/qwen3-coder-next`, `openai/gpt-6.1-sol`, and `typesafe/jev-1.14`. No model has been trained.

Additional primary documentation consulted: [OpenCode CLI](https://opencode.ai/docs/cli/), [agents](https://opencode.ai/docs/agents/), [permissions](https://opencode.ai/docs/permissions/), and [OpenRouter Jev tutorial](https://openrouter.ai/docs/guides/community/jev-tutorial). These informed the configuration and adapter, which were then validated by real calls. The tutorial's older version examples were not assumed to override the live model catalog.

The report uses the unmodified [official ICLR 2027 style](https://github.com/ICLR/Master-Template/tree/master/iclr2027), with named course authors and an explicit draft header. The stylesheet's Git blob SHA was `f61ad7efce0855557694078c0945e6c33feb8236`; the bibliography style's SHA was `a85a0087d13bb3d19ba2ca53cae3a9db47119853`. The SWE-bench reference was checked against [the original paper](https://arxiv.org/abs/2310.06770). The current dataset is synthetic and must not be attributed to SWE-bench.

`midpoint_evidence.json` identifies the nine primary runs, two supplementary checks, two excluded setup attempts, identical primary source hashes, and total metered spending. Raw local files are preserved; the portable ZIP strips machine-local paths and hashes its sanitized content. The video is a generated replay of actual traces, not a live screen capture. Team review and submission have not occurred.
