# Midpoint video walkthrough

`demo_replay.mp4` is a silent, captioned replay rendered from real saved model/tool traces. It is not a screen capture or live run. Review it before deciding whether to submit it or record a live terminal walkthrough with this script. The course video-length requirement, if any, still needs checking in the submission portal.

1. **Problem and scope (about 8 seconds).** “We ask whether a small decision model can route coding tasks to a cheaper model while preserving task success. This is our working midpoint prototype. The video replays actual recorded execution on synthetic development tasks.”
2. **Architecture (about 10 seconds).** “Jev sees the issue, broken source, model pair, and limits. A threshold selects the model for the existing OpenCode harness. OpenCode reads and repairs the file and runs public smoke tests. A separate grader checks the patch. A local adapter records billed usage and enforces request and task limits.”
3. **Strong route (recorded duration about 13 seconds).** Show `m2-stable-jev-v1`. “Jev returned 0.79. Our provisional 0.90 threshold selected GPT-6.1-Sol. These are the actual recorded tool events. The repaired file passed six independent tests.”
4. **Cheap route (recorded duration about 9 seconds).** Show `m2-stable-jev-sensitivity075`. “This is a separate, post-hoc development demonstration at threshold 0.75. The score was again 0.79, so the real upstream request used Qwen3-Coder-Next. This verifies the cheap-routing path; it is not evidence that 0.75 is calibrated.”
5. **Patch and evaluation (about 9 seconds).** Show the actual diff and saved `evaluation.json`. “The agent repaired the implementation; a success label alone is insufficient. The grader rejects the broken starter and evaluates a fresh copy of the final source.”
6. **Pilot results and limitations (about 15 seconds).** “All three policies passed the same three development tasks. At the default threshold, Jev routed everything strong. Always cheap already succeeded on every task, so this sample establishes feasibility, not routing value or general savings. Latency and costs include the actual captured calls.”
7. **Remaining work (about 10 seconds).** “Next are independent teammate reproduction, report review, and submission. The final study needs a repository-scale environment, more varied tasks, development-only calibration, heuristic and random controls, locked evaluation, and error analysis.”

For a live terminal recording, start with `python3 -m unittest -v test_midpoint.py`, then show a small `python3 midpoint.py run ... --policy jev` invocation and its result. Use a new run ID for a real new execution. Reusing a completed run ID replays its stored result without another API call; label that as a replay. Keep credentials off screen.

The team must still verify course repository access, choose/record the final video, review the report, and submit through the course portal. Nothing has been submitted automatically.
