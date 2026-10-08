# Auto Cut AI v4.2 — AppYoutube Timing Bridge

## Root cause

AppYoutube VoiceSync V2.2 already creates real source-media timing:

- `<video>.srt` via `write_srt()`;
- `<video>.words.json` with `timeline_basis: source_media` when word timing is available.

However AppYoutube also creates `Transcript.txt` by calling `srt_to_text()`. That helper intentionally removes cue numbers and every line containing `-->`, so `Transcript.txt` is plain reading text with no timeline.

Auto Cut v4.1 sent the selected `Transcript.txt` directly to ChatGPT stage 1, so ChatGPT correctly returned `ERROR_NO_TIMESTAMPS`.

## v4.2 behavior

Before ChatGPT stage 1, a deterministic Timing Bridge resolves the timeline locally:

1. If the selected SRT/VTT/TXT already contains timing, use it directly.
2. If the user selected AppYoutube `Transcript.txt`, first look for exact `<selected-video-stem>.srt` in the same directory.
3. If no exact SRT exists, evaluate sibling SRT files using video-name and transcript-content matching to avoid picking the wrong subtitle.
4. If no SRT exists but `<video>.words.json` exists, reconstruct `C0_timing_recovered_from_words.srt` from the real word `start/end` values.
5. If no timed sidecar exists, stop. The tool never invents timeline data.

The resolved timed SRT is what ChatGPT receives in stage 1.

## AppYoutube layout supported

```
Video Folder/
  My Video.mp4
  My Video.srt
  My Video.words.json
  Transcript.txt
  Transcript_status.json
```

Users may select either `My Video.srt` directly or `Transcript.txt`; v4.2 recovers the correct SRT/words timeline automatically.

## Safety

ChatGPT remains a semantic selector only. Final Premiere cut boundaries originate from AppYoutube/YouTube/faster-whisper timestamps and local deterministic validation.
