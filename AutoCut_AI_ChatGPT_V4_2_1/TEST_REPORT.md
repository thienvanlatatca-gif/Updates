# Auto Cut AI v4.2.1 — Test report

Root cause reproduced: v4.2 Timing Bridge correctly found a 511-cue AppYoutube SRT, but Stage 1 still depended on ChatGPT reproducing the full SRT. That model-output step is now removed from the critical path.

PASS:
- AppYoutube Transcript.txt + exact sibling <video>.srt resolution;
- direct SRT resolution;
- words.json-only timing recovery;
- 511-cue AppYoutube-style SRT -> deterministic C1, no cue loss;
- C1 canonical SRT round-trip: 511/511 cues;
- Stage 1 main pipeline contains no ChatGPTDirect.stage1(...) dependency;
- Stage 2/3 still use ChatGPT for semantic cut selection and cut-only filtering;
- existing model-catalog and semantic-policy tests;
- deterministic CutPlan and empty-C2 tests;
- JavaScript syntax, CEP XML, HTML resources/load order, ZIP integrity.

The packaged v4.2.1 build uses C1Builder.fromFile(timing.path) before ChatGPT semantic analysis.