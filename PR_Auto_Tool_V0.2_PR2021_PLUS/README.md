# PR Auto Tool V0.3 — Premiere Pro 2021 / 2022 / 2023+

The bridge is **CEP + ExtendScript**, not UXP-only, so the same tool targets:

- Premiere Pro 2021 / 15.x
- Premiere Pro 2022 / 22.x
- Premiere Pro 2023 / 23.x
- newer CEP-capable Premiere builds

The manifest host range stays `PPRO [15.0,99.9]`. The required CSXS runtime is lowered to `6.0` for broad backward/forward CEP compatibility.

## Core Premiere APIs

- `app.project.importFiles()`
- `app.project.createNewSequenceFromClips()`
- `Sequence.overwriteClip()`
- `Sequence.importMGT()`
- `TrackItem.getMGTComponent()`
- guarded QE `addTracks()` fallback

## Installation

The extension is installed to:

`%APPDATA%\Adobe\CEP\extensions\PR_Auto_Bridge_2021_Plus`

The installer enables PlayerDebugMode across CSXS generations used by Premiere 2021 and Premiere 2023.

Open the panel from:

- Premiere 2021: `Window > Extensions > PR Auto Bridge 2021-2023+`
- Premiere 2023: `Window > Extensions` or `Window > Extensions (Legacy)`

No UXP Developer Tool is required.

## Validation

The compatibility suite now executes the same CEP/ExtendScript build flow against mocked Premiere versions:

- 15.4.1 (Premiere 2021)
- 23.6.0 (Premiere 2023)

Both exercise sequence creation, background, BGM, logo, MOGRT insertion and Source Text update.

Note: plugin compatibility and MOGRT compatibility are separate. A MOGRT authored with newer-only AE/Premiere features can still fail in Premiere 2021 while working in Premiere 2023.
