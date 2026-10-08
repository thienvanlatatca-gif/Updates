# Auto Cut AI v4.2.4 — Premiere Media Compatibility Bridge

The reported failure happens at Premiere step 1 while importing the selected source video.

AppYoutube VoiceSync V2.2 currently uses yt-dlp format selectors starting with `bv*` and then sets `merge_output_format: mp4`. That forces the **container** to MP4, not the video codec. YouTube may therefore deliver AV1/VP9 inside an .mp4 file, which Windows can play while Premiere Pro 2021 may reject as `unsupported compression type`.

v4.2.4 probes the real streams before Premiere import:

- direct import for H.264 + common 4:2:0 pixel format + compatible audio in MP4/MOV/M4V;
- otherwise create a short-name `_PremiereSafe/PR_SAFE_<hash>.mp4`;
- encode unsafe video as H.264/yuv420p and unsafe audio as AAC;
- validate the converted file and compare source/output duration;
- if Premiere rejects a file that probed safe, force-convert once and retry Premiere step 1.

The ChatGPT/SRT timeline is not regenerated during this process.