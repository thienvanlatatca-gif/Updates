from __future__ import annotations

import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'src')


def replace_once(path: Path, old: str, new: str) -> None:
    s = path.read_text(encoding='utf-8')
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'Patch marker not found in {path}: {old[:120]!r}')
    path.write_text(s.replace(old, new, 1), encoding='utf-8')


eng = root / 'rainloop' / 'engine.py'
old_encoder = """def _turbo_audio_encoder(cfg: RenderConfig) -> tuple[str, list[str], str]:
    requested = str(getattr(cfg, 'turbo_audio_codec', 'opus') or 'opus').lower().strip()
    if requested == 'opus' and ffmpeg_has_encoder('libopus'):
        # Opus is dramatically faster than native AAC in FFmpeg and is an official
        # YouTube recommended upload codec. compression_level=0 favors speed; at
        # 192k stereo it is still ample for rain/wave ambience.
        return 'opus', ['-c:a', 'libopus', '-b:a', cfg.audio_bitrate, '-compression_level', '0', '-application', 'audio'], '.mp4'
    return 'aac', ['-c:a', 'aac', '-b:a', cfg.audio_bitrate], '.m4a'
"""
new_encoder = """def _turbo_audio_encoder(cfg: RenderConfig) -> tuple[str, list[str], str]:
    # V2.4.1 AUDIO FIX: Always use AAC for MP4 output compatibility.
    # Opus-in-MP4 is valid in FFmpeg, but several Windows playback stacks/editors
    # can show the video while producing no audible sound. Chunked AAC is still
    # rendered in parallel by TURBO, so we keep the speed advantage without the
    # compatibility risk. Old autosaves that still say 'opus' are intentionally
    # migrated here by ignoring that legacy value.
    return 'aac', ['-c:a', 'aac', '-b:a', cfg.audio_bitrate], '.m4a'
"""
replace_once(eng, old_encoder, new_encoder)
replace_once(
    eng,
    "str(cfg.turbo_audio_chunk_seconds), str(cfg.turbo_audio_codec), 'turbo-audio-v2-opus',",
    "str(cfg.turbo_audio_chunk_seconds), 'aac', 'turbo-audio-v3-aac-compat',",
)
replace_once(
    eng,
    "turbo_audio_codec: str = 'opus'  # opus (YouTube recommended) | aac",
    "turbo_audio_codec: str = 'aac'  # V2.4.1: AAC forced for MP4/Windows compatibility",
)

app = root / 'app.py'
replace_once(app, "APP_TITLE = 'QUANZU RAIN V2.4 BATCH TURBO — FFmpeg 8–12H'", "APP_TITLE = 'QUANZU RAIN V2.4.1 BATCH TURBO AUDIO FIX — FFmpeg 8–12H'")
replace_once(app, "self.v_turbo_audio_codec = tk.StringVar(value='opus')", "self.v_turbo_audio_codec = tk.StringVar(value='aac')")
replace_once(app, "values=['opus','aac']", "values=['aac']")
replace_once(app, "Opus = nhanh nhất + YouTube hỗ trợ", "AAC – tương thích MP4 / Windows / YouTube")
replace_once(app, "self.v_turbo_audio_codec.set(d.get('turbo_audio_codec','opus'))", "self.v_turbo_audio_codec.set('aac')")
replace_once(app, "turbo_audio_codec=self.v_turbo_audio_codec.get(),", "turbo_audio_codec='aac',")
replace_once(
    app,
    "V2.4 BATCH: chọn nhiều video → render tuần tự. Mỗi video có thể tự random +1 đến +15 phút; nguồn âm thanh và mọi lựa chọn tự lưu khi đóng/mở tool.",
    "V2.4.1 AUDIO FIX: batch + random phút + autosave; TURBO audio luôn xuất AAC để tránh video có hình nhưng không nghe tiếng trên Windows/player.",
)
replace_once(app, "Render lỗi — QuanZu Rain V2.4", "Render lỗi — QuanZu Rain V2.4.1")

(root / 'rainloop' / '__init__.py').write_text("__version__ = '2.4.1'\n", encoding='utf-8')

p = root / 'tests' / 'test_engine.py'
replace_once(p, "self.assertEqual(c.turbo_audio_codec, 'opus')", "self.assertEqual(c.turbo_audio_codec, 'aac')")

p = root / 'tests' / 'test_integration_ffmpeg.py'
s = p.read_text(encoding='utf-8')
s = s.replace("self.assertIn(info['audio_codec'], {'opus','aac'})", "self.assertEqual(info['audio_codec'], 'aac')")
if 'def test_legacy_opus_setting_is_migrated_to_aac' not in s:
    marker = "\n\nif __name__ == '__main__':"
    if marker not in s:
        raise SystemExit('Integration test insertion marker not found')
    extra = '''\n\n    def test_legacy_opus_setting_is_migrated_to_aac(self):\n        out = self.root / 'legacy_opus.mp4'\n        cfg = self._base_cfg(out)\n        cfg.turbo_audio_codec = 'opus'  # simulate old V2.3/V2.4 autosave\n        cfg.normalize_fast = True\n        ok, msg, built = run_render(cfg)\n        self.assertTrue(ok, msg)\n        info = probe_media(str(out))\n        self.assertEqual(info['audio_codec'], 'aac')\n        cp = subprocess.run([FFMPEG, '-v', 'error', '-i', str(out), '-map', '0:a:0', '-t', '1', '-f', 'null', '-'], capture_output=True, text=True)\n        self.assertEqual(cp.returncode, 0, cp.stderr)\n'''
    s = s.replace(marker, extra + marker, 1)
p.write_text(s, encoding='utf-8')

rd = root / 'README.md'
s = rd.read_text(encoding='utf-8')
s = s.replace('# QuanZu Rain V2.4 BATCH TURBO', '# QuanZu Rain V2.4.1 BATCH TURBO AUDIO FIX', 1)
if '## V2.4.1 AUDIO FIX' not in s:
    section = '''\n## V2.4.1 AUDIO FIX\n- Sửa trường hợp video render xong có hình nhưng một số player Windows không phát tiếng do Opus nằm trong MP4.\n- TURBO audio giờ **luôn xuất AAC** (M4A trung gian, AAC trong MP4 cuối) để tương thích Windows/YouTube/editor tốt hơn.\n- Cache audio đổi version, nên bản này không tái sử dụng cache Opus cũ.\n- Project/autosave cũ đang lưu `opus` sẽ tự được engine chuyển sang AAC, không cần xóa cấu hình.\n- Vẫn giữ batch nhiều video, autosave và random +1–15 phút/video.\n\n'''
    pos = s.find('\n## ')
    s = (s[:pos] + section + s[pos:]) if pos >= 0 else (s + section)
rd.write_text(s, encoding='utf-8')

print('QuanZu Rain V2.4.1 AUDIO FIX patch applied')
