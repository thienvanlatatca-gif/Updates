# v4.2.2 critical path

The screenshot proves Premiere was still running v4.2.0:

- footer: `Auto Cut AI v4.2.0 — AppYoutube Timing Bridge`
- host ping: `"version":"4.2.0"`
- log: `AI Bước 1/3: gửi transcript CÓ TIMELINE cho ChatGPT để chuẩn hóa SRT`

The fixed runtime must instead execute:

```js
var timing = TimingBridge.resolve(...);

var built = C1Builder.fromFile(timing.path);
var c1 = built.cues;
var c1Path = saveText("C1_goc_AI_"+st+".srt", C1Builder.toSrt(c1));

// ChatGPT begins at semantic cut classification.
// There must be NO ChatGPTDirect.stage1(...) call in main.js.
var r2 = await promiseCall(function(cb) {
    ChatGPTDirect.stage2(c1Path, policy, state.audioInfo.summary, model, deltaLogger("Bước 2"), cb);
});
```

Installer v4.2.2 verifies that exact condition in the installed CEP directory and fails if stale stage-1 code remains.
