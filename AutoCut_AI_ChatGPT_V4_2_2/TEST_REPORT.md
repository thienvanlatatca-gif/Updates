# Auto Cut AI v4.2.2 test report

PASS:
- all extension JS files: Node syntax check;
- host.jsx lexical syntax;
- offline semantic/model tests;
- AppYoutube Timing Bridge tests;
- 511-cue AppYoutube-style SRT -> deterministic C1;
- C1 round-trip 511/511 cues;
- main critical path contains C1Builder.fromFile(timing.path);
- main critical path contains no ChatGPTDirect.stage1(...);
- CEP manifest XML parse;
- ZIP integrity;
- installer blocks while Premiere is running;
- installer deletes old CEP directory;
- installer mirrors a clean copy with robocopy;
- installer verifies v4.2.2, c1Builder.js, deterministic main.js and host version;
- standalone installed-version verifier included.

Root cause of the user's repeated screenshot was stale installed CEP v4.2.0, not the 511-cue SRT itself.
