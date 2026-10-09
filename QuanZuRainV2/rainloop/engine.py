from __future__ import annotations

import hashlib
import json
import math
import os
import random
import shutil
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Iterable, Optional

AUDIO_EXTS = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.wma'}
VIDEO_EXTS = {'.mp4', '.mov', '.mkv', '.m4v', '.avi', '.webm', '.ts'}
HARDWARE_ENCODERS = ('h264_nvenc', 'h264_qsv', 'h264_amf')


def _candidate_bin(name: str) -> Optional[str]:
    here = Path(__file__).resolve().parent.parent
    candidates = [here / name, here / 'ffmpeg' / 'bin' / name, here / 'bin' / name]
    if os.name == 'nt' and not name.lower().endswith('.exe'):
        candidates = [Path(str(p) + '.exe') for p in candidates] + candidates
    for p in candidates:
        if p.exists():
            return str(p)
    return shutil.which(name) or (shutil.which(name + '.exe') if os.name == 'nt' else None)


def find_ffmpeg() -> str:
    p = _candidate_bin('ffmpeg')
    if not p:
        raise FileNotFoundError('Không tìm thấy FFmpeg. Hãy cài FFmpeg hoặc đặt ffmpeg.exe trong thư mục tool.')
    return p


def find_ffprobe() -> str:
    p = _candidate_bin('ffprobe')
    if not p:
        ffmpeg = Path(find_ffmpeg())
        peer = ffmpeg.with_name('ffprobe.exe' if os.name == 'nt' else 'ffprobe')
        if peer.exists():
            return str(peer)
        raise FileNotFoundError('Không tìm thấy ffprobe.')
    return p


def _creationflags() -> int:
    return subprocess.CREATE_NO_WINDOW if os.name == 'nt' and hasattr(subprocess, 'CREATE_NO_WINDOW') else 0


def probe_media(path: str) -> dict:
    cmd = [find_ffprobe(), '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', path]
    cp = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', creationflags=_creationflags())
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or 'ffprobe lỗi')
    data = json.loads(cp.stdout or '{}')
    streams = data.get('streams', [])
    v = next((s for s in streams if s.get('codec_type') == 'video'), None)
    a = next((s for s in streams if s.get('codec_type') == 'audio'), None)
    fmt = data.get('format') or {}
    duration = float(fmt.get('duration') or 0.0)
    if duration <= 0 and v:
        duration = float(v.get('duration') or 0.0)
    return {
        'duration': duration,
        'has_video': bool(v),
        'has_audio': bool(a),
        'width': int((v or {}).get('width') or 0),
        'height': int((v or {}).get('height') or 0),
        'video_codec': (v or {}).get('codec_name') or '',
        'audio_codec': (a or {}).get('codec_name') or '',
        'pix_fmt': (v or {}).get('pix_fmt') or '',
        'avg_frame_rate': (v or {}).get('avg_frame_rate') or '',
    }


def ffmpeg_has_encoder(name: str) -> bool:
    try:
        cp = subprocess.run(
            [find_ffmpeg(), '-hide_banner', '-encoders'],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            creationflags=_creationflags(), timeout=12,
        )
        return name in (cp.stdout or '')
    except Exception:
        return False


def _encoder_probe_args(name: str) -> list[str]:
    if name == 'h264_nvenc':
        return ['-c:v', 'h264_nvenc', '-preset', 'p4', '-cq', '25', '-b:v', '0', '-pix_fmt', 'yuv420p']
    if name == 'h264_qsv':
        return ['-vf', 'format=nv12', '-c:v', 'h264_qsv', '-global_quality', '25']
    if name == 'h264_amf':
        return ['-c:v', 'h264_amf', '-quality', 'speed', '-pix_fmt', 'yuv420p']
    return ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '30', '-pix_fmt', 'yuv420p']


