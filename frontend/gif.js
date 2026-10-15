/* Editable GIF frame controls. Decoding and validation are handled in Python. */
const S5Gif={
 status(e){
  const count=e.gif_frames.filter(f=>f.included).length,limit=state.gifFrameLimit||10,over=!e.aod&&count>limit;
  return {count,limit,over,message:e.aod?'GIF statica nell’AOD: viene esportato solo il primo fotogramma incluso.':over?'Limite superato: massimo 10 fotogrammi inclusi per GIF. Deseleziona fotogrammi per esportare.':'Limite rispettato. I fotogrammi esclusi non entrano nel ZIP.'};
 },
 properties(e){
  const thumbnails=state.gifThumbnails?.[e.id]||[],status=this.status(e);
  return `<div class="card p-3 mt-3"><span class="field">Animazione GIF</span>${field('Velocità (%)','gif_speed',e.gif_speed,'number','min="25" max="400" step="1"')}<p class="text-[10px] text-slate-500 mt-2">100%: velocità originale. Massimo 25 fotogrammi al secondo. L’AOD mostra il primo fotogramma incluso.</p><button id="gif-play" class="btn w-full mt-3">${state.gifPreview?'Ferma anteprima GIF':'Avvia anteprima GIF'}</button><div class="gif-export-limit ${status.over?'over':''}" role="status"><strong data-gif-count>${esc(t('{count} / {limit} fotogrammi inclusi',{count:status.count,limit:status.limit}))}</strong><p data-gif-limit-message>${esc(t(status.message))}</p></div><div class="flex justify-between items-center mt-4"><span class="field">Fotogrammi</span><span class="text-[10px] text-slate-400" data-gif-total>${status.count} / ${e.gif_frames.length}</span></div><p class="text-[10px] text-slate-500 mb-2">Deseleziona i fotogrammi da escludere. Clicca un’immagine per esaminarla.</p><div class="gif-frames">${e.gif_frames.map((f,i)=>`<div class="gif-frame ${f.included?'':'excluded'}"><button type="button" data-gif-inspect="${i}" title="Mostra fotogramma"><img src="${thumbnails[i]||''}" alt="${i+1}"></button><label><input type="checkbox" data-gif-frame="${i}" ${f.included?'checked':''}><span>${i+1} · ${f.duration} ms</span></label></div>`).join('')}</div><button id="gif-remove" class="btn danger w-full mt-3" ${e.gif_frames.every(f=>f.included)?'disabled':''}>Elimina fotogrammi esclusi</button><p class="text-[10px] text-slate-500 mt-2">Le modifiche valgono anche per l’esportazione. Annulla ripristina i fotogrammi eliminati.</p></div>`;
 },
 refresh(id){
  const root=document.getElementById('properties'),e=state.layers.find(layer=>layer.id===id);
  if(root.dataset.layerId!==id||!e||e.kind!=='gif'||!root.querySelector('.gif-frames'))return false;
  const status=this.status(e);
  root.querySelectorAll('[data-gif-frame]').forEach(input=>{input.checked=e.gif_frames[Number(input.dataset.gifFrame)].included;input.closest('.gif-frame').classList.toggle('excluded',!input.checked);});
  root.querySelector('.gif-export-limit').classList.toggle('over',status.over);
  root.querySelector('[data-gif-count]').textContent=t('{count} / {limit} fotogrammi inclusi',{count:status.count,limit:status.limit});
  root.querySelector('[data-gif-limit-message]').textContent=t(status.message);
  root.querySelector('[data-gif-total]').textContent=status.count+' / '+e.gif_frames.length;
  document.getElementById('gif-remove').disabled=e.gif_frames.every(frame=>frame.included);
  return true;
 },
 bind(e){
  const play=document.getElementById('gif-play');if(!play)return;
  play.onclick=()=>send('gif-preview',{value:!state.gifPreview});
  document.querySelectorAll('[data-gif-frame]').forEach(input=>input.onchange=()=>send('gif-frame',{id:e.id,index:Number(input.dataset.gifFrame),included:input.checked}));
  document.querySelectorAll('[data-gif-inspect]').forEach(button=>button.onclick=()=>send('gif-inspect',{id:e.id,index:Number(button.dataset.gifInspect)}));
  document.getElementById('gif-remove').onclick=()=>send('gif-remove',{id:e.id});
 }
};
