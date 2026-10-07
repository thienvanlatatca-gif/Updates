const { entrypoints, storage, shell } = require("uxp");
const premiere = require("premierepro");

const fs = storage.localFileSystem;
const TOKEN_PREFIX = "textfx.mogrt.";
const FOLDER_TOKEN_KEY = "textfx.folder.token";
const categories = ["Đang thịnh hành","Kinetic","Glitch","Cartoon","Modern","Neon"];
let selectedCategory = "Đang thịnh hành";
let root = null;

function $(sel){ return root.querySelector(sel); }
function setStatus(message,type=""){ const el=$("#status"); el.textContent=message; el.className=`status ${type}`.trim(); }
function normalizeName(v){ return String(v||"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim(); }
function getToken(id){ return localStorage.getItem(TOKEN_PREFIX+id); }

async function getMappedFile(id){
  const token=getToken(id); if(!token) return null;
  try { const entry=await fs.getEntryForPersistentToken(token); if(entry&&entry.isFile) return entry; }
  catch(e){ localStorage.removeItem(TOKEN_PREFIX+id); }
  return null;
}

async function mapFile(id,file){
  if(!file||!file.isFile) return false;
  const token=await fs.createPersistentToken(file);
  localStorage.setItem(TOKEN_PREFIX+id,token);
  return true;
}

async function chooseMogrtForTemplate(id){
  try{
    const file=await fs.getFileForOpening({types:["mogrt"],allowMultiple:false});
    if(!file) return;
    await mapFile(id,file);
    setStatus(`Đã gán ${file.name}.`,"ok");
    await renderCards();
  }catch(err){ setStatus(`Không gán được MOGRT: ${err.message||err}`,"error"); }
}

function scoreMatch(t,fileName){
  const n=normalizeName(fileName.replace(/\.mogrt$/i,""));
  const title=normalizeName(t.name);
  const words=title.split(" ").filter(w=>w.length>=4);
  let score=n===title?100:0;
  for(const w of words) if(n.includes(w)) score+=10;
  if(n.includes(normalizeName(t.id))) score+=30;
  return score;
}

async function chooseFolderAndAutoMap(){
  try{
    const folder=await fs.getFolder(); if(!folder) return;
    const folderToken=await fs.createPersistentToken(folder);
    localStorage.setItem(FOLDER_TOKEN_KEY,folderToken);
    const entries=await folder.getEntries();
    const mogrts=entries.filter(e=>e.isFile&&/\.mogrt$/i.test(e.name));
    let mapped=0;
    for(const t of TEMPLATE_CATALOG){
      if(getToken(t.id)) continue;
      let best=null,bestScore=0;
      for(const file of mogrts){ const score=scoreMatch(t,file.name); if(score>bestScore){best=file;bestScore=score;} }
      if(best&&bestScore>=10){ await mapFile(t.id,best); mapped++; }
    }
    $("#folderState").textContent=`Thư mục: ${folder.name} • ${mogrts.length} MOGRT • tự gán ${mapped}`;
    setStatus("Đã quét thư viện MOGRT.","ok");
    await renderCards();
  }catch(err){ setStatus(`Không đọc được thư mục: ${err.message||err}`,"error"); }
}

async function restoreFolder(){
  const token=localStorage.getItem(FOLDER_TOKEN_KEY); if(!token) return;
  try{
    const folder=await fs.getEntryForPersistentToken(token);
    if(folder&&folder.isFolder) $("#folderState").textContent=`Thư mục: ${folder.name}`;
  }catch(e){ localStorage.removeItem(FOLDER_TOKEN_KEY); }
}

async function openSource(url){
  try{
    const result=await shell.openExternal(url,"Mở trang tải MOGRT đã chọn");
    if(result) setStatus(`Không mở được trình duyệt: ${result}`,"error");
  }catch(err){ setStatus(`Không mở được nguồn tải: ${err.message||err}`,"error"); }
}

async function insertTemplate(id){
  try{
    const file=await getMappedFile(id);
    if(!file){ setStatus("Mẫu này chưa được gán file .mogrt. Bấm Gán trước.","error"); return; }
    const project=await premiere.Project.getActiveProject();
    if(!project) throw new Error("Không có project Premiere đang mở.");
    const sequence=await project.getActiveSequence();
    if(!sequence) throw new Error("Không có sequence đang active.");
    const playhead=await sequence.getPlayerPosition();
    const trackUI=parseInt($("#trackInput").value,10)||3;
    const videoTrackIndex=Math.max(0,trackUI-1);
    const nativePath=fs.getNativePath(file);
    const editor=premiere.SequenceEditor.getEditor(sequence);
    const inserted=await editor.insertMogrtFromPath(nativePath,playhead,videoTrackIndex,0);
    const count=Array.isArray(inserted)?inserted.length:0;
    setStatus(`Đã chèn ${file.name} tại playhead vào V${trackUI}${count?` • ${count} item`:""}.`,"ok");
  }catch(err){ setStatus(`Chèn MOGRT thất bại: ${err.message||err}`,"error"); }
}

function renderChips(){
  const host=$("#chips"); host.innerHTML="";
  for(const category of categories){
    const b=document.createElement("button");
    b.className=`chip ${selectedCategory===category?"active":""}`;
    b.textContent=category;
    b.addEventListener("click",async()=>{ selectedCategory=category; renderChips(); await renderCards(); });
    host.appendChild(b);
  }
}

async function renderCards(){
  const host=$("#cards");
  const query=normalizeName($("#searchInput").value);
  host.innerHTML="";
  const filtered=TEMPLATE_CATALOG.filter(t=>t.category.includes(selectedCategory)&&(!query||normalizeName(t.name).includes(query)));
  let ready=0;
  for(const t of TEMPLATE_CATALOG) if(await getMappedFile(t.id)) ready++;
  $("#readyCount").textContent=`${ready}/${TEMPLATE_CATALOG.length} mẫu đã gán`;
  $("#sectionTitle").textContent=selectedCategory;

  for(const t of filtered){
    const mapped=await getMappedFile(t.id);
    const card=document.createElement("div"); card.className="card";
    const preview=document.createElement("div"); preview.className=`preview ${t.previewClass}`;
    const txt=document.createElement("div"); txt.className="previewText"; txt.textContent=t.previewText; preview.appendChild(txt);
    const name=document.createElement("div"); name.className="cardName"; name.textContent=t.name;
    const badge=document.createElement("div"); badge.className=`badge ${mapped?"ready":""}`; badge.textContent=mapped?`● ${mapped.name}`:"○ Chưa gán MOGRT";
    const actions=document.createElement("div"); actions.className="cardActions";
    const insert=document.createElement("button"); insert.className="actionBtn primary"; insert.textContent="Chèn"; insert.disabled=!mapped; insert.addEventListener("click",()=>insertTemplate(t.id));
    const map=document.createElement("button"); map.className="actionBtn"; map.textContent=mapped?"Đổi":"Gán"; map.addEventListener("click",()=>chooseMogrtForTemplate(t.id));
    const src=document.createElement("button"); src.className="actionBtn"; src.textContent="Tải"; src.addEventListener("click",()=>openSource(t.source));
    actions.append(insert,map,src);
    card.append(preview,name,badge,actions);
    host.appendChild(card);
  }
}

function setTab(tab){
  root.querySelectorAll(".tab").forEach(b=>b.classList.toggle("active",b.dataset.tab===tab));
  const on=tab==="templates";
  $("#cards").classList.toggle("hidden",!on);
  $("#chips").classList.toggle("hidden",!on);
  root.querySelector(".sectionHeader").classList.toggle("hidden",!on);
  $("#emptyState").classList.toggle("hidden",on);
}

async function init(panelRoot){
  root=panelRoot;
  $("#chooseFolderBtn").addEventListener("click",chooseFolderAndAutoMap);
  $("#searchInput").addEventListener("input",renderCards);
  root.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>setTab(b.dataset.tab)));
  renderChips(); setTab("templates"); await restoreFolder(); await renderCards();
}

entrypoints.setup({panels:{textfxPanel:{create(panelRoot){return init(panelRoot);},show(){if(root)renderCards();}}}});