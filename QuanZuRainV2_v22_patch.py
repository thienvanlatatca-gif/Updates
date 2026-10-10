from __future__ import annotations

import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'src')


def replace_once(path: Path, old: str, new: str) -> None:
    s = path.read_text(encoding='utf-8')
    if old not in s:
        raise SystemExit(f'Patch marker not found in {path}: {old[:100]!r}')
    path.write_text(s.replace(old, new, 1), encoding='utf-8')


def ensure_replace(path: Path, old: str, new: str) -> None:
    s = path.read_text(encoding='utf-8')
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'Patch marker not found in {path}: {old[:100]!r}')
    path.write_text(s.replace(old, new), encoding='utf-8')

test = root / 'tests' / 'test_engine.py'
ensure_replace(
    test,
    "self.assertEqual(str(Path(p).parent), '/tmp/render out')",
    "self.assertEqual(Path(p).parent, Path('/tmp/render out'))",
)

app = root / 'app.py'
ensure_replace(app, "APP_TITLE = 'QUANZU RAIN V2.1 FAST — FFmpeg 8–12H'", "APP_TITLE = 'QUANZU RAIN V2.2 FAST — FFmpeg 8–12H'")
ensure_replace(app, "ttk.Label(top, text='QUANZU RAIN V2.1 FAST'", "ttk.Label(top, text='QUANZU RAIN V2.2 FAST'")
ensure_replace(
    app,
    "self.v_fps = tk.StringVar(value='24')\n        self.v_block_seconds",
    "self.v_fps = tk.StringVar(value='24')\n        self.v_video_bitrate = tk.IntVar(value=3600)\n        self.v_block_seconds",
)
old_ui = """        cb_res.bind('<<ComboboxSelected>>',lambda _e:self._update_output_preview()); cb_fps.bind('<<ComboboxSelected>>',lambda _e:self._update_output_preview())
        ttk.Label(cfg,text='FAST V2.1: mặc định chỉ encode clip nguồn ngắn thành cache 1080p/24 một lần rồi loop COPY 8–12h. Tránh việc lặp nguyên bitrate 4K rất lớn.',foreground='#1f6f43').grid(row=4,column=0,columnspan=9,sticky='w',pady=(10,0))
        ttk.Label(cfg,text='Tool kiểm tra dung lượng trước giai đoạn ghi dài; nếu hết ổ đĩa sẽ dừng sớm và xóa file dang dở. Auto thử NVENC → QSV → AMF → CPU.',foreground='#5d6d7e').grid(row=5,column=0,columnspan=9,sticky='w',pady=(4,0))
"""
new_ui = """        cb_res.bind('<<ComboboxSelected>>',lambda _e:self._update_output_preview()); cb_fps.bind('<<ComboboxSelected>>',lambda _e:self._update_output_preview())
        ttk.Label(cfg,text='Bitrate video:').grid(row=4,column=0,sticky='w',pady=(10,0))
        sp_br=ttk.Spinbox(cfg,from_=0,to=50000,increment=100,textvariable=self.v_video_bitrate,width=9,command=self._update_output_preview); sp_br.grid(row=4,column=1,pady=(10,0),sticky='w')
        sp_br.bind('<FocusOut>',lambda _e:self._update_output_preview()); sp_br.bind('<Return>',lambda _e:self._update_output_preview())
        ttk.Label(cfg,text='kbps   •   3600 ≈ 16–18 GB / 10h   •   0 = dùng CRF/CQ',foreground='#8a5a00').grid(row=4,column=2,columnspan=7,sticky='w',pady=(10,0))
        ttk.Label(cfg,text='FAST V2.2: mặc định encode clip nguồn ngắn 1080p/24 ở bitrate đã chọn một lần, sau đó loop COPY 8–12h. Bitrate 3600k phù hợp mục tiêu ~16–18 GB/10h.',foreground='#1f6f43').grid(row=5,column=0,columnspan=9,sticky='w',pady=(10,0))
        ttk.Label(cfg,text='Bitrate chỉ làm giảm dung lượng khi video được encode (Chuẩn hóa FAST / độ sáng / full encode). Nếu COPY nguyên nguồn thì bitrate nguồn được giữ nguyên.',foreground='#5d6d7e').grid(row=6,column=0,columnspan=9,sticky='w',pady=(4,0))
"""
ensure_replace(app, old_ui, new_ui)
ensure_replace(
    app,
    'self.v_storage_info.set(f"Chuẩn hóa FAST {self.v_resolution.get()}/{self.v_fps.get()}fps: tool sẽ đo bitrate cache thật và kiểm tra ổ đĩa trước khi ghi 8–12h.")',
    'self.v_storage_info.set(f"Chuẩn hóa FAST {self.v_resolution.get()}/{self.v_fps.get()}fps • bitrate {int(self.v_video_bitrate.get())} kbps: ước tính theo bitrate mục tiêu và kiểm tra ổ đĩa trước khi ghi 8–12h.")',
)
ensure_replace(
    app,
    "normalize_fast=bool(self.v_normalize_fast.get()), output_resolution=self.v_resolution.get(), output_fps=self.v_fps.get(),",
    "normalize_fast=bool(self.v_normalize_fast.get()), output_resolution=self.v_resolution.get(), output_fps=self.v_fps.get(), video_bitrate_kbps=int(self.v_video_bitrate.get()),",
)
ensure_replace(
    app,
    "self.v_normalize_fast.set(d.get('normalize_fast',True)); self.v_resolution.set(d.get('output_resolution','1080p')); self.v_fps.set(d.get('output_fps','24')); self.v_block_seconds",
    "self.v_normalize_fast.set(d.get('normalize_fast',True)); self.v_resolution.set(d.get('output_resolution','1080p')); self.v_fps.set(d.get('output_fps','24')); self.v_video_bitrate.set(d.get('video_bitrate_kbps',3600)); self.v_block_seconds",
)

