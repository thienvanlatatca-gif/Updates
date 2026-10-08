# v4.2.1 C1 deterministic integration

The v4.2 failure happened after Timing Bridge successfully resolved a valid 511-cue AppYoutube SRT. The remaining problem was Stage 1 asking ChatGPT to reproduce the entire SRT.

The production fix changes the critical path to:

1. TimingBridge.resolve(...) finds the real SRT/words timeline.
2. C1Builder.fromFile(timing.path) parses and validates it locally.
3. C1Builder.toSrt(...) writes canonical C1 locally.
4. ChatGPT starts at semantic cut selection (Stage 2).
5. Stage 3 is still validated against C1 and rebuilt from Stage-2 cue IDs if needed.

This keeps timestamps deterministic and prevents long-model-output formatting/truncation from breaking C1.