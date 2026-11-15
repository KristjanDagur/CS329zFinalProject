# Evidence-matched intent experiment

Owner: Rami with Codex (Astra). Branch: rami. Designed November 14, 2026.

## Question and estimands

How much of the retrieval agent's advantage is explained by supplying relevant labeled examples, rather than repeated model calls and adaptive search? Does Jev remain competitive when both single-call models see exactly the same evidence?

The four single-call arms cross model (Jev/Sol) with evidence (static catalog/static catalog plus eight fixed BM25 support examples). Static prompts match the original study. Retrieved prompts add one common instruction and the same ordered support records to both models. The native OpenCode agent retains its original tools, prompt and limits. It may choose different searches, so comparison against it measures the whole adaptive-agent package, not reasoning in isolation. The interaction between model and evidence is a secondary estimand.

The original 7,039 support rows, catalog and grouped splits are unchanged. Fixed retrieval queries the raw utterance, never a gold label or an agent-generated query. All 77 labels remain available. Add one fixed, standard supervised baseline: word/character TF-IDF plus linear SVM trained only on support data. It has more labeled training exposure than the prompted catalog, and its different setup cost is disclosed. No hyperparameter sweep or embedding service is required.

## Collection

Run 154 balanced development examples (two per intent) to verify leakage boundaries, model revisions, identical evidence, receipts, failures and cost projections. All five conditions are collected contemporaneously and interleaved in a seeded order. Repeating the static/agent conditions is a planned replication needed to avoid confounding the new evidence effect with collection date, caching or provider changes. It does not replace any original run.

Before new test calls, publish the protocol, source hashes, exact test IDs and model snapshot. Prefer all 3,080 test examples. If the development projection with 25% headroom exceeds the $50 test allowance, freeze 1,540 balanced examples before outcomes; otherwise stop and document. Total additional cap $60 (development $6, test $50, live $4); original accounted $38.147568 remains below the existing $120 ceiling even at the new cap. Recheck account allowance before collection. Tinker: no training/API spend.

Use 24 bounded workers with two isolated persistent native servers (12 native sessions). Preserve each request, raw response, tool trace, receipt and prediction. Resume only exact completed records; never silently retry a partially paid job. Separate ledger and run directory; frozen original runners/evidence stay byte-identical.

After the main collection, run a preselected 30-example development timing panel serially with fresh trajectories and randomized arm order. Report paired latency intervals, p50/p95 and warm-runtime conditions. Do not interpret parallel collection times as deployment latency. Dollar estimates use actual receipts including cache reads; also provide uncached token-price sensitivity. Local CPU time and classifier training time are reported separately from API dollars.

## Analysis and publication limits

Four primary paired accuracy comparisons are specified in retrieval_protocol.json, with exact McNemar and Holm adjustment. Report 10,000 paired within-intent bootstrap intervals and whole-intent sensitivity for accuracy and cost. Report 2-point noninferiority against the agent as a secondary practical-tolerance test, never equivalence. Include per-intent results, confusion/error examples, support-overlap sensitivity, evidence-model interaction, and comparison to the original trajectories for reproducibility.

This is an exploratory follow-up on an already examined test benchmark. Its new method and analysis are frozen before new outcomes, but the benchmark is not fresh confirmatory evidence. No new confidence threshold or certification is fitted in this experiment. The original failed certification remains unchanged. A later CLINC150/OOS study requires a separate protocol.

Expected artifacts: retrieval_probe.py, retrieval_analysis.py, offline checks, retrieval_frozen.json, retrieval_evidence.json, portable trace archive, report/retrieval_results.md and exportable figures. The README remains the current status and handoff.
