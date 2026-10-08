# Auto Cut AI v4.0

Rebuild of the Auto Cut Premiere CEP extension with direct ChatGPT sign-in and a three-stage semantic SRT workflow.

## Inputs
- Original video
- Original audio MP3/WAV/M4A/AAC
- Timestamped transcript SRT/VTT/TXT
- ChatGPT account via Sign in with ChatGPT

## AI pipeline
1. Normalize the transcript to SRT without rewriting text or inventing timestamps.
2. Ask ChatGPT to select SRT cue ranges to remove, targeting about 15% by default and prioritizing ads/sponsors, singing/music segments, off-topic tangents, repetition, and low-value detail.
3. Ask ChatGPT to output a cut-only SRT containing only cues to remove, preserving original timestamps and text exactly.

A local validator then compares the stage-3 SRT against stage 1. If ChatGPT changed text/timestamps or omitted selected cues, C2 is rebuilt deterministically from stage-2 cue IDs.

## Audio
The MP3 is not uploaded through the ChatGPT-plan flow. It is analyzed locally for:
- duration;
- silence detection when ffmpeg/ffprobe are available;
- snapping cut boundaries to nearby silence (about ±0.8 s).

If ffmpeg is not available, the extension still runs and uses browser audio metadata for duration, without silence snapping.

## Premiere executor
After C1/C2 are validated, the existing deterministic Auto Cut engine:
1. creates a source comparison sequence with C1;
2. imports C2 and adds deletion markers;
3. creates a new _DaCat sequence from KEEP ranges;
4. optionally retimes and restores subtitles.

## Compatibility
CEP manifest targets Premiere Pro 2021 / 15.x and newer.

## Security
- OAuth Authorization Code + PKCE
- state + nonce
- ID-token issuer/audience/expiry/nonce + JWKS signature validation
- ChatGPT tokens stored using Windows DPAPI (CurrentUser)
- Responses requests use store=false and stream=true

The source package produced in the build is named AutoCut_AI_ChatGPT_V4.zip.
