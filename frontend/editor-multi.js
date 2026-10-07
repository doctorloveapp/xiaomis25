'use strict';
const S5Multi=(()=>{
 let members=new Set();
 function sync(layers){
  const valid=new Set(layers.map(e=>e.id));members=new Set([...members].filter(id=>valid.has(id)));
  if(selected&&!members.has(selected))members=new Set([selected]);
  if(!selected)members.clear();
 }
 function pick(id,additive=false,preserve=false){
  if(additive){if(members.has(id))members.delete(id);else members.add(id);selected=members.has(id)?id:([...members].at(-1)||'');}
  else {if(!preserve||!members.has(id))members=new Set([id]);selected=id;}
 }
 function clear(){members.clear();selected='';paint();}
 function inspector(){
  if(members.size<2)return;
  const box=document.createElement('div');box.className='multi-controls card p-3 mb-4';
  box.innerHTML=`<div class="flex justify-between items-center"><strong>${members.size} livelli selezionati</strong><button class="btn" data-clear-selection>Deseleziona</button></div><p class="text-[11px] text-slate-400 mt-2">Ctrl + clic aggiunge o rimuove livelli. Trascina o usa le frecce per spostare il gruppo. Allinea il gruppo al quadrante:</p><div class="multi-align">${[['left','Sinistra'],['center-x','Centro X'],['right','Destra'],['top','Alto'],['center-y','Centro Y'],['bottom','Basso']].map(([id,label])=>`<button class="btn" data-align-group="${id}">${label}</button>`).join('')}</div>`;
  $('properties').prepend(box);box.querySelector('[data-clear-selection]').onclick=clear;
  box.querySelectorAll('[data-align-group]').forEach(button=>button.onclick=()=>send('align-group',{ids:[...members],alignment:button.dataset.alignGroup,variantOnly}));
 }
 function gesture(event){
  const layers=state.layers.filter(e=>members.has(e.id));
  if(layers.some(e=>e.locked)){toast('Sblocca tutti i livelli selezionati prima di spostare il gruppo.');paint();return;}
  const sx=event.clientX,sy=event.clientY;let dx=0,dy=0;
  const move=ev=>{
   const scale=480/$('canvas').getBoundingClientRect().width;
   let xmin=-8192,xmax=8192,ymin=-8192,ymax=8192;
   for(const e of layers){const image=e.kind==='image',low=image?-state.maxImageSize:0;
    xmin=Math.max(xmin,low-e.x);xmax=Math.min(xmax,(image?state.maxImageSize:Math.max(0,480-e.width))-e.x);
    ymin=Math.max(ymin,low-e.y);ymax=Math.min(ymax,(image?state.maxImageSize:Math.max(0,480-e.height))-e.y);}
   dx=Math.max(xmin,Math.min(xmax,Math.round((ev.clientX-sx)*scale)));dy=Math.max(ymin,Math.min(ymax,Math.round((ev.clientY-sy)*scale)));
   for(const e of layers){const overlay=$('overlays').querySelector(`[data-element="${e.id}"]`);if(overlay)Object.assign(overlay.style,{left:(e.x+dx)/480*100+'%',top:(e.y+dy)/480*100+'%'});}
  };
  const done=ev=>{window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',done);window.removeEventListener('pointercancel',done);if(ev.type!=='pointercancel'&&(dx||dy))send('move-group',{ids:[...members],dx,dy,variantOnly});else paint();};
  window.addEventListener('pointermove',move);window.addEventListener('pointerup',done);window.addEventListener('pointercancel',done);
 }
 return {sync,pick,clear,inspector,gesture,has:id=>members.has(id),ids:()=>[...members]};
})();
