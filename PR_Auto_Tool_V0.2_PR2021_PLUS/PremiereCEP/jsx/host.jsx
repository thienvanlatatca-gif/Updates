/* PR Auto Bridge 2021+ — CEP/ExtendScript host for Premiere Pro 15.x+ */
var PRAuto = (function(){
    var api = {};
    api.version = "0.2.0";
    api.logs = [];

    function log(s){ api.logs.push(String(s)); }
    function err(e){ return (e && e.message) ? e.message : String(e); }
    function norm(p){ return String(p || "").replace(/\\/g,"/").toLowerCase(); }
    function baseName(p){ var a=String(p||"").replace(/\\/g,"/").split("/"); return a[a.length-1]; }
    function timeObj(seconds){ var t=new Time(); t.seconds=Math.max(0,Number(seconds)||0); return t; }
    function safeNum(v,d){ var n=Number(v); return isNaN(n)?d:n; }
    function readText(path){
        var f=new File(path); if(!f.exists) throw new Error("Không thấy file: "+path);
        f.encoding="UTF-8"; if(!f.open("r")) throw new Error("Không mở được file: "+path);
        var s=f.read(); f.close(); return s;
    }
    function parseObject(raw){ return eval("("+raw+")"); }

    function walkItems(root,out){
        out=out||[];
        if(!root) return out;
        var kids=null;
        try{ kids=root.children; }catch(_){ kids=null; }
        if(!kids) return out;
        for(var i=0;i<kids.numItems;i++){
            var it=kids[i]; if(!it) continue;
            var hasKids=false;
            try{ hasKids=!!it.children; }catch(_e){ hasKids=false; }
            if(hasKids){ walkItems(it,out); }
            else out.push(it);
        }
        return out;
    }

    function mediaPath(item){
        try{ return item.getMediaPath ? item.getMediaPath() : ""; }catch(_){ return ""; }
    }
    function findItem(path){
        var target=norm(path), name=baseName(path).toLowerCase();
        var items=walkItems(app.project.rootItem,[]);
        for(var i=0;i<items.length;i++){
            var p=norm(mediaPath(items[i]));
            if(p===target || (p && baseName(p).toLowerCase()===name)) return items[i];
        }
        return null;
    }
    function importOne(path){
        var existing=findItem(path); if(existing) return existing;
        var ok=app.project.importFiles([path],true,app.project.rootItem,false);
        if(!ok) throw new Error("Premiere importFiles thất bại: "+path);
        var imported=findItem(path); if(!imported) throw new Error("Đã import nhưng không tìm lại được: "+path);
        return imported;
    }
    function importMany(paths,maxCount){
        var out=[], lim=Math.min((paths||[]).length,maxCount||9999);
        for(var i=0;i<lim;i++){
            try{ out.push(importOne(paths[i])); }
            catch(e){ log("⚠ Import lỗi "+baseName(paths[i])+": "+err(e)); }
        }
        return out;
    }

    function activateSequence(seq){
        try{ seq.openInTimeline(); }catch(_){ try{ app.project.openSequence(seq.sequenceID); }catch(__){} }
        try{ app.project.activeSequence=seq; }catch(_e){}
    }
    function createOrGetSequence(mainItem,job){
        var seq=null;
        if(job.premiere.create_new_sequence || !app.project.activeSequence){
            seq=app.project.createNewSequenceFromClips(job.premiere.sequence_name,[mainItem],app.project.rootItem);
            if(!seq) throw new Error("Không tạo được sequence từ video chính.");
            activateSequence(seq);
            log("✓ Tạo sequence: "+seq.name);
        }else{
            seq=app.project.activeSequence;
            try{ seq.overwriteClip(mainItem,0,job.premiere.main_video_track||0,job.premiere.main_audio_track||0); }
            catch(e){
                try{ seq.videoTracks[job.premiere.main_video_track||0].overwriteClip(mainItem,0); }
                catch(_){ throw e; }
            }
            log("✓ Dùng active sequence: "+seq.name);
        }
        return seq;
    }

    function ensureTracks(seq,minV,minA){
        var guard=0;
        while((seq.videoTracks.numTracks<minV || seq.audioTracks.numTracks<minA) && guard<12){
            guard++;
            try{
                app.enableQE();
                var q=qe.project.getActiveSequence();
                if(!q || !q.addTracks) break;
                q.addTracks();
            }catch(e){ log("⚠ Không tự thêm track bằng QE: "+err(e)); break; }
        }
        return {v:seq.videoTracks.numTracks,a:seq.audioTracks.numTracks};
    }
    function clampTrack(idx,count){ idx=Math.max(0,parseInt(idx,10)||0); return Math.min(idx,Math.max(0,count-1)); }

    function projectNodeId(item){ try{return String(item.nodeId);}catch(_){return "";} }
    function findTrackItem(track,projectItem,startSec){
        if(!track) return null; var wanted=projectNodeId(projectItem), best=null, bestD=999999;
        for(var i=0;i<track.clips.numItems;i++){
            var c=track.clips[i]; if(!c) continue;
            try{
                var pid=projectNodeId(c.projectItem);
                if(wanted && pid!==wanted) continue;
                var d=Math.abs(c.start.seconds-startSec); if(d<bestD){best=c;bestD=d;}
            }catch(_e){}
        }
        return best;
    }
    function setEnd(item,endSec){ try{ item.end=timeObj(endSec); return true; }catch(_){ return false; } }
    function setDisabled(item,state){ try{ item.disabled=!!state; return true; }catch(_){ return false; } }

    function setComponentValue(trackItem,componentNames,propertyNames,value){
        try{
            var comps=trackItem.components;
            for(var ci=0;ci<comps.numItems;ci++){
                var comp=comps[ci], cn=String(comp.displayName||comp.name||"").toLowerCase();
                var cmatch=false;
                for(var c=0;c<componentNames.length;c++) if(cn.indexOf(componentNames[c])>=0){cmatch=true;break;}
                if(!cmatch) continue;
                var props=comp.properties;
                for(var pi=0;pi<props.numItems;pi++){
                    var p=props[pi], pn=String(p.displayName||p.name||"").toLowerCase();
                    var pmatch=false;
                    for(var n=0;n<propertyNames.length;n++) if(pn.indexOf(propertyNames[n])>=0){pmatch=true;break;}
                    if(!pmatch) continue;
                    try{ p.setValue(value,true); return true; }catch(e1){ try{ p.setValue(value); return true; }catch(e2){} }
                }
            }
        }catch(e){}
        return false;
    }
    function setScale(item,scale){ return setComponentValue(item,["motion","chuyển động"],["scale","tỷ lệ","ty le"],safeNum(scale,100)); }

    function overwrite(seq,item,seconds,vIndex,aIndex){
        try{ seq.overwriteClip(item,seconds,vIndex,aIndex); return true; }
        catch(e1){
            try{ seq.videoTracks[vIndex].overwriteClip(item,seconds); return true; }
            catch(e2){ throw e1; }
        }
    }
    function overwriteAudio(seq,item,seconds,aIndex){
        try{ seq.audioTracks[aIndex].overwriteClip(item,seconds); return true; }
        catch(e1){ try{ seq.overwriteClip(item,seconds,0,aIndex); return true; }catch(e2){ throw e1; } }
    }

    function prepareMainForBackground(seq,mainItem,job){
        var counts=ensureTracks(seq,2,1), mainTrack=clampTrack(1,counts.v);
        if(mainTrack===0){ log("⚠ Không có V2; bỏ qua layout nền."); return; }
        try{
            overwrite(seq,mainItem,0,mainTrack,0);
            var clone=findTrackItem(seq.videoTracks[mainTrack],mainItem,0);
            if(clone){
                var scaled=setScale(clone,job.background.main_scale_percent||82);
                if(!scaled) log("⚠ Không set được Motion Scale cho video chính.");
            }
            var original=findTrackItem(seq.videoTracks[0],mainItem,0);
            if(original) setDisabled(original,true);
            log("✓ Video chính → V"+(mainTrack+1)+"; V1 dành cho background.");
        }catch(e){ log("⚠ Không chuyển video chính lên V2: "+err(e)); }
    }

    function insertBackground(seq,mainItem,job,opts){
        if(opts.skipBackground || !job.background.enabled) return;
        var paths=job.background.files||[]; if(!paths.length) return;
        var items=importMany(paths,240); if(!items.length) return;
        prepareMainForBackground(seq,mainItem,job);
        var counts=ensureTracks(seq,2,3); var v=clampTrack(job.premiere.background_video_track||0,counts.v); var a=clampTrack(2,counts.a);
        var total=safeNum(job.video.duration_sec,0), scene=Math.max(2,safeNum(job.background.scene_seconds,8));
        var t=0,idx=0,inserted=0;
        while(t<total && inserted<240){
            var item=items[idx%items.length], len=Math.min(scene,total-t);
            try{
                overwrite(seq,item,t,v,a);
                var ti=findTrackItem(seq.videoTracks[v],item,t); if(ti) setEnd(ti,t+len);
                inserted++;
            }catch(e){ log("⚠ Background "+(idx+1)+" lỗi: "+err(e)); }
            idx++; t+=len;
        }
        try{ seq.audioTracks[a].setMute(1); }catch(_){ try{seq.audioTracks[a].setMute(true);}catch(__){} }
        log("✓ Background: "+inserted+" cảnh.");
    }

    function insertBgm(seq,job,opts){
        if(opts.skipBgm || !job.bgm.enabled) return;
        var paths=job.bgm.files||[]; if(!paths.length) return;
        var item=importOne(paths[0]); var counts=ensureTracks(seq,1,2); var a=clampTrack(job.bgm.audio_track||1,counts.a);
        try{
            overwriteAudio(seq,item,0,a);
            var ti=findTrackItem(seq.audioTracks[a],item,0); if(ti && job.video.duration_sec) setEnd(ti,job.video.duration_sec);
            log("✓ BGM → A"+(a+1)+" (gain "+job.bgm.db+" dB chưa ép tự động trên bridge 2021).");
        }catch(e){ log("⚠ BGM lỗi: "+err(e)); }
    }

    function insertLogo(seq,job,opts){
        if(opts.skipBrand || !job.branding.logo_enabled || !job.branding.logo_path) return;
        var item=importOne(job.branding.logo_path); var counts=ensureTracks(seq,5,1); var v=clampTrack(job.premiere.logo_video_track||4,counts.v);
        try{
            seq.videoTracks[v].overwriteClip(item,0);
            var ti=findTrackItem(seq.videoTracks[v],item,0);
            if(ti){ if(job.video.duration_sec) setEnd(ti,job.video.duration_sec); setScale(ti,20); }
            log("✓ Logo → V"+(v+1));
        }catch(e){ log("⚠ Logo lỗi: "+err(e)); }
    }

    function importVoice(job,opts){
        if(opts.skipBrand) return;
        var files=job.branding.voice_files||[]; if(!files.length) return;
        importMany(files,50); log("✓ Import "+Math.min(50,files.length)+" voice/audio vào Project panel.");
    }

    function textParamSet(trackItem,text){
        var comp=null;
        try{ comp=trackItem.getMGTComponent(); }catch(_){ comp=null; }
        if(!comp) return false;
        var props=comp.properties, preferred=["source text","text","title","headline","message","caption","văn bản","van ban"];
        var order=[];
        for(var i=0;i<props.numItems;i++){
            var p=props[i], name=String(p.displayName||p.name||"").toLowerCase(), rank=99;
            for(var k=0;k<preferred.length;k++) if(name.indexOf(preferred[k])>=0){rank=k;break;}
            order.push({p:p,name:name,rank:rank});
        }
        order.sort(function(a,b){return a.rank-b.rank;});
        for(var j=0;j<order.length;j++){
            var prop=order[j].p, current=null;
            try{ current=prop.getValue(); }catch(_g){}
            try{ prop.setValue(String(text),true); return true; }catch(e1){
                try{ prop.setValue(String(text)); return true; }catch(e2){}
            }
            if(typeof current==="string" && current.charAt(0)==="{"){
                try{
                    var escText=String(text).replace(/\\/g,"\\\\").replace(/"/g,'\\"').replace(/\r?\n/g,'\\n');
                    var changed=current;
                    changed=changed.replace(/("textEditValue"\s*:\s*")[^"]*(")/,"$1"+escText+"$2");
                    changed=changed.replace(/("mText"\s*:\s*")[^"]*(")/,"$1"+escText+"$2");
                    if(changed!==current){ try{prop.setValue(changed,true);return true;}catch(_j){try{prop.setValue(changed);return true;}catch(__j){}} }
                }catch(_x){}
            }
        }
        return false;
    }

    function addMarkers(seq,events){
        var lim=Math.min(events.length,100), made=0;
        for(var i=0;i<lim;i++){
            try{
                var ev=events[i], m=seq.markers.createMarker(ev.start); m.name=String(ev.text).substr(0,80); m.comments=String(ev.text); m.end=ev.end; made++;
            }catch(_e){}
        }
        log("✓ Fallback markers: "+made);
    }

    function insertText(seq,job,mogrtPath,opts){
        if(opts.skipText || !job.text_templates.enabled) return;
        var events=job.text_templates.events||[]; if(!events.length){log("Text Templates bật nhưng không có event.");return;}
        if(!mogrtPath || !(new File(mogrtPath)).exists){
            var msg="Mẫu "+job.text_templates.template_id+" chưa gán file MOGRT.";
            if(opts.stopOnTextError) throw new Error(msg);
            log("⚠ "+msg+" Dùng marker fallback."); addMarkers(seq,events); return;
        }
        var counts=ensureTracks(seq,(job.premiere.text_video_track||3)+1,1), v=clampTrack(job.premiere.text_video_track||3,counts.v);
        var ok=0,textSet=0;
        for(var i=0;i<events.length;i++){
            var ev=events[i];
            try{
                var t=timeObj(ev.start);
                var trackItem=seq.importMGT(mogrtPath,t.ticks,v,0);
                if(!trackItem) throw new Error("importMGT không trả TrackItem");
                setEnd(trackItem,ev.end);
                if(textParamSet(trackItem,ev.text)) textSet++; else if(opts.stopOnTextError) throw new Error("Không tìm thấy text parameter trong MOGRT");
                ok++;
            }catch(e){ log("⚠ Text FX "+(i+1)+"/"+events.length+" lỗi: "+err(e)); if(opts.stopOnTextError) throw e; }
        }
        log("✓ Text Templates: "+ok+"/"+events.length+" MOGRT; thay text "+textSet+"/"+ok+".");
    }

    api.systemCheck=function(){
        try{
            var v=String(app.version||"?");
            var project=!!app.project, seq=project?app.project.activeSequence:null;
            var importMgt=!!(seq && seq.importMGT);
            var createSeq=!!(project && app.project.createNewSequenceFromClips);
            return "OK|Premiere "+v+" | CEP/ExtendScript OK | Project "+(project?"OK":"NO")+" | Sequence "+(seq?"OK":"chưa mở")+" | createNewSequenceFromClips "+(createSeq?"OK":"NO")+" | importMGT "+(importMgt?"OK":"sẽ kiểm tra sau khi có sequence");
        }catch(e){ return "ERR|"+err(e); }
    };

    api.buildJobFromFile=function(jobPath,mogrtPath,optionsRaw){
        api.logs=[];
        try{
            if(!app.project) throw new Error("Hãy mở một Premiere Project trước.");
            var major=parseInt(String(app.version||"0").split(".")[0],10)||0;
            if(major && major<15) throw new Error("Cần Premiere Pro 2021 (15.x) trở lên. Máy đang chạy "+app.version);
            var job=parseObject(readText(jobPath));
            if(!job || job.schema!=="pr-auto-job-v1") throw new Error("Job schema không hỗ trợ.");
            var opts={}; try{opts=parseObject(optionsRaw||"{}");}catch(_o){opts={};}
            log("=== PR AUTO CEP BUILD 2021+ ===");
            log("Premiere: "+app.version);
            var mainItem=importOne(job.video.path);
            var seq=createOrGetSequence(mainItem,job);
            ensureTracks(seq,5,3);
            insertBackground(seq,mainItem,job,opts);
            insertBgm(seq,job,opts);
            insertLogo(seq,job,opts);
            importVoice(job,opts);
            insertText(seq,job,mogrtPath,opts);
            try{ seq.setPlayerPosition(timeObj(0).ticks); }catch(_p){}
            try{ app.project.save(); }catch(_s){}
            log("=== HOÀN TẤT ===");
            return "OK|"+api.logs.join("\n");
        }catch(e){
            log("BUILD FAILED: "+err(e));
            return "ERR|"+api.logs.join("\n");
        }
    };

    return api;
})();