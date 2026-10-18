(function(){
  const D=JSON.parse(document.getElementById('data').textContent);
  const COL={AB:'#0090ae',Balto:'#C4820A',Vintage:'#7b6ca8'}, LBL={AB:'A / B Class',Balto:'Balto Capital',Vintage:'Vintage-C'};
  const mf=D.buildings.filter(b=>!b.sfh), sfh=D.buildings.filter(b=>b.sfh);
  const podById={}; D.pods.forEach(p=>podById[p.id]=p);
  const byCode={}; mf.forEach(b=>{if(b.code!=null)byCode[String(b.code)]=b;});
  const doors=b=>b.dispUnits||b.units||0;
  const num=n=>n==null?'—':Number(n).toLocaleString();
  const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const ll=b=>b.lat+','+b.lng;
  const dirTo=b=>'https://www.google.com/maps/dir/?api=1&destination='+ll(b);
  const dirAB=(a,b)=>'https://www.google.com/maps/dir/?api=1&origin='+ll(a)+'&destination='+ll(b)+'&travelmode=driving';
  const mins=(a,b)=>{const r=D.minutes[String(a.code)];return r?r[String(b.code)]:undefined;};
  const fmtMin=m=>m==null?'—':(m<60?m+' min':Math.floor(m/60)+' h '+String(m%60).padStart(2,'0')+' min');
  const btn='display:inline-block;margin-top:7px;padding:6px 10px;border-radius:7px;background:var(--teal,#0090ae);color:#fff;font-weight:700;font-size:11.5px;text-decoration:none';
  const lnk='color:var(--teal,#0090ae);font-size:10.5px;text-decoration:none;white-space:nowrap';
  // ---- HEADER STATS ----
  document.getElementById('s-d').textContent=mf.reduce((a,b)=>a+doors(b),0).toLocaleString();
  document.getElementById('s-b').textContent=mf.length;
  document.getElementById('s-p').textContent=D.pods.filter(p=>mf.some(b=>b.pod===p.id)).length;
  document.getElementById('s-u').textContent=sfh.length.toLocaleString();
  const map=L.map('map',{zoomControl:true}).setView([53.4,-113.5],6); window._map=map;
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',{maxZoom:16,attribution:'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'}).addTo(map);
  const segLayers={AB:L.layerGroup().addTo(map),Balto:L.layerGroup().addTo(map),Vintage:L.layerGroup().addTo(map)},sfhLayer=L.layerGroup(),pts=[];
  const rad=v=>Math.max(5,Math.min(26,2+Math.sqrt(v||0)*1.25));
  function driveList(b,list){
    return list.map(o=>'<div class="lrow"><span>'+esc(o.x.name)+'</span><span style="display:flex;gap:8px;align-items:baseline"><b>'+fmtMin(o.m)+'</b><a style="'+lnk+'" href="'+dirAB(b,o.x)+'" target="_blank" rel="noopener">route ↗</a></span></div>').join('');
  }
  function popup(b){
    const p=podById[b.pod]||{};
    const hasM=!!D.minutes[String(b.code)];
    const others=mf.filter(x=>x!==b).map(x=>({x:x,m:mins(b,x)})).filter(o=>o.m!=null).sort((a,c)=>a.m-c.m);
    const mates=others.filter(o=>o.x.pod===b.pod);
    const near=others.filter(o=>o.x.pod!==b.pod).slice(0,4);
    const off=D.office[String(b.code)];
    return '<div class="pl">'+esc(b.name)+(b.leaseup?' · <span style="color:#1f9d6b">lease-up</span>':'')+'</div>'+
      '<div style="color:#4a5b6b;font-size:11px;margin-bottom:5px">'+esc(b.addr||'')+' · '+LBL[b.seg]+'</div>'+
      '<div class="lrow"><span>Doors</span><b>'+num(doors(b))+'</b></div>'+
      (b.phaseNote?'<div class="lrow"><span>Phasing</span><b style="color:#C4820A">'+esc(b.phaseNote)+'</b></div>':'')+
      '<div class="lrow"><span>Pod</span><b>'+esc(p.name||'—')+'</b></div>'+
      (off!=null?'<div class="lrow"><span>Drive to ZEN office</span><b>'+fmtMin(off)+'</b></div>':'')+
      '<a style="'+btn+'" href="'+dirTo(b)+'" target="_blank" rel="noopener">🧭 Directions to here</a>'+
      (hasM?(
        '<div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#4a5b6b;margin:9px 0 2px;font-weight:700">Drive time to pod-mates</div>'+
        (mates.length?driveList(b,mates):'<div style="font-size:11px;color:#4a5b6b">Only building in this pod.</div>')+
        (near.length?'<details class="acc"><summary>Nearest buildings in other pods</summary>'+driveList(b,near)+'</details>':'')
      ):'<div style="font-size:10.5px;color:#4a5b6b;margin-top:7px">No measured drive times for this building yet.</div>');
  }
  window._mk=[];window._mkPods={};
  mf.forEach(b=>{const m=L.circleMarker([b.lat,b.lng],{radius:rad(doors(b)),weight:b.leaseup?2.5:1,color:b.leaseup?'#1f9d6b':'#fff',fillColor:COL[b.seg],fillOpacity:.82});
    m._base={weight:b.leaseup?2.5:1,color:b.leaseup?'#1f9d6b':'#fff'};window._mk.push({n:b.name+' '+(b.addr||''),name:b.name,m:m,lat:b.lat,lng:b.lng});(window._mkPods[b.pod]=window._mkPods[b.pod]||[]).push(m);
    m.bindTooltip('<b>'+esc(b.name)+'</b> · '+num(doors(b))+' doors');
    m.bindPopup(()=>popup(b),{maxWidth:300}); segLayers[b.seg].addLayer(m); pts.push([b.lat,b.lng]);});
  sfh.forEach(b=>{const m=L.circleMarker([b.lat,b.lng],{radius:4,weight:1,color:'#fff',fillColor:'#6b7a88',fillOpacity:.75});
    m.bindPopup('<div class="pl">'+esc(b.name)+'</div>'+esc(b.addr)+'<br>SFH division'+(b.pod>=0&&podById[b.pod]?' · '+esc(podById[b.pod].name):'')+'<br><a style="'+btn+'" href="'+dirTo(b)+'" target="_blank" rel="noopener">🧭 Directions to here</a>');
    window._mk.push({n:b.name+' '+(b.addr||''),name:b.name,m:m,lat:b.lat,lng:b.lng});sfhLayer.addLayer(m);});map.addLayer(sfhLayer);
  if(pts.length){window._pts=pts;const _fit=()=>{map.invalidateSize();map.fitBounds(pts,{padding:[40,40],maxZoom:11});};_fit();let _fn=0;const _fi=setInterval(()=>{const s=map.getSize();if(s.x>0&&s.y>0){_fit();clearInterval(_fi);}else if(++_fn>60)clearInterval(_fi);},250);}
  const segC={};['AB','Balto','Vintage'].forEach(s=>{const bl=mf.filter(b=>b.seg===s);segC[s]={n:bl.length,d:bl.reduce((a,b)=>a+doors(b),0)};});
  document.getElementById('segs').innerHTML=['AB','Balto','Vintage'].map(s=>'<div class="seg" data-layer="'+s+'"><span class="sw" style="background:'+COL[s]+'"></span>'+LBL[s]+'<span class="d">'+segC[s].n+' bldgs · '+segC[s].d.toLocaleString()+' doors</span></div>').join('');
  const pn={},pu={};mf.forEach(b=>{pn[b.pod]=(pn[b.pod]||0)+1;pu[b.pod]=(pu[b.pod]||0)+doors(b);});const ps={};sfh.forEach(b=>{if(b.pod>=0)ps[b.pod]=(ps[b.pod]||0)+1;});
  // furthest measured pair inside a pod = the worst drive between any two of its buildings
  const furthest=bl=>{let best=null;for(let i=0;i<bl.length;i++)for(let j=i+1;j<bl.length;j++){const m=mins(bl[i],bl[j]);if(m!=null&&(!best||m>best.m))best={m:m,a:bl[i],b:bl[j]};}return best;};
  const podCard=(p)=>{
    const bl=mf.filter(b=>b.pod===p.id).sort((a,b)=>doors(b)-doors(a));
    const fp=furthest(bl), anchor=bl[0];
    const rows=bl.map(b=>{const m=(anchor&&b!==anchor)?mins(anchor,b):null;return '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;padding:4px 0;border-top:1px dashed var(--line,#e5e9ee);font-size:11.5px"><span>'+esc(b.name)+(b.leaseup?' ◇':'')+'</span><span style="white-space:nowrap;display:flex;gap:8px;align-items:baseline"><span><b>'+num(doors(b))+'</b> doors'+(b.phaseNote?' <span style="color:#C4820A;font-size:9.5px">('+esc(b.phaseNote)+')</span>':'')+'</span>'+(m!=null?'<span style="color:var(--ink2);font-size:10.5px">'+fmtMin(m)+'</span>':'')+'<a style="'+lnk+'" href="'+dirTo(b)+'" target="_blank" rel="noopener">directions ↗</a></span></div>';}).join('');
    return '<div class="pod" data-pod="'+p.id+'"><div><div class="nm">'+esc(p.name)+'</div><div class="meta">'+pn[p.id]+' bldgs'+(ps[p.id]?' · '+ps[p.id]+' SFH':'')+(fp?' · furthest pair <b>'+fmtMin(fp.m)+'</b>':'')+'</div></div><div class="doors"><b>'+pu[p.id].toLocaleString()+'</b><span>doors</span></div></div>'+
      '<div class="podx" data-podx="'+p.id+'" style="display:none;padding:8px 12px 12px;background:var(--card,#fff);border-radius:0 0 10px 10px;margin:-6px 0 8px">'+
      (fp?'<div style="font-size:11px;color:var(--ink2);margin:2px 0 4px">Furthest pair: '+esc(fp.a.name)+' ↔ '+esc(fp.b.name)+' — <b>'+fmtMin(fp.m)+'</b> · <a style="'+lnk+'" href="'+dirAB(fp.a,fp.b)+'" target="_blank" rel="noopener">route ↗</a></div>':'')+
      (bl.length>1&&anchor?'<div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2);margin:6px 0 2px">Drive times from '+esc(anchor.name)+' (largest building)</div>':'')+
      '<div>'+rows+'</div>'+(function(){const sh=sfh.filter(b=>b.pod===p.id);return '<details style="margin-top:6px"><summary style="font-size:11px;cursor:pointer;color:var(--ink2)">🏠 SFH in this pod — '+sh.length+(sh.length?'':' (none)')+'</summary>'+(sh.length?'<div style="font-size:10.5px;max-height:150px;overflow:auto">'+sh.map(b=>'<div style="padding:2px 0;border-top:1px dashed var(--line,#e5e9ee);display:flex;justify-content:space-between;gap:6px"><span>'+esc(b.name)+(b.rp?' <b style="color:#7b6ca8">RENTAL POOL · '+b.rpUnits+'u</b>':'')+' — '+esc((b.addr||'').slice(0,52))+'</span><a style="'+lnk+'" href="'+dirTo(b)+'" target="_blank" rel="noopener">↗</a></div>').join('')+'</div>':'')+'</details>';})()+'</div>';
  };
  const GRP=p=>(['Edmonton','Sherwood Park','St. Albert'].indexOf(p.metro)>=0?'Edmonton Metro':(['Calgary','Cochrane'].indexOf(p.metro)>=0?'Calgary Metro':'Saskatchewan'));
  document.getElementById('podlist').innerHTML='<div class="msec" style="border:0"><h3>Pods by market — click a pod for buildings, drive times + directions</h3></div>'+['Edmonton Metro','Calgary Metro','Saskatchewan'].map(g=>{const gp=D.pods.filter(p=>pn[p.id]&&GRP(p)===g).sort((a,b)=>pu[b.id]-pu[a.id]);if(!gp.length)return '';const gb=gp.reduce((a,p)=>a+pn[p.id],0),gu=gp.reduce((a,p)=>a+pu[p.id],0),gs=gp.reduce((a,p)=>a+(ps[p.id]||0),0);return '<div style="margin:12px 0 6px;padding:7px 10px;background:var(--ink,#12222e);color:#fff;border-radius:8px;font-size:11px;letter-spacing:.1em;text-transform:uppercase;display:flex;justify-content:space-between"><b>'+g+'</b><span>'+gb+' bldgs · <b>'+gu.toLocaleString()+'</b> doors'+(gs?' · '+gs+' SFH':'')+'</span></div>'+gp.map(podCard).join('');}).join('');
  document.querySelectorAll('.pod').forEach(el=>el.addEventListener('click',()=>{const id=el.dataset.pod;const x=document.querySelector('.podx[data-podx="'+id+'"]');if(x)x.style.display=(x.style.display==='none'?'block':'none');Object.keys(window._mkPods).forEach(k=>window._mkPods[k].forEach(m=>m.setStyle(m._base)));(window._mkPods[id]||[]).forEach(m=>m.setStyle({weight:3,color:'#C4820A'}));const p=podById[+id];if(p&&p.centroid)map.setView(p.centroid,12);}));
  (function(){const inp=document.getElementById('bsearch'),res=document.getElementById('bsres');if(!inp)return;
   inp.addEventListener('input',()=>{const q=inp.value.trim().toLowerCase();if(q.length<2){res.innerHTML='';return;}const hits=window._mk.filter(x=>x.n.toLowerCase().indexOf(q)>=0).slice(0,12);res.innerHTML=hits.map(x=>'<div class="bsr" data-i="'+window._mk.indexOf(x)+'" style="padding:6px 8px;border-bottom:1px dashed var(--line,#e5e9ee);cursor:pointer;font-size:12px">'+esc(x.n.slice(0,64))+'</div>').join('')||'<div style="padding:6px 8px;font-size:11px;color:var(--ink2)">no match</div>';res.querySelectorAll('.bsr').forEach(r=>r.addEventListener('click',()=>{const x=window._mk[+r.dataset.i];map.setView([x.lat,x.lng],15);x.m.openPopup();res.innerHTML='';inp.value=x.name;}));});})();
  document.querySelectorAll('.seg').forEach(t=>t.addEventListener('click',()=>{const k=t.dataset.layer,ly=k==='sfh'?sfhLayer:segLayers[k];if(!ly)return;const off=t.classList.toggle('off');if(off)map.removeLayer(ly);else map.addLayer(ly);}));
})();
