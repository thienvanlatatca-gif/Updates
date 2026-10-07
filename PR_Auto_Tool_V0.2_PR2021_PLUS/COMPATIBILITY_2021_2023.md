# Premiere compatibility matrix

| Premiere | App version | Bridge | Status |
|---|---:|---|---|
| Premiere Pro 2021 | 15.x | CEP + ExtendScript | Supported |
| Premiere Pro 2022 | 22.x | CEP + ExtendScript | Supported |
| Premiere Pro 2023 | 23.x | CEP + ExtendScript | Supported |
| Premiere Pro 2024+ | 24.x+ | CEP legacy path | Expected; real-host test recommended |

The extension host range is `[15.0,99.9]`. Core automation avoids UXP-only APIs, so Premiere 23.x follows the same code path as 15.x.

The critical Text Template path uses `Sequence.importMGT()` plus `TrackItem.getMGTComponent()`, which is the same CEP/ExtendScript approach used by Adobe's PProPanel sample.