def encoder_runtime_usable(name: str) -> bool:
    if name == 'libx264':
        return ffmpeg_has_encoder('libx264')
    if not ffmpeg_has_encoder(name):
        return False
    try:
        cmd = [
            find_ffmpeg(), '-y', '-hide_banner', '-loglevel', 'error',
            '-f', 'lavfi', '-i', 'color=c=black:s=128x72:r=1',
            '-frames:v', '1', '-an',
        ] + _encoder_probe_args(name) + ['-f', 'null', '-']
        cp = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
            timeout=15, creationflags=_creationflags(),
        )
        return cp.returncode == 0
    except Exception:
        return False


def resolve_encoder(requested: str) -> str:
    requested = (requested or 'auto').lower().strip()
    if requested == 'libx264':
        return 'libx264'
    if requested in HARDWARE_ENCODERS:
        return requested if encoder_runtime_usable(requested) else 'libx264'
    for enc in HARDWARE_ENCODERS:
        if encoder_runtime_usable(enc):
            return enc
    return 'libx264'


def encoder_args(name: str, cfg: 'RenderConfig') -> list[str]:
    if name == 'h264_nvenc':
        return ['-c:v', 'h264_nvenc', '-preset', 'p4', '-cq', str(int(cfg.cq)), '-b:v', '0', '-pix_fmt', 'yuv420p']
    if name == 'h264_qsv':
        return ['-vf', 'format=nv12', '-c:v', 'h264_qsv', '-global_quality', str(int(cfg.cq))]
    if name == 'h264_amf':
        return ['-c:v', 'h264_amf', '-quality', 'speed', '-pix_fmt', 'yuv420p']
    return ['-c:v', 'libx264', '-preset', cfg.preset, '-crf', str(int(cfg.crf)), '-pix_fmt', 'yuv420p']


def choose_audio_source(path_or_folder: str, seed: int, salt: int = 0) -> str:
    if not path_or_folder:
        return ''
    p = Path(path_or_folder)
    if p.is_file():
        return str(p)
    if p.is_dir():
        files = sorted(str(x) for x in p.iterdir() if x.is_file() and x.suffix.lower() in AUDIO_EXTS)
        if not files:
            raise FileNotFoundError(f'Folder không có file âm thanh: {p}')
        r = random.Random(int(seed) + int(salt))
        return r.choice(files)
    raise FileNotFoundError(f'Không tồn tại: {path_or_folder}')


def _fmt(v: float) -> str:
    s = f'{float(v):.6f}'.rstrip('0').rstrip('.')
    return s if s not in {'', '-0'} else '0'


def piecewise_linear_expr(values: Iterable[float], total_seconds: float, var: str = 't') -> str:
    vals = [float(x) for x in values]
    if not vals:
        return '0'
    if len(vals) == 1 or total_seconds <= 0:
        return _fmt(vals[0])
    step = float(total_seconds) / (len(vals) - 1)
    expr = _fmt(vals[-1])
    for i in range(len(vals) - 2, -1, -1):
        t0 = i * step
        t1 = (i + 1) * step
        v0, v1 = vals[i], vals[i + 1]
        seg = f'({_fmt(v0)}+({_fmt(v1-v0)})*(({var}-{_fmt(t0)})/{_fmt(t1-t0)}))'
        expr = f'if(lt({var},{_fmt(t1)}),{seg},{expr})'
    return expr


def curve_value_at(values: Iterable[float], total_seconds: float, t: float) -> float:
    vals = [float(x) for x in values]
    if not vals:
        return 0.0
    if len(vals) == 1 or total_seconds <= 0:
        return vals[0]
    x = max(0.0, min(float(total_seconds), float(t))) / float(total_seconds) * (len(vals) - 1)
    i = min(len(vals) - 2, int(math.floor(x)))
    frac = x - i
    return vals[i] + (vals[i + 1] - vals[i]) * frac


def quantize_value(value: float, step: float) -> float:
    step = max(0.1, float(step))
    q = round(float(value) / step) * step
    return round(q, 4)


def db_volume_expr(db_values: Iterable[float], total_seconds: float) -> str:
    db = piecewise_linear_expr(db_values, total_seconds, 't')
    return f'pow(10,({db})/20)'


