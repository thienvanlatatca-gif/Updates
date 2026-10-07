(function(){
  'use strict';
  var BRIDGE_KEY='prauto.cep.bridge.folder';
  var MOGRT_PREFIX='prauto.cep.mogrt.';
  var currentJob=null;
  var currentJobPath='';
  var selectedCategory='Trending';

  function $(s){ return document.querySelector(s); }
  function log(msg){
    var el=$('#log');
    var line='['+new Date().toLocaleTimeString()+'] '+msg;
    el.textContent += (el.textContent?'\n':'')+line;
    el.scrollTop=el.scrollHeight;
    $('#status').textContent=msg;
  }
  function baseName(p){ return String(p||'').replace(/\\/g,'/').split('/').pop(); }
  function joinPath(a,b){ return String(a||'').replace(/[\\\/]$/,'')+'/'+b; }
  function evalHost(code,cb){
    try{
      if(!window.__adobe_cep__ || !window.__adobe_cep__.evalScript){ throw new Error('CEP evalScript không khả dụng.'); }
      window.__adobe_cep__.evalScript(code,function(res){ cb(String(res||'')); });
    }catch(e){ cb('ERR|'+e.message); }
  }
  function qstr(v){ return JSON.stringify(String(v==null?'':v)); }
  function fsRead(path){
    var r=window.cep.fs.readFile(path);
    if(r.err!==0) throw new Error('CEP FS lỗi '+r.err+': '+path);
    return r.data;
  }
  function chooseFolder(title){
    var r=window.cep.fs.showOpenDialog(false,true,title||'Chọn thư mục',null,[]);
    if(!r || r.err!==0 || !r.data || !r.data.length) return '';
    return r.data[0];
  }
  function chooseMogrt(){
    var r=window.cep.fs.showOpenDialog(false,false,'Chọn file MOGRT',null,['mogrt']);
    if(!r || r.err!==0 || !r.data || !r.data.length) return '';
    return r.data[0];
  }
  function bridgeFolder(){ return localStorage.getItem(BRIDGE_KEY)||''; }
  function mogrtPath(id){ return localStorage.getItem(MOGRT_PREFIX+id)||''; }
  function setMogrt(id,path){ if(path) localStorage.setItem(MOGRT_PREFIX+id,path); else localStorage.removeItem(MOGRT_PREFIX+id); }

  function connectBridge(){
    var p=chooseFolder('Chọn bridge folder của PR Auto');
    if(!p) return;
    localStorage.setItem(BRIDGE_KEY,p);
    $('#bridgeState').textContent='Bridge: '+p;
    log('Đã kết nối bridge folder.');
    loadLatestJob();
  }

  function loadLatestJob(){
    try{
      var folder=bridgeFolder();
      if(!folder) throw new Error('Chưa kết nối bridge folder.');
      var path=joinPath(folder,'latest_job.json');
      var raw=fsRead(path);
      var job=JSON.parse(raw);
      if(job.schema!=='pr-auto-job-v1') throw new Error('Job schema không hỗ trợ: '+job.schema);
      currentJob=job; currentJobPath=path;
      var d=job.diagnostics||{};
      $('#jobState').textContent='✓ '+baseName(job.video.path)+' • '+(d.caption_count||0)+' captions • '+(d.text_event_count||0)+' text FX';
      $('#jobSummary').textContent=[
        'Video: '+job.video.path,
        'Sequence: '+job.premiere.sequence_name,
        'Background: '+(job.background.enabled ? ((job.background.files||[]).length+' files') : 'Tắt'),
        'BGM: '+(job.bgm.enabled ? ((job.bgm.files||[]).length+' files') : 'Tắt'),
        'Logo: '+(job.branding.logo_enabled?'Bật':'Tắt'),
        'Text: '+(job.text_templates.enabled ? (job.text_templates.template_id+' • '+(job.text_templates.events||[]).length+' events') : 'Tắt')
      ].join('\n');
      log('Đã đọc job: '+job.premiere.sequence_name);
    }catch(e){
      currentJob=null; currentJobPath='';
      $('#jobState').textContent='✗ '+e.message;
      log('Không đọc được job: '+e.message);
    }
  }

  function buildJob(){
    if(!currentJob) loadLatestJob();
    if(!currentJob || !currentJobPath) return;
    var t=currentJob.text_templates||{};
    var mpath=t.enabled ? mogrtPath(t.template_id) : '';
    if(t.enabled && !mpath && $('#stopOnTextError').checked){
      log('Mẫu '+t.template_id+' chưa gán MOGRT.'); return;
    }
    var opts={
      skipBackground:$('#skipBackground').checked,
      skipBgm:$('#skipBgm').checked,
      skipBrand:$('#skipBrand').checked,
      skipText:$('#skipText').checked,
      stopOnTextError:$('#stopOnTextError').checked
    };
    $('#buildBtn').disabled=true;
    log('Đang gửi job sang ExtendScript...');
    var code='PRAuto.buildJobFromFile('+qstr(currentJobPath)+','+qstr(mpath)+','+qstr(JSON.stringify(opts))+')';
    evalHost(code,function(res){
      $('#buildBtn').disabled=false;
      if(res.indexOf('OK|')===0) log('✓ '+res.slice(3).replace(/\\n/g,'\n'));
      else log('✗ '+res.replace(/^ERR\|/,''));
    });
  }

  function systemCheck(){
    evalHost('PRAuto.systemCheck()',function(res){
      if(res.indexOf('OK|')===0) log(res.slice(3)); else log('Check lỗi: '+res.replace(/^ERR\|/,''));
    });
  }

  function openSource(url){
    try{ window.cep.util.openURLInDefaultBrowser(url); }
    catch(e){ log('Không mở được link: '+e.message); }
  }

  function assignMogrt(id){
    var p=chooseMogrt(); if(!p) return;
    setMogrt(id,p); log('Đã gán '+id+' → '+baseName(p)); renderTemplates();
  }

  function scoreFile(t,name){
    var n=String(name||'').toLowerCase().replace(/\.mogrt$/,'').replace(/[^a-z0-9]+/g,' ');
    var words=t.name.toLowerCase().split(/\s+/); var s=0;
    if(n.indexOf(t.id.replace(/-/g,' '))>=0) s+=50;
    for(var i=0;i<words.length;i++) if(words[i].length>=4 && n.indexOf(words[i])>=0) s+=10;
    return s;
  }

  function scanMogrtFolder(){
    var folder=chooseFolder('Chọn thư mục chứa MOGRT'); if(!folder) return;
    var r=window.cep.fs.readdir(folder);
    if(!r || r.err!==0){ log('Không đọc được thư mục MOGRT. CEP FS lỗi '+(r?r.err:'?')); return; }
    var files=[]; for(var i=0;i<r.data.length;i++) if(/\.mogrt$/i.test(r.data[i])) files.push(r.data[i]);
    var mapped=0;
    for(var ti=0;ti<TEMPLATE_CATALOG.length;ti++){
      var t=TEMPLATE_CATALOG[ti],best='',bestScore=0;
      for(var fi=0;fi<files.length;fi++){ var sc=scoreFile(t,files[fi]); if(sc>bestScore){bestScore=sc;best=files[fi];} }
      if(best && bestScore>=10){ setMogrt(t.id,joinPath(folder,best)); mapped++; }
    }
    log('Quét '+files.length+' MOGRT, gán '+mapped+'/10 mẫu.'); renderTemplates();
  }

  function renderChips(){
    var cats=['Trending','Kinetic','Modern','Glitch','Cartoon','Neon']; var host=$('#chips'); host.innerHTML='';
    for(var i=0;i<cats.length;i++)(function(c){
      var b=document.createElement('button'); b.className='chip '+(c===selectedCategory?'active':''); b.textContent=c;
      b.onclick=function(){selectedCategory=c;renderChips();renderTemplates();}; host.appendChild(b);
    })(cats[i]);
  }

  function renderTemplates(){
    var q=String($('#searchInput').value||'').toLowerCase(); var grid=$('#templateGrid'); grid.innerHTML=''; var ready=0;
    for(var z=0;z<TEMPLATE_CATALOG.length;z++) if(mogrtPath(TEMPLATE_CATALOG[z].id)) ready++;
    $('#templateReady').textContent='MOGRT '+ready+'/10 đã gán';
    for(var i=0;i<TEMPLATE_CATALOG.length;i++){
      var t=TEMPLATE_CATALOG[i];
      if(t.category.indexOf(selectedCategory)<0) continue;
      if(q && t.name.toLowerCase().indexOf(q)<0 && t.id.indexOf(q)<0) continue;
      var mapped=mogrtPath(t.id);
      var card=document.createElement('div'); card.className='card';
      var pv=document.createElement('div'); pv.className='preview '+t.previewClass;
      var pt=document.createElement('div'); pt.className='previewText'; pt.textContent=t.sample; pv.appendChild(pt);
      var title=document.createElement('div'); title.className='cardTitle'; title.textContent=t.name;
      var badge=document.createElement('div'); badge.className='badge '+(mapped?'ready':''); badge.textContent=mapped?('● '+baseName(mapped)):'○ Chưa gán MOGRT';
      var act=document.createElement('div'); act.className='actions';
      var a=document.createElement('button'); a.textContent=mapped?'Đổi':'Gán'; a.onclick=(function(id){return function(){assignMogrt(id);};})(t.id);
      var d=document.createElement('button'); d.textContent='Tải'; d.onclick=(function(url){return function(){openSource(url);};})(t.source);
      act.appendChild(a); act.appendChild(d); card.appendChild(pv);card.appendChild(title);card.appendChild(badge);card.appendChild(act);grid.appendChild(card);
    }
  }

  function switchTab(name){
    var tabs=document.querySelectorAll('.tab'); for(var i=0;i<tabs.length;i++) tabs[i].classList.toggle('active',tabs[i].getAttribute('data-tab')===name);
    var names=['builder','templates','logs']; for(var j=0;j<names.length;j++) $('#tab-'+names[j]).classList.toggle('hidden',names[j]!==name);
  }

  function init(){
    var folder=bridgeFolder(); if(folder) $('#bridgeState').textContent='Bridge: '+folder;
    $('#connectBridgeBtn').onclick=connectBridge;
    $('#loadJobBtn').onclick=loadLatestJob;
    $('#buildBtn').onclick=buildJob;
    $('#systemBtn').onclick=systemCheck;
    $('#scanFolderBtn').onclick=scanMogrtFolder;
    $('#searchInput').oninput=renderTemplates;
    $('#clearLogBtn').onclick=function(){$('#log').textContent='';};
    var tabs=document.querySelectorAll('.tab'); for(var i=0;i<tabs.length;i++) tabs[i].onclick=function(){switchTab(this.getAttribute('data-tab'));};
    renderChips(); renderTemplates();
    if(folder) loadLatestJob();
    systemCheck();
  }

  document.addEventListener('DOMContentLoaded',init);
})();