engine = root / 'rainloop' / 'engine.py'
old_encoder = """def encoder_args(name: str, cfg: 'RenderConfig') -> list[str]:
    if name == 'h264_nvenc':
        return ['-c:v', 'h264_nvenc', '-preset', 'p4', '-cq', str(int(cfg.cq)), '-b:v', '0', '-pix_fmt', 'yuv420p']
    if name == 'h264_qsv':
        return ['-c:v', 'h264_qsv', '-global_quality', str(int(cfg.cq)), '-pix_fmt', 'nv12']
    if name == 'h264_amf':
        return ['-c:v', 'h264_amf', '-quality', 'speed', '-pix_fmt', 'yuv420p']
    return ['-c:v', 'libx264', '-preset', cfg.preset, '-crf', str(int(cfg.crf)), '-pix_fmt', 'yuv420p']
"""
new_encoder = """def _target_bitrate_args(cfg: 'RenderConfig') -> list[str]:
    kbps = max(0, int(getattr(cfg, 'video_bitrate_kbps', 0) or 0))
    if kbps <= 0:
        return []
    max_kbps = max(kbps, int(round(kbps * 1.15)))
    buf_kbps = max(kbps * 2, max_kbps)
    return ['-b:v', f'{kbps}k', '-maxrate', f'{max_kbps}k', '-bufsize', f'{buf_kbps}k']


def encoder_args(name: str, cfg: 'RenderConfig') -> list[str]:
    rate = _target_bitrate_args(cfg)
    if name == 'h264_nvenc':
        if rate:
            return ['-c:v', 'h264_nvenc', '-preset', 'p4'] + rate + ['-pix_fmt', 'yuv420p']
        return ['-c:v', 'h264_nvenc', '-preset', 'p4', '-cq', str(int(cfg.cq)), '-b:v', '0', '-pix_fmt', 'yuv420p']
    if name == 'h264_qsv':
        if rate:
            return ['-c:v', 'h264_qsv'] + rate + ['-pix_fmt', 'nv12']
        return ['-c:v', 'h264_qsv', '-global_quality', str(int(cfg.cq)), '-pix_fmt', 'nv12']
    if name == 'h264_amf':
        if rate:
            return ['-c:v', 'h264_amf', '-quality', 'speed'] + rate + ['-pix_fmt', 'yuv420p']
        return ['-c:v', 'h264_amf', '-quality', 'speed', '-pix_fmt', 'yuv420p']
    if rate:
        return ['-c:v', 'libx264', '-preset', cfg.preset] + rate + ['-pix_fmt', 'yuv420p']
    return ['-c:v', 'libx264', '-preset', cfg.preset, '-crf', str(int(cfg.crf)), '-pix_fmt', 'yuv420p']
"""
ensure_replace(engine, old_encoder, new_encoder)
ensure_replace(
    engine,
    "    output_fps: str = '24'  # keep | 24 | 30 | 60\n    original_audio_db",
    "    output_fps: str = '24'  # keep | 24 | 30 | 60\n    video_bitrate_kbps: int = 3600  # 0 = quality mode (CRF/CQ); 3600 ~= 16–18 GB/10h with 192k audio\n    original_audio_db",
)
old_est = """def estimate_output_size_bytes(cfg: 'RenderConfig', media_info: Optional[dict] = None) -> int:
    info = media_info or probe_media(cfg.video_path)
    video_bps = _media_video_rate_bps(info)
    has_any_audio = bool(info.get('has_audio') and float(cfg.original_audio_db) > -90) or bool(cfg.rain_source or cfg.wave_source or cfg.thunder_source)
    audio_bps = _parse_bitrate(cfg.audio_bitrate) if has_any_audio else 0
    raw = (video_bps + audio_bps) * cfg.duration_seconds / 8.0
    return int(raw * 1.06)
"""
new_est = """def estimate_output_size_bytes(cfg: 'RenderConfig', media_info: Optional[dict] = None) -> int:
    info = media_info or probe_media(cfg.video_path)
    target_kbps = max(0, int(getattr(cfg, 'video_bitrate_kbps', 0) or 0))
    will_encode_video = bool(cfg.normalize_fast or cfg.apply_brightness)
    if target_kbps > 0 and will_encode_video:
        video_bps = target_kbps * 1000.0
    else:
        video_bps = _media_video_rate_bps(info)
    has_any_audio = bool(info.get('has_audio') and float(cfg.original_audio_db) > -90) or bool(cfg.rain_source or cfg.wave_source or cfg.thunder_source)
    audio_bps = _parse_bitrate(cfg.audio_bitrate) if has_any_audio else 0
    raw = (video_bps + audio_bps) * cfg.duration_seconds / 8.0
    return int(raw * 1.06)
"""
ensure_replace(engine, old_est, new_est)
ensure_replace(
    engine,
    "cfg.preset, str(cfg.crf), str(cfg.cq), str(cfg.block_seconds), str(cfg.output_resolution), str(cfg.output_fps), 'smart-v4-block',",
    "cfg.preset, str(cfg.crf), str(cfg.cq), str(cfg.video_bitrate_kbps), str(cfg.block_seconds), str(cfg.output_resolution), str(cfg.output_fps), 'smart-v5-bitrate-block',",
)
ensure_replace(
    engine,
    "cfg.preset, str(cfg.crf), str(cfg.cq), str(cfg.output_resolution), str(cfg.output_fps),\n        'normalized-fast-v1',",
    "cfg.preset, str(cfg.crf), str(cfg.cq), str(cfg.video_bitrate_kbps), str(cfg.output_resolution), str(cfg.output_fps),\n        'normalized-fast-v2-bitrate',",
)