def brightness_expr(percent_values: Iterable[float], total_seconds: float) -> str:
    vals = [max(-100.0, min(100.0, float(v))) / 100.0 for v in percent_values]
    return piecewise_linear_expr(vals, total_seconds, 't')


@dataclass
class RenderConfig:
    video_path: str
    output_path: str
    duration_hours: float = 8.0
    rain_source: str = ''
    wave_source: str = ''
    thunder_source: str = ''
    rain_curve_db: list[float] | None = None
    wave_curve_db: list[float] | None = None
    thunder_curve_db: list[float] | None = None
    brightness_curve_pct: list[float] | None = None
    apply_brightness: bool = False
    brightness_mode: str = 'smart_fast'  # smart_fast | full_encode
    brightness_step_pct: float = 1.0
    original_audio_db: float = -6.0
    seed: int = 777
    encoder: str = 'auto'  # auto | h264_nvenc | h264_qsv | h264_amf | libx264
    preset: str = 'veryfast'
    crf: int = 22
    cq: int = 22
    audio_bitrate: str = '192k'
    cache_enabled: bool = True
    block_seconds: float = 60.0

    def __post_init__(self):
        self.rain_curve_db = list(self.rain_curve_db or [-18] * 9)
        self.wave_curve_db = list(self.wave_curve_db or [-24] * 9)
        self.thunder_curve_db = list(self.thunder_curve_db or [-60] * 9)
        self.brightness_curve_pct = list(self.brightness_curve_pct or [0] * 9)

    @property
    def duration_seconds(self) -> float:
        return max(1.0, float(self.duration_hours) * 3600.0)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


@dataclass
class BuildResult:
    command: list[str]
    selected_rain: str
    selected_wave: str
    selected_thunder: str
    video_copy: bool
    encoder_used: str
    mode: str = 'copy'
    variants_encoded: int = 0
    variants_reused: int = 0
    blocks_total: int = 0


def _validate(cfg: RenderConfig) -> tuple[Path, dict, str, str, str]:
    if not cfg.video_path or not Path(cfg.video_path).is_file():
        raise FileNotFoundError('Chưa chọn video nguồn hợp lệ.')
    out = Path(cfg.output_path)
    if not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
    if Path(cfg.video_path).resolve() == out.resolve():
        raise ValueError('File output không được trùng video nguồn.')
    info = probe_media(cfg.video_path)
    if not info['has_video']:
        raise ValueError('File nguồn không có video stream.')
    rain = choose_audio_source(cfg.rain_source, cfg.seed, 101) if cfg.rain_source else ''
    wave = choose_audio_source(cfg.wave_source, cfg.seed, 202) if cfg.wave_source else ''
    thunder = choose_audio_source(cfg.thunder_source, cfg.seed, 303) if cfg.thunder_source else ''
    return out, info, rain, wave, thunder


def _audio_filter_parts(cfg: RenderConfig, info: dict, orig_idx: Optional[int], rain_idx: Optional[int], wave_idx: Optional[int], thunder_idx: Optional[int]) -> tuple[list[str], list[str]]:
    filter_parts: list[str] = []
    audio_labels: list[str] = []
    if info['has_audio'] and orig_idx is not None and float(cfg.original_audio_db) > -90:
        orig_gain = math.pow(10.0, float(cfg.original_audio_db) / 20.0)
        filter_parts.append(f'[{orig_idx}:a:0]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume={_fmt(orig_gain)}[aorig]')
        audio_labels.append('[aorig]')
    if rain_idx is not None:
        r_expr = db_volume_expr(cfg.rain_curve_db, cfg.duration_seconds)
        filter_parts.append(f'[{rain_idx}:a:0]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume=\'{r_expr}\':eval=frame[arain]')
        audio_labels.append('[arain]')
    if wave_idx is not None:
        w_expr = db_volume_expr(cfg.wave_curve_db, cfg.duration_seconds)
        filter_parts.append(f'[{wave_idx}:a:0]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume=\'{w_expr}\':eval=frame[awave]')
        audio_labels.append('[awave]')
    if thunder_idx is not None:
        t_expr = db_volume_expr(cfg.thunder_curve_db, cfg.duration_seconds)
        filter_parts.append(f'[{thunder_idx}:a:0]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume=\'{t_expr}\':eval=frame[athunder]')
        audio_labels.append('[athunder]')
    if audio_labels:
        if len(audio_labels) == 1:
            filter_parts.append(f'{audio_labels[0]}anull[aout]')
        else:
            filter_parts.append(''.join(audio_labels) + f'amix=inputs={len(audio_labels)}:duration=longest:dropout_transition=0:normalize=0,alimiter=limit=0.95[aout]')
    return filter_parts, audio_labels


