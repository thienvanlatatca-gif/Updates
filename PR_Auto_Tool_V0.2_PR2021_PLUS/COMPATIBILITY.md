# Compatibility design

The V0.1 bridge was UXP-only and declared Premiere 25.6 as the minimum host. That cannot load in Premiere Pro 2021.

V0.2 changes the integration layer, not the job format:

- Desktop job schema remains `pr-auto-job-v1`.
- Premiere 2021+ uses CEP + ExtendScript.
- Manifest host range is `PPRO [15.0,99.9]`.
- MOGRT insertion uses `activeSequence.importMGT(path, ticks, videoTrackOffset, audioTrackOffset)`.
- Exposed MOGRT text is edited through `TrackItem.getMGTComponent().properties`.
- `app.project.createNewSequenceFromClips()` creates the sequence from the source media.
- `app.project.importFiles()` imports source/background/BGM/logo/voice assets.
- Track creation has a guarded QE fallback and clamps to existing tracks if required.

The implementation is based on the same API pattern used by Adobe's public CEP PProPanel sample for `importMGT()` and `getMGTComponent()`.

MOGRT compatibility is separate from plugin compatibility: a MOGRT authored with a newer After Effects/Premiere feature may still be rejected by Premiere 2021. Use MOGRT files authored for Premiere 2021-era compatibility when targeting 15.x.
