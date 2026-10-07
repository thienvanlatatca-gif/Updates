# -*- coding: utf-8 -*-
"""Direct ChatGPT command + SRT analysis engine for PR Auto Tool."""
from __future__ import annotations

from pathlib import Path
from typing import Callable
import base64
import json
import re
import time
import urllib.error
import urllib.request

from chatgpt_account import ChatGPTAccountManager, ChatGPTInferenceError, RESOURCE

DeltaFn = Callable[[str], None]
LogFn = Callable[[str], None]

SYSTEM_DIRECTOR = """You are the semantic editing brain inside PR Auto Tool, a Premiere Pro video-editing utility.
Analyze the ENTIRE attached SRT before making editing recommendations. The attached SRT is the source of truth for spoken content and timestamps. Never invent dialogue that is not in the SRT. The supplied video URL and locally extracted metadata are reference context only; do not claim you watched the video just from a URL.
When the user asks what to cut, preserve the main story, setup, causal links, turning points, climax, and conclusion. Prefer removing advertisements, off-topic tangents, repetition, singing/music-only material when indicated by the transcript, and low-value detail. Answer in Vietnamese unless the user explicitly requests another language.
"""

CUT_SCHEMA = {
    "type":"object",
    "properties":{
        "summary":{"type":"string"},
        "target_reduction_percent":{"type":"number","minimum":0,"maximum":80},
        "cuts":{"type":"array","items":{
            "type":"object",
            "properties":{
                "from_cue":{"type":"integer","minimum":1},
                "to_cue":{"type":"integer","minimum":1},
                "label":{"type":"string","enum":["ADVERTISEMENT","OFF_TOPIC","REPETITION","SONG","LOW_VALUE_DETAIL","OTHER"]},
                "reason":{"type":"string"},
                "confidence":{"type":"number","minimum":0,"maximum":1}
            },
            "required":["from_cue","to_cue","label","reason","confidence"],
            "additionalProperties":False
        }},
        "preserved_structure":{"type":"array","items":{"type":"string"}},
        "notes":{"type":"string"}
    },
    "required":["summary","target_reduction_percent","cuts","preserved_structure","notes"],
    "additionalProperties":False
}


def _parse_srt_time(raw: str) -> float:
    raw=raw.strip().replace('.',','); h,m,rest=raw.split(':'); s,ms=(rest.split(',')+['0'])[:2]
    return int(h)*3600+int(m)*60+int(s)+int(ms[:3].ljust(3,'0'))/1000.0


def parse_srt_with_ids(path: str|Path) -> list[dict]:
    p=Path(path)
    text=p.read_text(encoding='utf-8-sig',errors='replace').replace('\r\n','\n')
    blocks=re.split(r'\n\s*\n',text.strip()); out=[]; fallback=1
    for block in blocks:
        lines=[x.rstrip() for x in block.splitlines() if x.strip()]
        if not lines: continue
        ti=next((i for i,x in enumerate(lines) if '-->' in x),None)
        if ti is None: continue
        try:
            a,b=[x.strip() for x in lines[ti].split('-->',1)]; start,end=_parse_srt_time(a),_parse_srt_time(b)
        except Exception: continue
        cue_id=fallback
        if ti>0:
            try: cue_id=int(lines[ti-1].strip())
            except Exception: cue_id=fallback
        content='\n'.join(lines[ti+1:]).strip()
        if end>start:
            out.append({'cue_id':cue_id,'start':round(start,3),'end':round(end,3),'text':content})
            fallback=max(fallback+1,cue_id+1)
    return out


def _srt_stamp(sec: float) -> str:
    ms=max(0,int(round(sec*1000))); h=ms//3600000; ms%=3600000; m=ms//60000; ms%=60000; s=ms//1000; ms%=1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _merge_ranges(ranges: list[dict], gap: float=0.12) -> list[dict]:
    if not ranges: return []
    rows=sorted(ranges,key=lambda x:(x['start'],x['end'])); merged=[]
    for row in rows:
        if not merged or row['start']>merged[-1]['end']+gap:
            merged.append(dict(row))
        else:
            m=merged[-1]; m['end']=max(m['end'],row['end']); m['to_cue']=max(m['to_cue'],row['to_cue'])
            if row['label'] not in m['labels']: m['labels'].append(row['label'])
            m['reasons'].append(row['reason']); m['confidence']=max(m['confidence'],row['confidence'])
    return merged