def _brightness_active(cfg: RenderConfig) -> bool:
    return bool(cfg.apply_brightness and any(abs(float(v)) > 1e-6 for v in cfg.brightness_curve_pct))


def build_command(cfg: RenderConfig, force_encode: bool = False) -> BuildResult:
    out, info, rain, wave, thunder = _validate(cfg)
    ff = find_ffmpeg()
    cmd: list[str] = [ff, '-y', '-hide_banner', '-loglevel', 'warning', '-stream_loop', '-1', '-i', cfg.video_path]
    input_index = 1
    rain_idx = None
    wave_idx = None
    thunder_idx = None
    if rain:
        rain_idx = input_index; input_index += 1
        cmd += ['-stream_loop', '-1', '-i', rain]
    if wave:
        wave_idx = input_index; input_index += 1
        cmd += ['-stream_loop', '-1', '-i', wave]
    if thunder:
        thunder_idx = input_index; input_index += 1
        cmd += ['-stream_loop', '-1', '-i', thunder]

    filter_parts, audio_labels = _audio_filter_parts(cfg, info, 0, rain_idx, wave_idx, thunder_idx)
    brightness_active = _brightness_active(cfg)
    if brightness_active:
        b_expr = brightness_expr(cfg.brightness_curve_pct, cfg.duration_seconds)
        filter_parts.append(f'[0:v:0]eq=brightness=\'{b_expr}\':eval=frame[vout]')
    if filter_parts:
        cmd += ['-filter_complex', ';'.join(filter_parts)]

    video_copy = not brightness_active and not force_encode
    encoder_used = 'copy' if video_copy else resolve_encoder(cfg.encoder)
    cmd += ['-map', '[vout]' if brightness_active else '0:v:0']
    if video_copy:
        cmd += ['-c:v', 'copy']
    else:
        cmd += encoder_args(encoder_used, cfg)
    if audio_labels:
        cmd += ['-map', '[aout]', '-c:a', 'aac', '-b:a', cfg.audio_bitrate]
    else:
        cmd += ['-an']
    cmd += ['-t', _fmt(cfg.duration_seconds), '-max_muxing_queue_size', '4096', '-avoid_negative_ts', 'make_zero', '-progress', 'pipe:1', '-nostats', str(out)]
    return BuildResult(cmd, rain, wave, thunder, video_copy, encoder_used, mode='copy' if video_copy else 'full_encode')


def _cache_root() -> Path:
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA') or os.environ.get('TEMP') or Path.home())
        return base / 'RainLoopWeather' / 'smart_cache'
    return Path(os.environ.get('XDG_CACHE_HOME') or (Path.home() / '.cache')) / 'RainLoopWeather' / 'smart_cache'


def _smart_cache_dir(cfg: RenderConfig, encoder_used: str) -> Path:
    p = Path(cfg.video_path).resolve()
    st = p.stat()
    key_data = '|'.join([
        str(p), str(st.st_size), str(st.st_mtime_ns), encoder_used,
        cfg.preset, str(cfg.crf), str(cfg.cq), str(cfg.block_seconds), 'smart-v3-block',
    ])
    key = hashlib.sha1(key_data.encode('utf-8', 'replace')).hexdigest()[:20]
    d = _cache_root() / key
    d.mkdir(parents=True, exist_ok=True)
    return d


