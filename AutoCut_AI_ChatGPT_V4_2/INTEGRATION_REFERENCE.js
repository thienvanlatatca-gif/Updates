// Auto Cut v4.2 integration point.
// Run this BEFORE ChatGPT stage 1.
var timing = TimingBridge.resolve({
    scriptPath: state.sourceScript.path,
    videoPath: state.video.path,
    outputDir: outputDir()
});

state.resolvedScript = timing;

// Stage 1 must receive the resolved timed source, NOT plain AppYoutube Transcript.txt.
ChatGPTDirect.stage1(
    timing.path,
    state.audioInfo.summary,
    model,
    deltaLogger("Bước 1"),
    callback
);

// If AppYoutube only has words.json, TimingBridge creates
// C0_timing_recovered_from_words.srt using real word start/end timestamps.
// If neither SRT nor words.json exists, TimingBridge throws rather than invent timing.
