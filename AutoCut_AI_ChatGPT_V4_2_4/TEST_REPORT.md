# Auto Cut AI v4.2.4 — test report

PASS:
- all CEP JavaScript syntax checks;
- host.jsx lexical syntax;
- CEP manifest XML;
- existing deterministic C1 and AppYoutube timing tests;
- H.264/AAC MP4 probe -> direct-import decision;
- VP9 MP4 probe -> convert decision;
- VP9 test media converted by FFmpeg to H.264/yuv420p + AAC MP4;
- converted output re-probed as Premiere-safe;
- converted duration matched source in regression fixture;
- main flow uses compatibility path for Premiere;
- one-time forced conversion retry after Premiere import rejection;
- installer verification requires media compatibility module;
- ZIP integrity.

The user's exact 1.29 GB source video is not available in the build environment; v4.2.4 probes that file locally on the user's Windows machine before Premiere import.