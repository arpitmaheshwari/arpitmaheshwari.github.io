JSON.stringify((()=>{
  // Per-LINE rects, not union boxes. An inline element that wraps returns one
  // bounding box spanning every line it touches, which overlaps its neighbours
  // on those lines — that artifact reported 4 pages of phantom defects. A Range
  // over the element's own text nodes yields one rect per RENDERED line.
  const lineRects=(el)=>{
    const out=[];
    for(const n of el.childNodes){
      if(n.nodeType!==3||!n.textContent.trim()) continue;
      const r=document.createRange(); r.selectNodeContents(n);
      for(const cr of r.getClientRects())
        if(cr.width>4&&cr.height>4) out.push({l:cr.left,t:cr.top+scrollY,r:cr.right,b:cr.bottom+scrollY});
    }
    return out;
  };
  const leaf=[...document.querySelectorAll('body *')].filter(e=>{
    if(e.children.length) return false;
    if((e.textContent||'').trim().length<2) return false;
    const s=getComputedStyle(e);
    if(s.visibility==='hidden'||s.display==='none'||parseFloat(s.opacity)<0.1) return false;
    if(s.position==='fixed'||s.position==='absolute') return false;
    return true;
  });
  const items=leaf.map(e=>({e,rects:lineRects(e),txt:e.textContent.trim().slice(0,26)})).filter(x=>x.rects.length);
  const hits=[];
  for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++){
    const A=items[i],B=items[j];
    if(A.e.contains(B.e)||B.e.contains(A.e)) continue;
    for(const a of A.rects)for(const b of B.rects){
      const ox=Math.min(a.r,b.r)-Math.max(a.l,b.l), oy=Math.min(a.b,b.b)-Math.max(a.t,b.t);
      if(ox>3&&oy>3){
        const area=ox*oy, small=Math.min((a.r-a.l)*(a.b-a.t),(b.r-b.l)*(b.b-b.t));
        if(area/small>0.30){ hits.push({a:A.txt,b:B.txt,pct:Math.round(100*area/small)}); }
      }
    }
  }
  const uniq=[]; const seen=new Set();
  for(const h of hits){const k=h.a+'|'+h.b; if(!seen.has(k)){seen.add(k);uniq.push(h);}}
  return uniq.slice(0,6);})())
