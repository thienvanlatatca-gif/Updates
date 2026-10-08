/* global TxtToSrt */
(function (root) {
    "use strict";
    var fs=null,path=null;
    try{fs=require("fs");path=require("path");}catch(e){}
    function needNode(){if(!fs||!path)throw new Error("C1 Builder cần CEP Node.js để đọc transcript.");}
    function readText(p){return fs.readFileSync(p,"utf8").replace(/^\uFEFF/,"");}
    function normalizeCues(caps){
        var out=[];
        for(var i=0;i<(caps||[]).length;i++){
            var c=caps[i]||{},start=Number(c.start),end=Number(c.end),text=String(c.text||"").trim();
            if(!isFinite(start)||!isFinite(end)||end<=start||!text)continue;
            out.push({number:out.length+1,start:start,end:end,text:text});
        }
        return out;
    }
    function parseText(content){
        if(!root.TxtToSrt||!root.TxtToSrt.parseTxt)throw new Error("TxtToSrt parser chưa được nạp.");
        return normalizeCues(root.TxtToSrt.parseTxt(String(content||"")));
    }
    function fromFile(filePath){
        needNode();
        if(!filePath||!fs.existsSync(filePath))throw new Error("Không tìm thấy nguồn timeline: "+filePath);
        var cues=parseText(readText(filePath));
        if(!cues.length)throw new Error("Nguồn timeline đã tìm thấy nhưng không parse được cue SRT/VTT hợp lệ: "+path.basename(filePath));
        var maxEnd=0;for(var i=0;i<cues.length;i++)maxEnd=Math.max(maxEnd,cues[i].end);
        return {cues:cues,sourcePath:filePath,cueCount:cues.length,maxEnd:maxEnd};
    }
    function toSrt(cues){
        var caps=[];for(var i=0;i<(cues||[]).length;i++)caps.push({start:cues[i].start,end:cues[i].end,text:cues[i].text});
        return root.TxtToSrt.captionsToSrt(caps);
    }
    var api={parseText:parseText,fromFile:fromFile,toSrt:toSrt,normalizeCues:normalizeCues};
    root.C1Builder=api;
    if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof window!=="undefined"?window:(typeof global!=="undefined"?global:this));
