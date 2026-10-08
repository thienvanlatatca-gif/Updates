# Three ChatGPT stages

## Stage 1 — normalize transcript
Convert the attached timestamped transcript to valid SRT. Preserve all text and order. Do not summarize, translate, paraphrase, or invent timestamps. If no timestamp information exists, return ERROR_NO_TIMESTAMPS.

## Stage 2 — select cuts
From the full SRT, select cue ranges to remove so the video is reduced by approximately the requested percentage (default 15%, target tolerance ±3 percentage points). Prefer ads/sponsorship, singing/music that does not serve the core content, off-topic material, repetition, and low-value detail. Preserve the hook, main problem, causal argument, important facts/numbers, necessary examples, turning points, climax, and conclusion. Return cue IDs/ranges only; do not generate timestamps.

## Stage 3 — cut-only SRT
From the full SRT plus stage-2 decisions, output a new SRT containing only cues to cut. Preserve every selected cue's timestamp and text exactly. Remove all cues that should stay. Do not annotate or rewrite.

The extension validates stage 3 against stage 1 and reconstructs C2 deterministically from stage-2 cue IDs if needed.