def smart_brightness_schedule(cfg: RenderConfig, source_duration: float) -> tuple[list[float], list[float]]:
    if source_duration <= 0:
        raise ValueError('Không đọc được thời lượng video nguồn để dùng Smart Fast.')
    block = max(source_duration, float(cfg.block_seconds or 60.0))
    count = int(math.ceil(cfg.duration_seconds / block)) + 1
    levels: list[float] = []
    for i in range(count):
        t_mid = min(cfg.duration_seconds, (i + 0.5) * block)
        raw = curve_value_at(cfg.brightness_curve_pct, cfg.duration_seconds, t_mid)
        levels.append(quantize_value(raw, cfg.brightness_step_pct))
    uniq = sorted(set(levels))
    return levels, uniq


def _variant_name(level: float) -> str:
    sign = 'p' if level >= 0 else 'm'
    scaled = int(round(abs(level) * 100))
    return f'b_{sign}{scaled:05d}.mp4'


def _run_ffmpeg_process(
    cmd: list[str],
    total_seconds: float,
    on_progress: Optional[Callable[[float, str], None]],
    should_cancel: Optional[Callable[[], bool]],
    process_holder: Optional[dict],
    base_pct: float = 0.0,
    span_pct: float = 100.0,
    label: str = '',
) -> tuple[bool, str, str]:
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace', bufsize=1,
        creationflags=_creationflags(),
    )
    if process_holder is not None:
        process_holder['process'] = p
    logs: list[str] = []
    total_us = max(1.0, float(total_seconds)) * 1_000_000.0
    if p.stdout:
        for raw in p.stdout:
            line = raw.strip()
            if line:
                logs.append(line)
                if len(logs) > 250:
                    logs = logs[-250:]
            if should_cancel and should_cancel():
                try:
                    p.terminate()
                except Exception:
                    pass
                return False, 'Đã hủy render.', 'cancel'
            if line.startswith('out_time_us='):
                try:
                    us = float(line.split('=', 1)[1])
                    frac = max(0.0, min(1.0, us / total_us))
                    pct = base_pct + frac * span_pct
                    if on_progress:
                        txt = f'{label} {pct:5.1f}%'.strip()
                        on_progress(pct, txt)
                except Exception:
                    pass
    rc = p.wait()
    if rc == 0:
        return True, 'Hoàn tất.', 'ok'
    return False, '\n'.join(logs[-80:])[-7000:] or f'FFmpeg exit code {rc}', 'error'


def _variant_command(cfg: RenderConfig, level: float, dest: Path, encoder_used: str) -> list[str]:
    ff = find_ffmpeg()
    brightness = max(-1.0, min(1.0, float(level) / 100.0))
    cmd = [
        ff, '-y', '-hide_banner', '-loglevel', 'warning',
        '-i', cfg.video_path,
        '-map', '0:v:0', '-an',
        '-vf', f'eq=brightness={_fmt(brightness)}',
    ]
    cmd += encoder_args(encoder_used, cfg)
    cmd += ['-max_muxing_queue_size', '4096', '-progress', 'pipe:1', '-nostats', str(dest)]
    return cmd


def _block_name(level: float, block_seconds: float) -> str:
    sign = 'p' if level >= 0 else 'm'
    scaled = int(round(abs(level) * 100))
    sec = int(round(block_seconds))
    return f'block_{sec:04d}s_{sign}{scaled:05d}.mp4'


def _block_command(cfg: RenderConfig, variant: Path, dest: Path) -> list[str]:
    ff = find_ffmpeg()
    block = max(1.0, float(cfg.block_seconds or 60.0))
    return [
        ff, '-y', '-hide_banner', '-loglevel', 'warning',
        '-stream_loop', '-1', '-i', str(variant),
        '-map', '0:v:0', '-an', '-c:v', 'copy',
        '-t', _fmt(block), '-avoid_negative_ts', 'make_zero',
        '-progress', 'pipe:1', '-nostats', str(dest),
    ]


