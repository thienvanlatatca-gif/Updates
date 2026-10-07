# PR Auto Tool V0.2 — Premiere Pro 2021+

This version replaces the Premiere 25.6+ UXP-only bridge with a **CEP + ExtendScript** bridge so the tool can run on **Premiere Pro 2021 / 15.x and newer**.

## Architecture

- Windows controller: YouTube/local video intake, SRT/word timing, background/BGM/logo/voice settings, Text Template selection, writes `latest_job.json`.
- Premiere bridge: CEP panel + ExtendScript host.
- Bridge folder: `%APPDATA%\PR_Auto_Tool_V02\bridge`.
- CEP install folder: `%APPDATA%\Adobe\CEP\extensions\PR_Auto_Bridge_2021_Plus`.

## Premiere 2021 APIs used

- `app.project.importFiles()`
- `app.project.createNewSequenceFromClips()`
- `Sequence.overwriteClip()`
- `Sequence.importMGT()`
- `TrackItem.getMGTComponent()`
- QE `addTracks()` only as a guarded fallback when the sequence has too few tracks.

## Text Templates

The same 10 CapCut-style MOGRT slots are retained. MOGRT binaries are not redistributed; the user maps local .mogrt files inside the CEP panel.

## Install

Run `INSTALL_PREMIERE_2021_PLUGIN.bat`, restart Premiere, then open:

- Premiere 2021: `Window > Extensions > PR Auto Bridge 2021+`
- Newer versions may show `Window > Extensions (Legacy)`

No UXP Developer Tool is required.

## Validation

- Python/job builder compile + self-test.
- CEP manifest XML parse.
- Panel JavaScript syntax check.
- ExtendScript host syntax check.
- Mock Premiere 15.4 build test covering sequence creation, background, BGM, logo and MOGRT Source Text update.