def validate_cut_plan(plan: dict, srt_path: str|Path, *, video_duration: float=0.0) -> dict:
    cues=parse_srt_with_ids(srt_path)
    if not cues: raise ValueError('SRT không có cue hợp lệ.')
    by_id={c['cue_id']:c for c in cues}; raw=[]; rejected=[]
    for cut in plan.get('cuts') or []:
        try: a=int(cut.get('from_cue')); b=int(cut.get('to_cue'))
        except Exception: rejected.append({'cut':cut,'reason':'cue id không hợp lệ'}); continue
        if a>b: a,b=b,a
        selected=[c for c in cues if a<=c['cue_id']<=b]
        if not selected:
            rejected.append({'cut':cut,'reason':'cue range không tồn tại trong SRT'}); continue
        raw.append({
            'start':selected[0]['start'],'end':selected[-1]['end'],'from_cue':selected[0]['cue_id'],'to_cue':selected[-1]['cue_id'],
            'label':str(cut.get('label') or 'OTHER'),'labels':[str(cut.get('label') or 'OTHER')],
            'reason':str(cut.get('reason') or ''),'reasons':[str(cut.get('reason') or '')],
            'confidence':max(0.0,min(1.0,float(cut.get('confidence') or 0)))
        })
    merged=_merge_ranges(raw)
    base=max(float(video_duration or 0),cues[-1]['end'])
    cut_seconds=sum(max(0.0,r['end']-r['start']) for r in merged)
    keep=[]; cursor=0.0
    for r in merged:
        if r['start']>cursor: keep.append({'start':round(cursor,3),'end':round(r['start'],3)})
        cursor=max(cursor,r['end'])
    if base>cursor: keep.append({'start':round(cursor,3),'end':round(base,3)})
    result=dict(plan)
    result.update({
        'schema':'pr-auto-ai-cut-plan-v1','srt_path':str(Path(srt_path).resolve()),'cue_count':len(cues),
        'delete_ranges':[{k:(round(v,3) if isinstance(v,float) else v) for k,v in r.items()} for r in merged],
        'keep_ranges':keep,'cut_seconds':round(cut_seconds,3),'base_duration_seconds':round(base,3),
        'actual_reduction_percent':round((cut_seconds/base*100.0) if base else 0.0,2),'rejected_cuts':rejected,
    })
    return result


def write_cut_review_files(validated: dict, output_dir: str|Path) -> dict:
    srt=Path(validated['srt_path']); cues=parse_srt_with_ids(srt); ranges=validated.get('delete_ranges') or []
    outdir=Path(output_dir); outdir.mkdir(parents=True,exist_ok=True)
    stem=srt.stem
    review=outdir/f'{stem}_AI_REVIEW.srt'; cutonly=outdir/f'{stem}_AI_CUT_ONLY.srt'
    review_lines=[]; cut_lines=[]; ri=1; ci=1
    for c in cues:
        hit=None
        for r in ranges:
            if r['from_cue']<=c['cue_id']<=r['to_cue']:
                hit=r; break
        text=c['text']
        if hit: text=f"[✂ {','.join(hit.get('labels') or [hit.get('label','CUT')])}] {text}"
        review_lines += [str(ri),f"{_srt_stamp(c['start'])} --> {_srt_stamp(c['end'])}",text,'']; ri+=1
        if hit:
            cut_lines += [str(ci),f"{_srt_stamp(c['start'])} --> {_srt_stamp(c['end'])}",c['text'],'']; ci+=1
    review.write_text('\n'.join(review_lines),encoding='utf-8-sig'); cutonly.write_text('\n'.join(cut_lines),encoding='utf-8-sig')
    return {'review_srt':str(review.resolve()),'cut_only_srt':str(cutonly.resolve())}