def _smart_final_command(cfg: RenderConfig, manifest: Path, info: dict, rain: str, wave: str, thunder: str) -> list[str]:
    ff = find_ffmpeg()
    cmd: list[str] = [ff, '-y', '-hide_banner', '-loglevel', 'warning', '-f', 'concat', '-safe', '0', '-i', str(manifest)]
    input_index = 1
    orig_idx = None
    rain_idx = None
    wave_idx = None
    thunder_idx = None
    if info['has_audio']:
        orig_idx = input_index; input_index += 1
        cmd += ['-stream_loop', '-1', '-i', cfg.video_path]
    if rain:
        rain_idx = input_index; input_index += 1
        cmd += ['-stream_loop', '-1', '-i', rain]
    if wave:
        wave_idx = input_index; input_index += 1
        cmd += ['-stream_loop', '-1', '-i', wave]
    if thunder:
        thunder_idx = input_index; input_index += 1
        cmd += ['-stream_loop', '-1', '-i', thunder]
    filter_parts, audio_labels = _audio_filter_parts(cfg, info, orig_idx, rain_idx, wave_idx, thunder_idx)
    if filter_parts:
        cmd += ['-filter_complex', ';'.join(filter_parts)]
    cmd += ['-map', '0:v:0', '-c:v', 'copy']
    if audio_labels:
        cmd += ['-map', '[aout]', '-c:a', 'aac', '-b:a', cfg.audio_bitrate]
    else:
        cmd += ['-an']
    cmd += [
        '-t', _fmt(cfg.duration_seconds),
        '-max_muxing_queue_size', '4096',
        '-avoid_negative_ts', 'make_zero',
        '-progress', 'pipe:1', '-nostats',
        cfg.output_path,
    ]
    return cmd


