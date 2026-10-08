# Auto Cut AI v4.2 — test report

PASS:
- inspected AppYoutube VoiceSync V2.2 source;
- confirmed `write_srt()` outputs `HH:MM:SS,mmm --> HH:MM:SS,mmm`;
- confirmed AppYoutube output path `<video>.srt`;
- confirmed `<video>.words.json` uses source-media word timestamps;
- confirmed `Transcript.txt` intentionally strips SRT timestamps through `srt_to_text()`;
- dynamic extraction test from AppYoutube source: SRT timed / Transcript.txt untimed;
- Timing Bridge: plain Transcript.txt + exact sibling video SRT;
- Timing Bridge: direct SRT;
- Timing Bridge: words.json-only recovery;
- Timing Bridge: multiple SRTs, exact video stem wins;
- Timing Bridge: no timed sidecar fails instead of fabricating timestamps;
- existing Auto Cut offline self-test;
- JavaScript syntax;
- CEP XML parse;
- HTML resource validation;
- final ZIP integrity.

Real Premiere/OAuth execution still requires the user's Windows/Premiere host.
