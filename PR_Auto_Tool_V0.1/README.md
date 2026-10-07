# PR Auto Tool V0.1

Premiere Pro automation tool modeled after the existing CapCut Auto V3.10 workflow.

## Architecture

- **Windows controller (Python/Tkinter)**: YouTube/local media intake, yt-dlp download, SRT/word-timing discovery, background/BGM/logo/voice settings, Text Template selection, and generation of `latest_job.json`.
- **Premiere UXP Bridge (Premiere Pro 25.6+)**: imports media, creates/uses a sequence, inserts background/BGM/logo, and applies MOGRT text templates at timestamped text events.
- **Bridge folder**: `%APPDATA%\PR_Auto_Tool_V01\bridge`.

## Text Templates

V0.1 defines 10 CapCut-style template slots:

1. Kick Fall
2. Double Headline
3. Cartoon Dust
4. Colorful Splash
5. Two-line Trail
6. Luminescent
7. Quick Bold
8. Film Glitch
9. Animated Cluster
10. Colorful Glitch

The tool does not redistribute third-party MOGRT binaries. Each slot can be mapped to a local `.mogrt` file using a persistent UXP filesystem token. The bridge uses Premiere's official `SequenceEditor.insertMogrtFromPath()` API and attempts to update the first exposed string parameter in Essential Graphics.

## V0.1 workflow

1. Paste YouTube URL or select a local video.
2. Prepare subtitle/word timing.
3. Choose background, BGM, logo, voice folder, and text template.
4. Desktop controller writes `latest_job.json`.
5. In Premiere, open **PR Auto Bridge** and run **Build latest job**.

## Current scope

Implemented foundation: downloader integration, job schema/history, sequence creation, media import, background/BGM/logo basic insertion, voice import, MOGRT mapping, timestamped Text FX, and marker fallback.

Next work: exact audio gain automation, richer motion/layout controls, native caption styling, transitions, template preview video, and one-click bridge triggering.
