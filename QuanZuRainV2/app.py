from __future__ import annotations

import json
import os
import random
import threading
import time
from dataclasses import asdict
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from rainloop.engine import RenderConfig, probe_media, run_render, find_ffmpeg

APP_TITLE = 'QUANZU RAIN V2 FAST — FFmpeg 8–12H'
POINTS = 9

PRESETS = {
    'Sleep': {
        'rain': [-19, -18, -17, -18, -20, -19, -18, -18, -19],
        'wave': [-25, -23, -26, -27, -27, -24, -23, -22, -22],
        'thunder': [-60, -60, -52, -60, -60, -56, -60, -60, -60],
        'bright': [0, -1, -2, -4, -6, -8, -10, -11, -12],
    },
    'Natural': {
        'rain': [-15, -13, -12, -16, -18, -14, -12, -15, -16],
        'wave': [-24, -20, -23, -25, -22, -20, -22, -24, -23],
        'thunder': [-50, -44, -52, -60, -46, -42, -50, -56, -52],
        'bright': [1, 0, -1, 0, -2, -3, -2, -4, -5],
    },
    'Storm': {
        'rain': [-10, -8, -6, -9, -12, -7, -5, -8, -10],
        'wave': [-17, -14, -12, -16, -19, -13, -11, -14, -16],
        'thunder': [-28, -22, -18, -30, -24, -16, -20, -26, -22],
        'bright': [-1, -3, -5, -2, -7, -4, -8, -5, -7],
    },
}


