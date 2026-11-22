# Candidate data for further experiments (Omar, November 6)

Keep development and final-test data separate. Counts for SWE-bench were checked against the Hugging Face dataset on November 6; the others are from published descriptions and should be confirmed before use.

| Use | Dataset | Notes |
|---|---|---|
| Development (used by the file-selection study) | SWE-bench dev split, 225 issues: pvlib 63, pydicom 56, sqlfluff 50, astroid 31, pyvista 16, marshmallow 9 | Same format as the pilot. 124 of 225 official fixes change one file. The 51 further pydicom issues reuse the existing evaluator environment and are the next end-to-end candidates. |
| Larger development set | SWE-Gym (about 2.4k real issues from about 11 Python repositories, with executable environments) | For scaling repeated rollouts. |
| Held-out final test | SWE-bench Verified (500 human-validated test instances, official Docker evaluator) | Do not inspect outcomes until the final protocol is frozen. |
| Contamination check | SWE-rebench, SWE-bench-Live (continuously collected newer issues) | Newer issues are less likely to be in model training data. |
| Localization-specific | LocBench (LocAgent paper); gold-patch file lists from any SWE-bench split | Purpose-built for file/function localization. |