s = test.read_text(encoding='utf-8')
if 'encoder_args' not in s:
    ensure_replace(test, '    estimate_output_size_bytes, output_storage_report,\n)', '    estimate_output_size_bytes, output_storage_report, encoder_args,\n)')
ensure_replace(
    test,
    "cfg = RenderConfig('a', '/tmp/out.mp4', duration_hours=1, rain_source='rain')",
    "cfg = RenderConfig('a', '/tmp/out.mp4', duration_hours=1, rain_source='rain', normalize_fast=False, video_bitrate_kbps=0)",
)
s = test.read_text(encoding='utf-8')
if 'def test_target_bitrate_encoder_args' not in s:
    insert = """
    def test_target_bitrate_encoder_args(self):
        c = RenderConfig('a', 'b', video_bitrate_kbps=3600)
        args = encoder_args('libx264', c)
        self.assertIn('-b:v', args)
        self.assertIn('3600k', args)
        self.assertNotIn('-crf', args)

    def test_zero_bitrate_keeps_crf_mode(self):
        c = RenderConfig('a', 'b', video_bitrate_kbps=0, crf=22)
        args = encoder_args('libx264', c)
        self.assertIn('-crf', args)
        self.assertNotIn('3600k', args)

    def test_10h_3600k_targets_about_16_to_18_gib(self):
        c = RenderConfig('a', 'b', duration_hours=10, normalize_fast=True, video_bitrate_kbps=3600, audio_bitrate='192k')
        info = {
            'duration': 9.2, 'has_audio': True,
            'video_bitrate': 34_000_000, 'audio_bitrate': 192_000,
            'format_bitrate': 34_192_000, 'source_size': 40_000_000,
        }
        size = estimate_output_size_bytes(c, info)
        gib = size / (1024 ** 3)
        self.assertGreaterEqual(gib, 16.0)
        self.assertLessEqual(gib, 18.0)
"""
    marker = "\n\nif __name__ == '__main__':"
    if marker not in s:
        raise SystemExit('Could not find test insertion marker')
    test.write_text(s.replace(marker, '\n' + insert + marker, 1), encoding='utf-8')

readme = root / 'README.md'
ensure_replace(readme, '# QuanZu Rain V2.1 FAST', '# QuanZu Rain V2.2 FAST')
s = readme.read_text(encoding='utf-8')
if '## V2.2 — hạ bitrate' not in s:
    section = """
## V2.2 — hạ bitrate để file 10 giờ còn khoảng 16–18 GB
- Thêm dòng **Bitrate video (kbps)** trong phần chất lượng, mặc định **3600 kbps**.
- Với video 10 giờ và AAC 192k, 3600 kbps cho mức mục tiêu khoảng **16–18 GiB/GB hiển thị trên Windows**; kích thước thực tế có thể dao động nhẹ theo encoder và container.
- Nhập `0` để tắt ép bitrate và quay về CRF/CQ.
- Bitrate được áp dụng khi video có encode: **Chuẩn hóa FAST**, Smart Brightness hoặc Full Encode. Nếu COPY nguyên video nguồn thì bitrate không thể giảm vì không encode lại.
- Đổi bitrate tạo **cache mới**; tool không dùng nhầm cache cũ ở bitrate khác.

"""
    marker = '## V2.1 sửa các lỗi thực tế'
    if marker not in s:
        raise SystemExit('README marker not found')
    readme.write_text(s.replace(marker, section + marker, 1), encoding='utf-8')

(root / 'rainloop' / '__init__.py').write_text("__version__ = '2.2.0'\n", encoding='utf-8')
print('QuanZu Rain V2.2 patch applied successfully')