class CurveChart(tk.Canvas):
    def __init__(self, master, title, values, y_min, y_max, duration_getter, value_suffix='', **kw):
        super().__init__(master, height=180, background='#10161f', highlightthickness=0, **kw)
        self.title = title
        self.values = list(values)
        self.y_min = float(y_min)
        self.y_max = float(y_max)
        self.duration_getter = duration_getter
        self.value_suffix = value_suffix
        self.drag_index = None
        self.pad_l, self.pad_r, self.pad_t, self.pad_b = 45, 18, 28, 28
        self.bind('<Configure>', lambda e: self.redraw())
        self.bind('<Button-1>', self._down)
        self.bind('<B1-Motion>', self._move)
        self.bind('<ButtonRelease-1>', lambda e: setattr(self, 'drag_index', None))

    def set_values(self, vals):
        self.values = [float(x) for x in vals]
        self.redraw()

    def get_values(self):
        return [round(float(x), 2) for x in self.values]

    def _plot_box(self):
        w = max(200, self.winfo_width())
        h = max(120, self.winfo_height())
        return self.pad_l, self.pad_t, w - self.pad_r, h - self.pad_b

    def _xy(self, i, value):
        x0, y0, x1, y1 = self._plot_box()
        x = x0 + (x1 - x0) * i / max(1, len(self.values) - 1)
        frac = (float(value) - self.y_min) / (self.y_max - self.y_min)
        frac = max(0.0, min(1.0, frac))
        y = y1 - frac * (y1 - y0)
        return x, y

    def _value_from_y(self, y):
        x0, y0, x1, y1 = self._plot_box()
        frac = (y1 - max(y0, min(y1, y))) / max(1.0, (y1 - y0))
        return self.y_min + frac * (self.y_max - self.y_min)

    def redraw(self):
        self.delete('all')
        x0, y0, x1, y1 = self._plot_box()
        self.create_text(10, 8, anchor='nw', text=self.title, fill='white', font=('Segoe UI', 10, 'bold'))
        for j in range(5):
            y = y0 + (y1-y0)*j/4
            val = self.y_max - (self.y_max-self.y_min)*j/4
            self.create_line(x0, y, x1, y, fill='#26313f')
            self.create_text(x0-6, y, anchor='e', text=f'{val:.0f}', fill='#7f93a8', font=('Segoe UI', 8))
        hrs = max(0.1, float(self.duration_getter()))
        for i in range(len(self.values)):
            x, _ = self._xy(i, self.values[i])
            self.create_line(x, y0, x, y1, fill='#1e2935')
            label = hrs * i / max(1, len(self.values)-1)
            self.create_text(x, y1+15, text=f'{label:g}h', fill='#7f93a8', font=('Segoe UI', 8))
        pts = [self._xy(i, v) for i, v in enumerate(self.values)]
        if len(pts) >= 2:
            flat = [z for p in pts for z in p]
            self.create_line(*flat, fill='#58a6ff', width=3)
        for i, (x,y) in enumerate(pts):
            self.create_oval(x-5,y-5,x+5,y+5,fill='white',outline='#2f81f7',width=2,tags=(f'p{i}',))
            self.create_text(x, y-13, text=f'{self.values[i]:.0f}{self.value_suffix}', fill='#a8c7ff', font=('Segoe UI', 8))

    def _nearest(self, x, y):
        best, dist = None, 9999
        for i,v in enumerate(self.values):
            px,py = self._xy(i,v)
            d=(px-x)**2+(py-y)**2
            if d<dist:
                dist=d; best=i
        return best if dist <= 18**2 else None

    def _down(self, e):
        self.drag_index = self._nearest(e.x,e.y)
        if self.drag_index is not None:
            self._move(e)

    def _move(self, e):
        if self.drag_index is None: return
        val = self._value_from_y(e.y)
        self.values[self.drag_index] = round(max(self.y_min, min(self.y_max, val)), 1)
        self.redraw()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry('1280x920')
        self.minsize(1120, 780)
        self.process_holder = {}
        self.cancel_flag = False
        self.rendering = False
        self._make_vars()
        self._build_ui()
        self.apply_preset('Sleep')
        self._check_ffmpeg()

    def _make_vars(self):
        self.v_video = tk.StringVar()
        self.v_rain = tk.StringVar()
        self.v_wave = tk.StringVar()
        self.v_thunder = tk.StringVar()
        self.v_output = tk.StringVar()
        self.v_hours = tk.DoubleVar(value=8.0)
        self.v_orig_db = tk.DoubleVar(value=-6.0)
        self.v_apply_brightness = tk.BooleanVar(value=False)
        self.v_encoder = tk.StringVar(value='auto')
        self.v_brightness_mode = tk.StringVar(value='smart_fast')
        self.v_brightness_step = tk.DoubleVar(value=1.0)
        self.v_block_seconds = tk.DoubleVar(value=60.0)
        self.v_preset_x264 = tk.StringVar(value='veryfast')
        self.v_crf = tk.IntVar(value=22)
        self.v_seed = tk.IntVar(value=777)
        self.v_weather_preset = tk.StringVar(value='Sleep')
        self.v_status = tk.StringVar(value='Sẵn sàng.')
        self.v_src_info = tk.StringVar(value='')
        self.v_progress = tk.DoubleVar(value=0.0)

    def _build_ui(self):
        top = ttk.Frame(self, padding=10); top.pack(fill='x')
        ttk.Label(top, text='QUANZU RAIN V2 FAST', font=('Segoe UI', 18, 'bold')).pack(side='left')
        ttk.Label(top, text='  •  Fast Loop/Copy + bảng thời tiết + Mưa/Sóng/Sấm').pack(side='left', pady=(7,0))
        ttk.Button(top, text='Lưu project', command=self.save_project).pack(side='right', padx=4)
        ttk.Button(top, text='Mở project', command=self.load_project).pack(side='right', padx=4)

        self.nb = ttk.Notebook(self); self.nb.pack(fill='both', expand=True, padx=10, pady=(0,10))
        self.tab_source = ttk.Frame(self.nb, padding=12)
        self.tab_weather = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.tab_source, text='1. NGUỒN & RENDER FAST')
        self.nb.add(self.tab_weather, text='2. BẢNG THỜI TIẾT')
        self._build_source()
        self._build_weather()

    def _path_row(self, parent, row, title, var, mode='file'):
        ttk.Label(parent, text=title, width=24).grid(row=row,column=0,sticky='w',pady=6)
        e=ttk.Entry(parent,textvariable=var); e.grid(row=row,column=1,sticky='ew',pady=6,padx=(0,6))
        def choose_file():
            if mode=='video':
                p=filedialog.askopenfilename(filetypes=[('Video','*.mp4 *.mov *.mkv *.m4v *.avi *.webm *.ts'),('All','*.*')])
            elif mode=='audio':
                p=filedialog.askopenfilename(filetypes=[('Audio','*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus *.wma'),('All','*.*')])
            elif mode=='output':
                p=filedialog.asksaveasfilename(defaultextension='.mp4',filetypes=[('MP4','*.mp4'),('MKV','*.mkv')])
            else:
                p=filedialog.askopenfilename()
            if p:
                var.set(p)
                if mode=='video': self.on_video_changed()
        ttk.Button(parent,text='Chọn file',command=choose_file).grid(row=row,column=2,pady=6)
        if mode=='audio':
            def choose_folder():
                p=filedialog.askdirectory()
                if p: var.set(p)
            ttk.Button(parent,text='Chọn folder',command=choose_folder).grid(row=row,column=3,pady=6,padx=(6,0))

    def _build_source(self):
        f=self.tab_source; f.columnconfigure(1,weight=1)
        self._path_row(f,0,'Video nguồn (1 video):',self.v_video,'video')
        self._path_row(f,1,'Tiếng mưa (file/folder):',self.v_rain,'audio')
        self._path_row(f,2,'Tiếng sóng biển (file/folder):',self.v_wave,'audio')
        self._path_row(f,3,'Tiếng sấm (file/folder):',self.v_thunder,'audio')
        self._path_row(f,4,'File xuất:',self.v_output,'output')
        ttk.Label(f,textvariable=self.v_src_info,foreground='#336699').grid(row=5,column=1,columnspan=3,sticky='w',pady=(0,8))

        cfg=ttk.LabelFrame(f,text='Thời lượng & chất lượng',padding=10); cfg.grid(row=6,column=0,columnspan=4,sticky='ew',pady=8)
        for i in range(8): cfg.columnconfigure(i,weight=0)
        ttk.Label(cfg,text='Thời lượng:').grid(row=0,column=0,sticky='w')
        sp=ttk.Spinbox(cfg,from_=0.1,to=24.0,increment=0.5,textvariable=self.v_hours,width=8,command=self._redraw_charts); sp.grid(row=0,column=1,padx=(4,12))
        ttk.Button(cfg,text='8h',command=lambda:self._set_hours(8)).grid(row=0,column=2,padx=2)
        ttk.Button(cfg,text='10h',command=lambda:self._set_hours(10)).grid(row=0,column=3,padx=2)
        ttk.Button(cfg,text='12h',command=lambda:self._set_hours(12)).grid(row=0,column=4,padx=2)
        ttk.Label(cfg,text='Âm thanh gốc dB:').grid(row=0,column=5,padx=(20,4))
        ttk.Spinbox(cfg,from_=-60,to=12,increment=1,textvariable=self.v_orig_db,width=7).grid(row=0,column=6)

        ttk.Checkbutton(cfg,text='Áp dụng đường cong ĐỘ SÁNG',variable=self.v_apply_brightness).grid(row=1,column=0,columnspan=3,sticky='w',pady=(10,0))
        ttk.Label(cfg,text='Chế độ sáng:').grid(row=1,column=3,padx=(12,4),pady=(10,0))
        ttk.Combobox(cfg,textvariable=self.v_brightness_mode,values=['smart_fast','full_encode'],width=14,state='readonly').grid(row=1,column=4,pady=(10,0))
        ttk.Label(cfg,text='Encoder:').grid(row=1,column=5,padx=(20,4),pady=(10,0))
        ttk.Combobox(cfg,textvariable=self.v_encoder,values=['auto','h264_nvenc','h264_qsv','h264_amf','libx264'],width=14,state='readonly').grid(row=1,column=6,pady=(10,0))

        ttk.Label(cfg,text='x264 preset:').grid(row=2,column=0,sticky='w',pady=(10,0))
        ttk.Combobox(cfg,textvariable=self.v_preset_x264,values=['ultrafast','superfast','veryfast','faster','fast','medium'],width=12,state='readonly').grid(row=2,column=1,pady=(10,0))
        ttk.Label(cfg,text='CRF/CQ:').grid(row=2,column=2,padx=(15,4),pady=(10,0))
        ttk.Spinbox(cfg,from_=15,to=35,textvariable=self.v_crf,width=6).grid(row=2,column=3,pady=(10,0))
        ttk.Label(cfg,text='Bước sáng Smart:').grid(row=2,column=4,padx=(15,4),pady=(10,0))
        ttk.Spinbox(cfg,from_=0.5,to=5.0,increment=0.5,textvariable=self.v_brightness_step,width=6).grid(row=2,column=5,pady=(10,0))
        ttk.Label(cfg,text='%',foreground='#5d6d7e').grid(row=2,column=6,sticky='w',pady=(10,0))
        ttk.Label(cfg,text='Block FAST (giây):').grid(row=2,column=7,padx=(15,4),pady=(10,0))
        ttk.Spinbox(cfg,from_=15,to=300,increment=15,textvariable=self.v_block_seconds,width=7).grid(row=2,column=8,pady=(10,0))
        ttk.Label(cfg,text='FAST V2: không còn ghép 3.000+ clip 9 giây khi không cần. Tắt độ sáng = stream_loop + COPY trực tiếp + mix audio trong 1 lượt; bật độ sáng = cache block 60s rồi COPY.',foreground='#1f6f43').grid(row=3,column=0,columnspan=8,sticky='w',pady=(10,0))
        ttk.Label(cfg,text='Không tạo file 8h tạm rồi xử lý audio lần 2. Progress lấy trực tiếp từ FFmpeg nên không kẹt giả ở 99%. Auto thử NVENC → QSV → AMF → CPU.',foreground='#5d6d7e').grid(row=4,column=0,columnspan=8,sticky='w',pady=(4,0))

        action=ttk.LabelFrame(f,text='Render FAST',padding=10); action.grid(row=7,column=0,columnspan=4,sticky='nsew',pady=8)
        action.columnconfigure(0,weight=1)
        ttk.Progressbar(action,variable=self.v_progress,maximum=100).grid(row=0,column=0,columnspan=3,sticky='ew',pady=(0,8))
        ttk.Label(action,textvariable=self.v_status).grid(row=1,column=0,columnspan=3,sticky='w')
        self.btn_render=ttk.Button(action,text='▶ RENDER 8–12H',command=self.start_render); self.btn_render.grid(row=2,column=0,sticky='ew',pady=(12,0),padx=(0,6))
        self.btn_cancel=ttk.Button(action,text='HỦY',command=self.cancel_render,state='disabled'); self.btn_cancel.grid(row=2,column=1,pady=(12,0),padx=6)
        ttk.Button(action,text='Mở thư mục output',command=self.open_output_folder).grid(row=2,column=2,pady=(12,0),padx=(6,0))
        ttk.Label(action,text='1 video ngắn → 8–12h. Ba lớp audio riêng: MƯA + SÓNG + SẤM. Bảng thời tiết điều khiển âm lượng/độ sáng theo giờ.').grid(row=3,column=0,columnspan=3,sticky='w',pady=(12,0))

    def _build_weather(self):
        f=self.tab_weather
        controls=ttk.Frame(f); controls.pack(fill='x',pady=(0,8))
        ttk.Label(controls,text='Preset:').pack(side='left')
        cb=ttk.Combobox(controls,textvariable=self.v_weather_preset,values=list(PRESETS),state='readonly',width=14); cb.pack(side='left',padx=5)
        cb.bind('<<ComboboxSelected>>',lambda e:self.apply_preset(self.v_weather_preset.get()))
        ttk.Label(controls,text='Seed:').pack(side='left',padx=(15,4))
        ttk.Entry(controls,textvariable=self.v_seed,width=10).pack(side='left')
        ttk.Button(controls,text='RANDOM TẤT CẢ',command=self.random_all).pack(side='left',padx=(15,4))
        ttk.Button(controls,text='Random mưa',command=lambda:self.random_curve('rain')).pack(side='left',padx=3)
        ttk.Button(controls,text='Random sóng',command=lambda:self.random_curve('wave')).pack(side='left',padx=3)
        ttk.Button(controls,text='Random sấm',command=lambda:self.random_curve('thunder')).pack(side='left',padx=3)
        ttk.Button(controls,text='Random sáng',command=lambda:self.random_curve('bright')).pack(side='left',padx=3)
        ttk.Label(controls,text='Kéo các điểm lên/xuống để chỉnh theo từng mốc giờ.').pack(side='left',padx=(15,0))

        self.chart_rain=CurveChart(f,'CƯỜNG ĐỘ MƯA (dB)',PRESETS['Sleep']['rain'],-36,0,lambda:self.v_hours.get(),' dB'); self.chart_rain.pack(fill='x',pady=5)
        self.chart_wave=CurveChart(f,'SÓNG BIỂN (dB)',PRESETS['Sleep']['wave'],-36,0,lambda:self.v_hours.get(),' dB'); self.chart_wave.pack(fill='x',pady=5)
        self.chart_thunder=CurveChart(f,'SẤM / THUNDER (dB)',PRESETS['Sleep']['thunder'],-60,0,lambda:self.v_hours.get(),' dB'); self.chart_thunder.pack(fill='x',pady=5)
        self.chart_bright=CurveChart(f,'ĐỘ SÁNG VIDEO (%)',PRESETS['Sleep']['bright'],-20,10,lambda:self.v_hours.get(),'%'); self.chart_bright.pack(fill='x',pady=5)
        note=ttk.Label(f,text='Mưa/sóng/sấm thay đổi mượt theo thời gian. SMART FAST lượng tử độ sáng theo bước nhỏ (mặc định 1%); với video loop ngắn, thay đổi giữa các mức diễn ra rất chậm và gần như không thấy bước nhảy.',foreground='#5d6d7e')
        note.pack(anchor='w',pady=(8,0))

    def _set_hours(self,h):
        self.v_hours.set(float(h)); self._redraw_charts()

    def _redraw_charts(self):
        for c in getattr(self,'chart_rain',None),getattr(self,'chart_wave',None),getattr(self,'chart_thunder',None),getattr(self,'chart_bright',None):
            if c: c.redraw()

    def _check_ffmpeg(self):
        try:
            p=find_ffmpeg(); self.v_status.set(f'FFmpeg OK: {p}')
        except Exception as ex:
            self.v_status.set(str(ex))

    def on_video_changed(self):
        try:
            info=probe_media(self.v_video.get())
            self.v_src_info.set(f"Nguồn: {info['duration']:.1f}s • {info['width']}×{info['height']} • video={info['video_codec']} • audio={info['audio_codec'] or 'không có'}")
            if not self.v_output.get():
                p=Path(self.v_video.get()); self.v_output.set(str(p.with_name(p.stem+'_QuanZuRainV2_8-12H.mp4')))
        except Exception as ex:
            self.v_src_info.set(f'Lỗi đọc video: {ex}')

    def apply_preset(self,name):
        p=PRESETS.get(name,PRESETS['Sleep'])
        if hasattr(self,'chart_rain'):
            self.chart_rain.set_values(p['rain']); self.chart_wave.set_values(p['wave']); self.chart_thunder.set_values(p['thunder']); self.chart_bright.set_values(p['bright'])

    def _new_seed(self):
        s=random.SystemRandom().randint(100000,999999999); self.v_seed.set(s); return s

    def random_curve(self,kind):
        seed=self._new_seed(); r=random.Random(seed + {'rain':11,'wave':29,'thunder':41,'bright':53}[kind])
        if kind=='rain':
            base=r.uniform(-19,-11); vals=[]
            for _ in range(POINTS): base=max(-30,min(-5,base+r.uniform(-3.5,3.5))); vals.append(base)
            self.chart_rain.set_values(vals)
        elif kind=='wave':
            base=r.uniform(-27,-16); vals=[]
            for _ in range(POINTS): base=max(-34,min(-8,base+r.uniform(-4,4))); vals.append(base)
            self.chart_wave.set_values(vals)
        elif kind=='thunder':
            base=r.uniform(-55,-35); vals=[]
            for _ in range(POINTS): base=max(-60,min(-8,base+r.uniform(-10,10))); vals.append(base)
            self.chart_thunder.set_values(vals)
        else:
            base=r.uniform(-2,2); vals=[]
            for _ in range(POINTS): base=max(-18,min(8,base+r.uniform(-4,2))); vals.append(base)
            self.chart_bright.set_values(vals)

    def random_all(self):
        s=self._new_seed(); r=random.Random(s)
        rain=[]; wave=[]; thunder=[]; bright=[]
        br=r.uniform(-17,-11); bw=r.uniform(-25,-16); bt=r.uniform(-55,-35); bb=r.uniform(-1,2)
        for _ in range(POINTS):
            br=max(-30,min(-5,br+r.uniform(-3,3))); rain.append(br)
            bw=max(-34,min(-8,bw+r.uniform(-3.5,3.5))); wave.append(bw)
            bt=max(-60,min(-8,bt+r.uniform(-9,9))); thunder.append(bt)
            bb=max(-18,min(8,bb+r.uniform(-3.5,2))); bright.append(bb)
        self.chart_rain.set_values(rain); self.chart_wave.set_values(wave); self.chart_thunder.set_values(thunder); self.chart_bright.set_values(bright)

    def _config(self):
        hours=float(self.v_hours.get())
        if hours<0.1 or hours>24: raise ValueError('Thời lượng phải từ 0.1 đến 24 giờ.')
        return RenderConfig(
            video_path=self.v_video.get().strip(), output_path=self.v_output.get().strip(), duration_hours=hours,
            rain_source=self.v_rain.get().strip(), wave_source=self.v_wave.get().strip(), thunder_source=self.v_thunder.get().strip(),
            rain_curve_db=self.chart_rain.get_values(), wave_curve_db=self.chart_wave.get_values(), thunder_curve_db=self.chart_thunder.get_values(), brightness_curve_pct=self.chart_bright.get_values(),
            apply_brightness=bool(self.v_apply_brightness.get()), brightness_mode=self.v_brightness_mode.get(), brightness_step_pct=float(self.v_brightness_step.get()),
            original_audio_db=float(self.v_orig_db.get()), seed=int(self.v_seed.get()),
            encoder=self.v_encoder.get(), preset=self.v_preset_x264.get(), crf=int(self.v_crf.get()), cq=int(self.v_crf.get()), block_seconds=float(self.v_block_seconds.get()),
        )

    def start_render(self):
        if self.rendering: return
        try: cfg=self._config()
        except Exception as ex: return messagebox.showerror('Lỗi cấu hình',str(ex),parent=self)
        if not cfg.output_path: return messagebox.showwarning('Thiếu output','Chưa chọn file xuất.',parent=self)
        self.rendering=True; self.cancel_flag=False; self.v_progress.set(0); self.btn_render.config(state='disabled'); self.btn_cancel.config(state='normal')
        def ui_progress(pct,text):
            self.after(0,lambda:(self.v_progress.set(pct),self.v_status.set(f'Render: {text}')))
        def work():
            try:
                ok,msg,built=run_render(cfg,on_progress=ui_progress,should_cancel=lambda:self.cancel_flag,process_holder=self.process_holder)
                def done():
                    self.rendering=False; self.btn_render.config(state='normal'); self.btn_cancel.config(state='disabled')
                    self.v_status.set(('Hoàn tất: ' if ok else 'Lỗi: ')+msg)
                    if ok:
                        self.v_progress.set(100)
                        extra = ''
                        if getattr(built,'mode','') == 'smart_fast':
                            extra = f"\nSmart Fast: mã hóa mới {built.variants_encoded} mức sáng • dùng cache {built.variants_reused} mức • {built.blocks_total} block"
                        messagebox.showinfo('Xong',f"Render hoàn tất.\n\nVideo: {cfg.output_path}\nMưa: {built.selected_rain or 'không dùng'}\nSóng: {built.selected_wave or 'không dùng'}\nSấm: {built.selected_thunder or 'không dùng'}\nChế độ: {getattr(built,'mode','')}\nVideo codec: {built.encoder_used}{extra}",parent=self)
                    elif not self.cancel_flag:
                        messagebox.showerror('FFmpeg lỗi',msg,parent=self)
                self.after(0,done)
            except Exception as ex:
                self.after(0,lambda:self._render_exception(ex))
        threading.Thread(target=work,daemon=True).start()

    def _render_exception(self,ex):
        self.rendering=False; self.btn_render.config(state='normal'); self.btn_cancel.config(state='disabled'); self.v_status.set(f'Lỗi: {ex}'); messagebox.showerror('Lỗi',str(ex),parent=self)

    def cancel_render(self):
        self.cancel_flag=True; self.v_status.set('Đang hủy…')
        p=self.process_holder.get('process')
        if p:
            try: p.terminate()
            except Exception: pass

    def save_project(self):
        p=filedialog.asksaveasfilename(defaultextension='.rainloop.json',filetypes=[('RainLoop project','*.rainloop.json'),('JSON','*.json')])
        if not p:return
        try:
            data=asdict(self._config()); data['weather_preset']=self.v_weather_preset.get()
            Path(p).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
            self.v_status.set(f'Đã lưu project: {p}')
        except Exception as ex: messagebox.showerror('Lỗi',str(ex),parent=self)

    def load_project(self):
        p=filedialog.askopenfilename(filetypes=[('RainLoop project','*.rainloop.json *.json'),('All','*.*')])
        if not p:return
        try:
            d=json.loads(Path(p).read_text(encoding='utf-8'))
            self.v_video.set(d.get('video_path','')); self.v_output.set(d.get('output_path','')); self.v_hours.set(d.get('duration_hours',8)); self.v_rain.set(d.get('rain_source','')); self.v_wave.set(d.get('wave_source','')); self.v_thunder.set(d.get('thunder_source',''))
            self.v_orig_db.set(d.get('original_audio_db',-6)); self.v_apply_brightness.set(d.get('apply_brightness',False)); self.v_brightness_mode.set(d.get('brightness_mode','smart_fast')); self.v_brightness_step.set(d.get('brightness_step_pct',1.0)); self.v_block_seconds.set(d.get('block_seconds',60.0)); self.v_encoder.set(d.get('encoder','auto')); self.v_preset_x264.set(d.get('preset','veryfast')); self.v_crf.set(d.get('crf',22)); self.v_seed.set(d.get('seed',777)); self.v_weather_preset.set(d.get('weather_preset','Sleep'))
            self.chart_rain.set_values(d.get('rain_curve_db',PRESETS['Sleep']['rain'])); self.chart_wave.set_values(d.get('wave_curve_db',PRESETS['Sleep']['wave'])); self.chart_thunder.set_values(d.get('thunder_curve_db',PRESETS['Sleep']['thunder'])); self.chart_bright.set_values(d.get('brightness_curve_pct',PRESETS['Sleep']['bright']))
            self.on_video_changed(); self._redraw_charts(); self.v_status.set(f'Đã mở project: {p}')
        except Exception as ex: messagebox.showerror('Lỗi mở project',str(ex),parent=self)

    def open_output_folder(self):
        p=Path(self.v_output.get()).parent if self.v_output.get() else Path.cwd()
        try:
            if os.name=='nt': os.startfile(str(p))
            elif os.name=='posix': os.system(f'xdg-open "{p}" >/dev/null 2>&1 &')
        except Exception as ex: messagebox.showerror('Lỗi',str(ex),parent=self)


if __name__=='__main__':
    App().mainloop()