class ChatGPTDirector:
    def __init__(self, account: ChatGPTAccountManager, emit: LogFn|None=None):
        self.account=account; self.emit=emit or (lambda _s:None)

    def _model(self, requested: str) -> str:
        return self.account.choose_model(requested)

    def _file_part(self, srt_path: str|Path) -> dict:
        p=Path(srt_path)
        if not p.exists(): raise FileNotFoundError(f'Không tìm thấy SRT: {p}')
        size=p.stat().st_size
        if size>45*1024*1024: raise ValueError('SRT lớn hơn 45 MB; vượt giới hạn an toàn cho một request.')
        data=base64.b64encode(p.read_bytes()).decode('ascii')
        return {'type':'input_file','filename':p.name,'file_data':'data:application/x-subrip;base64,'+data}

    def _video_context(self, url: str) -> str:
        url=(url or '').strip()
        if not url: return 'Video URL: (không có)'
        bits=[f'Video URL: {url}']
        try:
            import yt_dlp
            opts={'quiet':True,'no_warnings':True,'skip_download':True,'noplaylist':True,'socket_timeout':15}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info=ydl.extract_info(url,download=False)
            if isinstance(info,dict):
                for label,key in [('Title','title'),('Channel','channel'),('Uploader','uploader'),('Duration','duration_string')]:
                    if info.get(key): bits.append(f'{label}: {info.get(key)}')
                desc=str(info.get('description') or '').strip()
                if desc: bits.append('Description (truncated): '+desc[:1500])
        except Exception as exc:
            self.emit(f'ℹ Không lấy được metadata URL; vẫn phân tích SRT: {exc}')
        return '\n'.join(bits)

    def _request(self, payload: dict, *, on_delta: DeltaFn|None=None, label: str='ChatGPT') -> str:
        token=self.account.access_token(); attempted_refresh=False
        while True:
            req=urllib.request.Request(RESOURCE+'/responses',data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={
                'Authorization':f'Bearer {token}','Content-Type':'application/json','Accept':'text/event-stream'
            },method='POST')
            pieces=[]; completed=False; request_id=''; started=time.monotonic(); last_notice=started
            try:
                with urllib.request.urlopen(req,timeout=900) as r:
                    request_id=str(r.headers.get('x-request-id') or '')
                    for raw_line in r:
                        line=raw_line.decode('utf-8','replace').strip()
                        if not line.startswith('data:'): continue
                        raw=line[5:].strip()
                        if not raw or raw=='[DONE]': continue
                        try: event=json.loads(raw)
                        except Exception: continue
                        etype=str(event.get('type') or '')
                        if etype=='response.output_text.delta':
                            delta=str(event.get('delta') or '')
                            if delta:
                                pieces.append(delta)
                                if on_delta: on_delta(delta)
                        elif etype=='response.completed': completed=True
                        elif etype in {'response.failed','response.incomplete','error'}:
                            err=event.get('error') or (event.get('response') or {}).get('error') or {}
                            if not isinstance(err,dict): err={'message':str(err)}
                            raise ChatGPTInferenceError(str(err.get('message') or etype),code=str(err.get('code') or etype),request_id=request_id)
                        now=time.monotonic()
                        if now-last_notice>=30:
                            self.emit(f'… {label} vẫn đang xử lý ({int(now-started)}s)'); last_notice=now
                if not completed: raise ChatGPTInferenceError('Luồng ChatGPT kết thúc nhưng không có response.completed',request_id=request_id)
                return ''.join(pieces).strip()
            except urllib.error.HTTPError as exc:
                body=exc.read().decode('utf-8','replace') if hasattr(exc,'read') else str(exc); code=''; msg=body
                try:
                    obj=json.loads(body); er=obj.get('error') if isinstance(obj,dict) else None
                    if isinstance(er,dict): code=str(er.get('code') or ''); msg=str(er.get('message') or body)
                except Exception: pass
                if exc.code==401 and not attempted_refresh:
                    attempted_refresh=True; token=self.account.access_token(force_refresh=True); continue
                if code in {'subscription_sharing_usage_limit_exceeded','subscription_sharing_usage_unavailable'}:
                    raise RuntimeError('Đã chạm giới hạn dùng gói ChatGPT cho ứng dụng. Kiểm tra ChatGPT > Settings > Usage.') from exc
                raise ChatGPTInferenceError(f'OpenAI HTTP {exc.code}: {msg[:1000]}',status=exc.code,code=code,request_id=request_id) from exc

    def ask(self, *, prompt: str, video_url: str, srt_path: str|Path, model: str='Auto', history: list[dict]|None=None, on_delta: DeltaFn|None=None) -> str:
        prompt=(prompt or '').strip()
        if not prompt: raise ValueError('Chưa nhập lệnh cho ChatGPT.')
        parts=[self._file_part(srt_path),{'type':'input_text','text':self._video_context(video_url)+'\n\nLỆNH NGƯỜI DÙNG:\n'+prompt}]
        input_items=[]
        for h in (history or [])[-6:]:
            role=str(h.get('role') or 'user'); content=str(h.get('content') or '')[:8000]
            if role in {'user','assistant'} and content: input_items.append({'role':role,'content':content})
        input_items.append({'role':'user','content':parts})
        payload={'model':self._model(model),'instructions':SYSTEM_DIRECTOR,'input':input_items,'store':False,'stream':True}
        return self._request(payload,on_delta=on_delta,label='phân tích SRT')

    def make_cut_plan(self, *, prompt: str, video_url: str, srt_path: str|Path, target_percent: float=15.0, model: str='Auto', video_duration: float=0.0, on_delta: DeltaFn|None=None) -> dict:
        user=(prompt or '').strip()
        instruction=f"""Hãy tạo KẾ HOẠCH CẮT video từ SRT đính kèm.
Mục tiêu giảm khoảng {float(target_percent):.1f}% thời lượng (sai số ưu tiên trong ±3 điểm phần trăm nếu nội dung cho phép).
Chỉ chọn theo SỐ CUE có sẵn trong SRT. Tuyệt đối không tự tạo timestamp. Mỗi block cắt phải là một dải cue liên tục from_cue..to_cue.
Ưu tiên: quảng cáo → lạc đề → lặp ý → hát/nhạc được thể hiện trong transcript → chi tiết ít giá trị. Giữ mạch lập luận/câu chuyện, hook, bước ngoặt, cao trào, kết luận.
Lệnh bổ sung của người dùng: {user or '(không có)'}
"""
        parts=[self._file_part(srt_path),{'type':'input_text','text':self._video_context(video_url)+'\n\n'+instruction}]
        payload={
            'model':self._model(model),'instructions':SYSTEM_DIRECTOR,'input':[{'role':'user','content':parts}],
            'text':{'format':{'type':'json_schema','name':'pr_auto_cut_plan','strict':True,'schema':CUT_SCHEMA}},
            'store':False,'stream':True
        }
        raw=self._request(payload,on_delta=on_delta,label='lập cut plan')
        try: plan=json.loads(raw)
        except Exception as exc: raise RuntimeError('ChatGPT trả cut plan không phải JSON hợp lệ: '+raw[:500]) from exc
        return validate_cut_plan(plan,srt_path,video_duration=video_duration)