def run_smart_fast(
    cfg: RenderConfig,
    on_progress: Optional[Callable[[float, str], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
    process_holder: Optional[dict] = None,
) -> tuple[bool, str, BuildResult]:
    out, info, rain, wave, thunder = _validate(cfg)
    source_duration = float(info.get('duration') or 0.0)
    if source_duration <= 0.05:
        raise ValueError('Không đọc được thời lượng video nguồn. Hãy dùng Full Encode.')

    levels, unique_levels = smart_brightness_schedule(cfg, source_duration)
    if len(unique_levels) == 1 and abs(unique_levels[0]) < 1e-9:
        # Curve quantizes to zero: use true stream-copy path.
        cfg2 = RenderConfig(**asdict(cfg))
        cfg2.apply_brightness = False
        return run_render(cfg2, on_progress, should_cancel, process_holder)

    encoder_used = resolve_encoder(cfg.encoder)
    cache_dir = _smart_cache_dir(cfg, encoder_used)
    manifest = cache_dir / 'current_manifest.txt'
    encoded = 0
    reused = 0

    total_unique = max(1, len(unique_levels))
    for idx, level in enumerate(unique_levels):
        dest = cache_dir / _variant_name(level)
        valid_cache = cfg.cache_enabled and dest.exists() and dest.stat().st_size > 4096
        if valid_cache:
            reused += 1
            if on_progress:
                on_progress((idx + 1) / total_unique * 38.0, f'Cache sáng {idx+1}/{total_unique} • {level:+g}%')
            continue
        tmp = dest.with_suffix('.tmp.mp4')
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        cmd = _variant_command(cfg, level, tmp, encoder_used)
        base = idx / total_unique * 38.0
        span = 38.0 / total_unique
        ok, msg, kind = _run_ffmpeg_process(
            cmd, source_duration, on_progress, should_cancel, process_holder,
            base_pct=base, span_pct=span,
            label=f'Mã hóa mức sáng {idx+1}/{total_unique} ({level:+g}%)',
        )
        if not ok:
            try:
                if tmp.exists(): tmp.unlink()
            except Exception:
                pass
            built = BuildResult(cmd, rain, wave, thunder, False, encoder_used, mode='smart_fast', variants_encoded=encoded, variants_reused=reused, blocks_total=len(levels))
            return False, msg, built
        tmp.replace(dest)
        encoded += 1

    # Build short stream-copy blocks so the final concat opens hundreds of files, not thousands.
    block_sec = max(source_duration, float(cfg.block_seconds or 60.0))
    for idx, level in enumerate(unique_levels):
        variant = cache_dir / _variant_name(level)
        block_file = cache_dir / _block_name(level, block_sec)
        valid_block = cfg.cache_enabled and block_file.exists() and block_file.stat().st_size > 4096
        if valid_block:
            continue
        tmp_block = block_file.with_suffix('.tmp.mp4')
        try:
            if tmp_block.exists(): tmp_block.unlink()
        except Exception:
            pass
        cmd_block = _block_command(cfg, variant, tmp_block)
        ok, msg, kind = _run_ffmpeg_process(
            cmd_block, block_sec, on_progress, should_cancel, process_holder,
            base_pct=38.0 + (idx / total_unique) * 12.0, span_pct=12.0 / total_unique,
            label=f'Tạo block FAST {idx+1}/{total_unique} ({level:+g}%)',
        )
        if not ok:
            try:
                if tmp_block.exists(): tmp_block.unlink()
            except Exception:
                pass
            built = BuildResult(cmd_block, rain, wave, thunder, False, encoder_used, mode='smart_fast', variants_encoded=encoded, variants_reused=reused, blocks_total=len(levels))
            return False, msg, built
        tmp_block.replace(block_file)

    # Manifest contains ~duration/block_seconds entries (e.g. 480 for 8h at 60s), not 3000+ 9s clips.
    lines = [f"file '{_block_name(level, block_sec)}'" for level in levels]
    manifest.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    cmd = _smart_final_command(cfg, manifest, info, rain, wave, thunder)
    ok, msg, _ = _run_ffmpeg_process(
        cmd, cfg.duration_seconds, on_progress, should_cancel, process_holder,
        base_pct=50.0, span_pct=50.0, label='Ghép FAST 8–12h + 3 lớp âm thanh',
    )
    built = BuildResult(cmd, rain, wave, thunder, False, encoder_used, mode='smart_fast', variants_encoded=encoded, variants_reused=reused, blocks_total=len(levels))
    if ok and out.exists() and out.stat().st_size > 1024:
        return True, f'Hoàn tất Smart Fast. Mã hóa {encoded} mức sáng, dùng cache {reused} mức, ghép {len(levels)} block.', built
    if ok:
        return False, 'FFmpeg kết thúc nhưng file output không hợp lệ.', built
    return False, msg, built


def run_render(
    cfg: RenderConfig,
    on_progress: Optional[Callable[[float, str], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
    process_holder: Optional[dict] = None,
) -> tuple[bool, str, BuildResult]:
    if _brightness_active(cfg) and cfg.brightness_mode == 'smart_fast':
        return run_smart_fast(cfg, on_progress, should_cancel, process_holder)

    def _run(force_encode: bool = False):
        built = build_command(cfg, force_encode=force_encode)
        ok, msg, kind = _run_ffmpeg_process(
            built.command, cfg.duration_seconds, on_progress, should_cancel, process_holder,
            base_pct=0.0, span_pct=100.0, label='Render',
        )
        if ok and Path(cfg.output_path).exists() and Path(cfg.output_path).stat().st_size > 1024:
            return True, 'Hoàn tất.', built, 'ok'
        return False, msg, built, kind

    ok, msg, built, kind = _run(False)
    if not ok and kind == 'error' and built.video_copy and cfg.encoder == 'auto':
        try:
            if Path(cfg.output_path).exists():
                Path(cfg.output_path).unlink()
        except Exception:
            pass
        if on_progress:
            on_progress(0.0, 'Copy lỗi → tự chuyển sang encode H.264…')
        ok, msg2, built2, _ = _run(True)
        if ok:
            return True, 'Hoàn tất (fallback encode H.264).', built2
        return False, msg2, built2
    return ok, msg, built