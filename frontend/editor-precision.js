'use strict';
window.S5Precision=(()=>{
 let zoom=100,space=false;
 const $=id=>document.getElementById(id),levels=[50,75,100,125,150,200,300,400];
 function setZoom(value,clientX,clientY){
  const viewport=$('stage-viewport'),canvas=$('canvas'),before=canvas.getBoundingClientRect(),v=viewport.getBoundingClientRect();
  const px=clientX??v.left+v.width/2,py=clientY??v.top+v.height/2;
  const fractionX=(px-before.left)/before.width,fractionY=(py-before.top)/before.height;
  zoom=Math.max(50,Math.min(400,Number(value)));canvas.style.width=canvas.style.height=(480*zoom/100)+'px';
  const after=canvas.getBoundingClientRect();viewport.scrollLeft+=after.left+fractionX*after.width-px;viewport.scrollTop+=after.top+fractionY*after.height-py;
  $('preview-zoom').value=String(zoom);$('preview-zoom')._refreshStudioLabel?.();
  $('zoom-out').disabled=zoom<=50;$('zoom-in').disabled=zoom>=400;
 }
 function centre(e){
  const viewport=$('stage-viewport'),v=viewport.getBoundingClientRect(),c=$('canvas').getBoundingClientRect();
  viewport.scrollLeft+=c.left+(e?(e.x+e.width/2)/480:.5)*c.width-(v.left+v.width/2);
  viewport.scrollTop+=c.top+(e?(e.y+e.height/2)/480:.5)*c.height-(v.top+v.height/2);
 }
 function mount(){
  $('preview-zoom').onchange=event=>setZoom(event.target.value);
  $('zoom-out').onclick=()=>setZoom([...levels].reverse().find(v=>v<zoom)??50);
  $('zoom-in').onclick=()=>setZoom(levels.find(v=>v>zoom)??400);
  $('zoom-reset').onclick=()=>{setZoom(100);centre();};
  $('zoom-selection').onclick=()=>centre(state.layers.find(e=>e.id===selected));
  const viewport=$('stage-viewport');
  viewport.addEventListener('wheel',event=>{if(event.ctrlKey){event.preventDefault();setZoom(event.deltaY<0?(levels.find(v=>v>zoom)??400):([...levels].reverse().find(v=>v<zoom)??50),event.clientX,event.clientY);}},{passive:false});
  window.addEventListener('keydown',event=>{if(event.code==='Space'&&!document.activeElement?.matches('input,textarea,select,button,[contenteditable=true]')){space=true;viewport.classList.add('can-pan');event.preventDefault();}});
  window.addEventListener('keyup',event=>{if(event.code==='Space'){space=false;viewport.classList.remove('can-pan');}});
  window.addEventListener('blur',()=>{space=false;viewport.classList.remove('can-pan');});
  viewport.addEventListener('pointerdown',event=>{
   if(event.button!==1&&!space)return;
   event.preventDefault();event.stopPropagation();viewport.setPointerCapture(event.pointerId);
   const start={x:event.clientX,y:event.clientY,left:viewport.scrollLeft,top:viewport.scrollTop};viewport.classList.add('panning');
   const move=ev=>{viewport.scrollLeft=start.left-(ev.clientX-start.x);viewport.scrollTop=start.top-(ev.clientY-start.y);};
   const end=()=>{viewport.removeEventListener('pointermove',move);viewport.removeEventListener('pointerup',end);viewport.removeEventListener('pointercancel',end);viewport.classList.remove('panning');};
   viewport.addEventListener('pointermove',move);viewport.addEventListener('pointerup',end);viewport.addEventListener('pointercancel',end);
  },true);
  setZoom(100);centre();
 }
 function handPreviews(e){
  for(const hand of ['hour','minute','second']){
   const holder=$('pivot-'+hand),preview=state.handPreviews[e.id]?.[hand];if(!holder)continue;
   holder.hidden=!preview;if(!preview)continue;
   holder.innerHTML='<span class="field">Pivot · clicca sulla grafica applicata</span>';
   const button=document.createElement('button');button.type='button';button.className='pivot-preview';button.title='Clicca per impostare il punto di rotazione manuale';button.dataset.pivotHand=hand;
   const width=Math.min(248,210*preview.width/preview.height);button.style.width=width+'px';button.style.aspectRatio=preview.width+'/'+preview.height;
   const img=document.createElement('img');img.src=preview.src;img.alt='Grafica applicata: scegli il punto di rotazione';button.append(img);
   const marker=document.createElement('span');marker.className='pivot-crosshair';marker.style.left=(preview.pivotX+.5)/preview.width*100+'%';marker.style.top=(preview.pivotY+.5)/preview.height*100+'%';button.append(marker);
   button.onclick=event=>{
    const rect=img.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>=rect.right||event.clientY<rect.top||event.clientY>=rect.bottom)return;
    const x=preview.originX+Math.floor((event.clientX-rect.left)/rect.width*preview.width),y=preview.originY+Math.floor((event.clientY-rect.top)/rect.height*preview.height);
    if(x<0||y<0||x>=480||y>=480){toast('Scegli un punto nella grafica o nel suo margine valido.');return;}
    send('hand-pivot',{id:e.id,hand,x,y,asset:preview.asset,variantOnly});
   };
   holder.append(button);
   const caption=document.createElement('p');caption.className='pivot-caption';caption.textContent='Croce = perno attuale. Il clic imposta X e Y e disattiva il perno automatico.';holder.append(caption);
  }
 }
 return {mount,setZoom,centre,handPreviews,getZoom:()=>zoom};
})();
