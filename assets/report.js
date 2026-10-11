/* Offline teaching modules. Geometry and photometry have independent states. */
(() => {
  "use strict";
  const data = JSON.parse(document.getElementById("astro-data").textContent);
  const $ = id => document.getElementById(id);
  const num = id => Number($(id).value);
  const NS = "http://www.w3.org/2000/svg";
  const make = (tag, attrs = {}, text = null) => {
    const e = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
    if (text !== null) e.textContent = text;
    return e;
  };
  const add = (svg, tag, attrs, text) => svg.appendChild(make(tag, attrs, text));
  const fmt = x => Math.abs(x) < 1e-10 ? "0" : Number(x.toPrecision(3)).toString();
  function plot(id, bounds, xlabel, ylabel) {
    const svg = $(id); svg.replaceChildren();
    const [xmin, xmax, ymin, ymax] = bounds;
    const x = v => 64 + 320 * (v - xmin) / (xmax - xmin);
    const y = v => 340 - 320 * (v - ymin) / (ymax - ymin);
    const clipId = id + "-clip";
    const defs = add(svg, "defs", {});
    const clip = add(defs, "clipPath", {id: clipId});
    add(clip, "rect", {x: 64, y: 20, width: 320, height: 320});
    add(svg, "rect", {x: 64, y: 20, width: 320, height: 320, class: "plot-frame"});
    for (let i = 0; i <= 4; i++) {
      const xv = xmin + i * (xmax-xmin)/4, yv = ymin + i*(ymax-ymin)/4;
      add(svg, "line", {x1:x(xv), x2:x(xv), y1:20, y2:340, class:"grid-line"});
      add(svg, "line", {x1:64, x2:384, y1:y(yv), y2:y(yv), class:"grid-line"});
      add(svg, "text", {x:x(xv), y:360, "text-anchor":"middle", class:"tick"}, fmt(xv));
      add(svg, "text", {x:54, y:y(yv)+4, "text-anchor":"end", class:"tick"}, fmt(yv));
    }
    if (xmin < 0 && xmax > 0) add(svg, "line", {x1:x(0), x2:x(0), y1:20, y2:340, class:"zero-line"});
    if (ymin < 0 && ymax > 0) add(svg, "line", {x1:64, x2:384, y1:y(0), y2:y(0), class:"zero-line"});
    add(svg, "text", {x:224,y:388,"text-anchor":"middle",class:"axis-label"}, xlabel);
    add(svg, "text", {x:18,y:180,transform:"rotate(-90 18 180)","text-anchor":"middle",class:"axis-label"}, ylabel);
    const layer = add(svg, "g", {"clip-path":`url(#${clipId})`});
    return {svg, layer, x, y, scale:320/(xmax-xmin), bounds};
  }
  const path = (p, points, cls) => add(p.layer, "path", {
    d:points.map(([a,b],i) => `${i?"L":"M"}${p.x(a).toFixed(3)},${p.y(b).toFixed(3)}`).join(" "), class:cls
  });
  const point = (p,x,y,cls,r=4) => add(p.layer,"circle",{cx:p.x(x),cy:p.y(y),r,class:cls});
  function circle(p,x,y,r,cls) {
    add(p.layer,"circle",{cx:p.x(x),cy:p.y(y),r:r*p.scale,class:cls});
  }
  function analytic(u) {
    if (!(u > 0) || !Number.isFinite(u)) throw Error("点源距离必须为正；u=0 有解析奇点。");
    return (u*u+2)/(u*Math.sqrt(u*u+4));
  }
  function interpolate(u,rho) {
    if (!Number.isFinite(u) || u < 0 || u > 10) throw Error("超出 u∈[0,10]；拒绝外推。");
    if (rho === 0) return analytic(u);
    const table = Object.values(data.tables).find(t => t.rho === rho);
    if (!table) throw Error("ρ 没有对应离散数值表。");
    let lo=0, hi=table.u.length-1;
    while (hi-lo>1) { const mid=(hi+lo)>>1; if(table.u[mid]<=u) lo=mid; else hi=mid; }
    const f=(u-table.u[lo])/(table.u[hi]-table.u[lo]);
    return table.A[lo]*(1-f)+table.A[hi]*f;
  }
  const flux = (a,fs) => 1+fs*(a-1);
  function single() {
    const tau=num("single-time"), u0=num("single-u0"), te=num("single-te"), rho=num("single-rho"), fs=num("single-fs");
    if (!(Math.abs(tau)<=6 && u0>=.02 && u0<=2 && te>=.01 && te<=.1 && fs>=0 && fs<=1)) throw Error("参数超出已验证控制范围。");
    [["time",tau,2],["u0",u0,2],["te",te,4],["fs",fs,2]].forEach(([n,v,k]) => $("single-"+n+"-value").textContent=v.toFixed(k));
    const p=plot("single-geometry",[-10,10,-10,10],"x / θE（单透镜）","y / θE（单透镜）");
    path(p,[[-6,u0],[6,u0]],"trajectory"); circle(p,0,0,1,"einstein"); point(p,0,0,"lens",4);
    if(rho>0) circle(p,tau,u0,rho,"source-disk"); point(p,tau,u0,"current",5);
    path(p,[[0,0],[tau,u0]],"separation");
    add(p.svg,"text",{x:72,y:37,class:"plot-note"},`u=${Math.hypot(tau,u0).toFixed(3)} · ρ=${rho}`);
    const points=[], ps=[], count=600;
    for(let i=0;i<=count;i++) {
      const t=-6+12*i/count, u=Math.hypot(t,u0);
      points.push([t*te,flux(interpolate(u,rho),fs)]);
      ps.push([t*te,flux(analytic(u),fs)]);
    }
    const obs=data.observations, show=$("single-points").checked;
    let max=Math.max(...points.map(p=>p[1]));
    let min=1;
    if(show) {max=Math.max(max,...obs.flux.map((v,i)=>v+obs.sigma[i])); min=Math.min(min,...obs.flux.map((v,i)=>v-obs.sigma[i]));}
    const ceiling=Math.max(1.12,max + .12*(max-min));
    const xlim=Math.max(6*te,show ? Math.max(...obs.time_days.map(Math.abs))+.004 : 0);
    const c=plot("single-curve",[-xlim,xlim,min-.025,ceiling],"Δt = t − t₀（天）","F / Fbase");
    path(c,ps,"analytic"); path(c,points,"model");
    if(show) obs.time_days.forEach((t,i) => {
      path(c,[[t,obs.flux[i]-obs.sigma[i]],[t,obs.flux[i]+obs.sigma[i]]],"error-bar");
      point(c,t,obs.flux[i],"observation",2.6);
    });
    const f=flux(interpolate(Math.hypot(tau,u0),rho),fs), time=tau*te;
    path(c,[[time,c.bounds[2]],[time,c.bounds[3]]],"time-line");point(c,time,f,"current",5);
    const clipped=Math.max(...ps.map(p=>p[1]))>ceiling;
    add(c.svg,"text",{x:72,y:37,class:"plot-note"},rho ? "均匀源积分 · 插值" : "点源 · 解析计算");
    if(clipped) add(c.svg,"text",{x:72,y:56,class:"plot-note"},"点源虚线峰值超出纵轴；未裁改数据");
    $("single-status").textContent=`Δt=${time.toFixed(5)} 天 · F/Fbase=${f.toFixed(5)} · ${rho?"插值":"解析"}`;
    $("single-lens").dataset.state=JSON.stringify({tau,u0,te,rho,fs,time,flux:f});
  }
  function atlas(s,q) {
    const found=Object.values(data.atlas).find(v=>Math.abs(v.s-s)<1e-10 && v.q===q);
    if(!found) throw Error("没有该 s、q 的已计算图谱；拒绝插值。"); return found;
  }
  function branch(p,entry,field,cls) {
    // A root track at 2π may end on a different 0-phase root.
    for(let b=0;b<4;b++) {
      const points=entry[field].map(row=>row[b]);
      points.push(entry[field][0][entry.end_permutation[b]]);
      path(p,points,cls);
    }
  }
  function squareBounds(entries,field,extras=[]) {
    const points=entries.flatMap(e=>e[field].flat()).concat(extras);
    const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
    const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
    const cx=(xmin+xmax)/2,cy=(ymin+ymax)/2,half=Math.max(xmax-xmin,ymax-ymin,.15)*.60;
    return [cx-half,cx+half,cy-half,cy+half];
  }
  function binary() {
    const s=num("binary-s"),q=num("binary-q"),angle=num("binary-angle"),impact=num("binary-impact"),view=$("binary-view").value;
    if(!(Math.abs(angle)<=90 && Math.abs(impact)<=.3) || !["full","central"].includes(view)) throw Error("示意轨迹或视域参数无效。");
    const current=atlas(s,q), comparison=atlas(1/s,q);
    $("binary-angle-value").textContent=angle.toFixed(0)+"°";
    $("binary-impact-value").textContent=impact.toFixed(2);
    const z1=-s*q/(1+q),z2=s/(1+q);
    const p=plot("binary-critical",squareBounds([current],"z",[[z1,0],[z2,0]]),"Re(z) / θE,total","Im(z) / θE,total");
    branch(p,current,"z","critical");
    [z1,z2].forEach((z,i) => {point(p,z,0,"lens",i?3:5);path(p,[[z-.04,0],[z+.04,0]],"lens-mark");path(p,[[z,-.04],[z,.04]],"lens-mark");});
    const bounds=view==="central"?[-.3,.3,-.3,.3]:squareBounds([current,comparison],"caustic",[[0,0]]);
    const r=angle*Math.PI/180,span=Math.max(...bounds.map(Math.abs))*2;
    const trajectory=[-span,span].map(t=>[t*Math.cos(r)-impact*Math.sin(r),t*Math.sin(r)+impact*Math.cos(r)]);
    [["binary-caustic",current],["binary-compare",comparison]].forEach(([id,e])=>{
      const c=plot(id,bounds,"Re(ζ) / θE,total","Im(ζ) / θE,total");
      branch(c,e,"caustic","caustic");path(c,trajectory,"trajectory");
      point(c,-impact*Math.sin(r),impact*Math.cos(r),"schematic-point",3);
      add(c.svg,"text",{x:72,y:37,class:"plot-note"},`s=${fmt(e.s)} · q=${q}`);
      if(view==="central") add(c.svg,"text",{x:72,y:56,class:"plot-note"},"中心裁窗；外部焦散可能未显示");
    });
    $("binary-primary-title").textContent=`源平面 · s=${fmt(s)} 的焦散`;
    $("binary-compare-title").textContent=`源平面 · 1/s=${fmt(1/s)} 的焦散`;
    $("binary-status").textContent=`s=${fmt(s)} ↔ ${fmt(1/s)} · q=${q} · max |det J|=${current.max_abs_det_j.toExponential(2)}${s===1?" · s=1 的倒数仍为 1":""}`;
    $("binary-lens").dataset.state=JSON.stringify({s,q,angle,impact,view,z1,z2,comparison_s:comparison.s});
  }
  function guarded(name,update) {
    try {update();$(name+"-error").hidden=true;}
    catch(e) {
      $(name+"-error").textContent=e.message;$(name+"-error").hidden=false;
      $(name+"-lens").querySelectorAll("svg").forEach(svg=>svg.replaceChildren());
      $(name+"-status").textContent="无法计算，请恢复教学初值。";
      delete $(name+"-lens").dataset.state;
    }
  }
  const resets={};
  function mount(name,update,defaults) {
    const section=$(name+"-lens"); if(!section) return;
    section.querySelectorAll("input,select").forEach(input=>input.addEventListener("input",()=>guarded(name,update)));
    resets[name]=()=>{
      Object.entries(defaults).forEach(([id,value])=>{const e=$(name+"-"+id);if(e.type==="checkbox") e.checked=value;else e.value=value;});
      guarded(name,update);
    };
    guarded(name,update);
  }
  mount("single",single,{time:0,u0:.59,te:.0288,rho:"3.39",fs:1,points:true});
  mount("binary",binary,{s:.8,q:.1,view:"full",angle:20,impact:.06});
  // Pure numeric functions exposed for independent Python↔browser agreement tests.
  window.AstroXray=Object.freeze({analytic,interpolate,reset:name=>resets[name]()});
})();
