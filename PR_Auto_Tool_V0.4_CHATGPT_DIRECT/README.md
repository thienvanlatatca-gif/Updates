# PR Auto Tool V0.4 — ChatGPT Direct

Premiere automation utility for Premiere Pro 2021 / 2022 / 2023+ with a direct ChatGPT command layer.

## New in V0.4

- **Continue with ChatGPT** sign-in flow using OpenAI's official Sign in with ChatGPT OAuth route.
- Paste a YouTube URL and choose an existing SRT.
- The full SRT is attached to the Responses API as an `input_file`.
- The YouTube URL is reference context only; local yt-dlp metadata is added when available. The tool does not pretend a URL alone means ChatGPT watched the video.
- Free-form commands can be sent directly from the PR Auto desktop UI.
- Dedicated semantic cut-plan command:
  - ChatGPT selects **SRT cue IDs**, not timestamps.
  - Local deterministic code maps cue IDs to timestamps.
  - Overlaps are merged and actual cut percentage is calculated.
  - Review SRT and cut-only SRT are generated before Premiere execution.
- OAuth profile is protected with Windows DPAPI on Windows.
- Requests use `store=false` and `stream=true`.

## Cut-plan outputs

Written under the PR Auto bridge folder:

- `ai_cut_plan.json`
- `ai_cut_review/<name>_AI_REVIEW.srt`
- `ai_cut_review/<name>_AI_CUT_ONLY.srt`

## Important V0.4 boundary

V0.4 analyzes and validates the AI cut plan but does **not automatically execute the AI cut on the Premiere timeline yet**. This is deliberate: the Premiere executor will consume only a validated deterministic plan after real-host testing.

## Compatibility

The Premiere bridge remains CEP + ExtendScript and preserves the V0.3 target:

- Premiere Pro 2021 / 15.x
- Premiere Pro 2022 / 22.x
- Premiere Pro 2023 / 23.x
- newer CEP-compatible Premiere builds

## Tests

- Python compile: PASS
- Existing PR Auto self-test: PASS
- ChatGPT offline cut-plan validation test: PASS
- CEP JavaScript syntax: PASS
- CEP manifest XML parse: PASS
- ZIP integrity: PASS

A real ChatGPT OAuth login requires user consent in a browser and therefore is not automated in the build environment.
