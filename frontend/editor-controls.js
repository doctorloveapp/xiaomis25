'use strict';
// A highlighted native popup row must never become a committed Studio value.
// This selector commits only on click or keyboard activation.
window.S5Selectors=(()=>{
  let popup=null,counter=0;
  const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function preview(select,value){
    select.dispatchEvent(new CustomEvent('studio-option-preview',{detail:{value}}));
    if(popup?.select===select&&popup.figure){
      const graphic=select._studioGraphic?.(value),img=popup.figure.querySelector('img'),caption=popup.figure.querySelector('figcaption');
      img.hidden=!graphic;
      if(graphic){img.src=graphic.src;img.alt=graphic.label;caption.textContent=graphic.label;}
      else{img.removeAttribute('src');caption.textContent='Passa su un modello per vedere l’anteprima';}
    }
    if(popup?.select===select&&popup.description)popup.description.textContent=select._studioDescription?.(value)||'Passa su una voce per leggerne il significato.';
  }
  function close(){if(popup){const current=popup;popup=null;current.trigger.setAttribute('aria-expanded','false');current.menu.remove();preview(current.select,current.select.value);}}
  function mount(root=document){
    root.querySelectorAll('select').forEach(select=>{
      if(select.dataset.enhanced){select._refreshStudioLabel();return;}
      select.dataset.enhanced='true';select.classList.add('select-source');select.tabIndex=-1;
      const shell=document.createElement('div');shell.className='select-control';
      if(select.classList.contains('w-36'))shell.style.width='144px';
      select.before(shell);shell.append(select);
      const trigger=document.createElement('button');trigger.type='button';trigger.className='input select-trigger';
      trigger.setAttribute('role','combobox');trigger.setAttribute('aria-expanded','false');trigger.setAttribute('aria-haspopup','listbox');
      const label=select.closest('label')?.querySelector('.field')?.textContent||select.getAttribute('aria-label')||'Scegli un valore';
      trigger.setAttribute('aria-label',label);shell.append(trigger);
      const refresh=()=>{trigger.innerHTML=`<span>${escape(select.selectedOptions[0]?.textContent||'Scegli…')}</span><span aria-hidden="true">⌄</span>`;trigger.disabled=select.disabled;};
      select._refreshStudioLabel=refresh;select.addEventListener('change',refresh);refresh();
      function open(){
        if(popup?.select===select){close();return;}
        close();const menu=document.createElement('div');menu.className='select-popup';menu.id='s5-select-'+(++counter);
        trigger.setAttribute('aria-controls',menu.id);trigger.setAttribute('aria-expanded','true');
        const list=document.createElement('div');list.className='select-options';list.setAttribute('role','listbox');list.setAttribute('aria-label',label);menu.append(list);
        let search=null;
        if(select.options.length>8){search=document.createElement('input');search.type='search';search.className='input select-search';search.placeholder='Cerca…';search.setAttribute('aria-label','Cerca '+label);menu.prepend(search);}
        function populate(filter=''){
          list.innerHTML='';
          [...select.options].filter(o=>o.textContent.toLowerCase().includes(filter.toLowerCase())).forEach(option=>{
            const button=document.createElement('button');button.type='button';button.className='select-option';button.setAttribute('role','option');button.dataset.value=option.value;
            button.disabled=option.disabled;button.setAttribute('aria-selected',String(option.value===select.value));
            button.innerHTML=`<span>${escape(option.textContent)}</span><span class="committed-check">${option.value===select.value?'✓':''}</span>`;
            button.onmouseenter=button.onmouseover=button.onfocus=()=>{
              list.querySelectorAll('.is-hovered').forEach(row=>row.classList.remove('is-hovered'));
              button.classList.add('is-hovered');preview(select,option.value);
            };
            button.onmouseleave=button.onblur=()=>button.classList.remove('is-hovered');
            button.onclick=()=>{const value=option.value;close();trigger.focus();if(select.value!==value){select.value=value;select.dispatchEvent(new Event('change',{bubbles:true}));}};
            list.append(button);
          });
          if(!list.children.length)list.innerHTML='<div class="select-empty">Nessun risultato</div>';
        }
        populate();if(search)search.oninput=()=>populate(search.value);
        menu.onkeydown=event=>{
          if(event.key==='Escape'){event.preventDefault();close();trigger.focus();}
          if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
            event.preventDefault();const options=[...list.querySelectorAll('button:not(:disabled)')];let index=options.indexOf(document.activeElement);
            if(event.key==='Home')index=0;else if(event.key==='End')index=options.length-1;else index=Math.max(0,Math.min(options.length-1,index+(event.key==='ArrowDown'?1:-1)));
            options[index]?.focus();
          }
        };
        let figure=null;
        if(select._studioGraphic){figure=document.createElement('figure');figure.className='select-graphic-preview';figure.innerHTML='<img hidden alt="Anteprima modello"><figcaption>Passa su un modello per vedere l’anteprima</figcaption>';menu.classList.add('with-preview');menu.append(figure);}
        let description=null;
        if(select._studioDescription){description=document.createElement('div');description.className='select-description';description.setAttribute('role','tooltip');menu.classList.add('with-description');menu.append(description);}
        document.body.append(menu);const bounds=trigger.getBoundingClientRect();
        menu.style.width=Math.max(200,Math.min(420,bounds.width+(figure?120:0)))+'px';menu.style.left=Math.max(8,Math.min(bounds.left,window.innerWidth-menu.offsetWidth-8))+'px';
        const height=menu.getBoundingClientRect().height,preferred=bounds.bottom+height+5<window.innerHeight-8?bounds.bottom+5:bounds.top-height-5;
        menu.style.top=Math.max(8,Math.min(preferred,window.innerHeight-height-8))+'px';
        popup={select,trigger,menu,figure,description};preview(select,select.value);
        menu.onmouseleave=()=>{list.querySelectorAll('.is-hovered').forEach(row=>row.classList.remove('is-hovered'));preview(select,select.value);};
      }
      trigger.onclick=event=>{event.preventDefault();open();};
      trigger.onkeydown=event=>{if(['ArrowDown','ArrowUp','Enter',' '].includes(event.key)){event.preventDefault();open();popup?.menu.querySelector('button[aria-selected=true]')?.focus();}};
    });
  }
  document.addEventListener('pointerdown',event=>{if(popup&&!popup.menu.contains(event.target)&&!popup.trigger.contains(event.target))close();});
  document.addEventListener('keydown',event=>{if(event.key==='Escape')close();});
  document.addEventListener('scroll',event=>{if(popup&&!popup.menu.contains(event.target))close();},true);
  window.addEventListener('resize',close);
  return {mount,close,isOpen:()=>Boolean(popup)};
})();

// Every color control uses the same dialog, including project/style colors.
window.S5Colors=(()=>{
 let choosing=false;
 function mountAll(root=document){
  root.querySelectorAll('input[type=color]').forEach(input=>{
   if(input.dataset.studioColorPicker)return;
   const property=input.dataset.prop||'';let target,key,context='layer',identity;
   if(property.startsWith('project-')){context='project';key=property.slice(8);target={background:state.background};}
   else if(property.startsWith('variant-')){context='variant';key=property.slice(8);target=state.variants[state.variantIndex];}
   else{key=property;target=state.layers.find(e=>e.id===selected);identity=target?.id;}
   if(!target||!key)return;
   let absent=target[key]==='none',original=false,cap=false;
   if(context==='variant'&&key==='accent')absent=!target[key]||target[key]==='none';
   if(context==='layer'){
    const role=key.replace(/_color$/,'');
    if(['hour_color','minute_color','second_color'].includes(key)&&['analog','pointer'].includes(target.kind)){
     original=Boolean(target[role+'_asset']);absent=original?!target[key]||target[key]==='none':target[key]==='none';
    }else if(key==='color'&&target.kind==='analog'){cap=true;absent=target.show_center_cap===false;}
    else if(key==='color'&&target.kind==='pointer'){original=Boolean(target.second_asset);absent=original?!target.second_color||target.second_color==='none':target.second_color==='none';}
    else if(key==='color'&&['image','compass','image_values'].includes(target.kind)){original=true;absent=!target.tint;}
   }
   input.dataset.studioColorPicker='true';input.dataset.originalColor=String(absent);
   input.title=absent?(cap?'Tappo centrale nascosto':original?'Colori originali, nessuna ricolorazione':'Nessun colore'):'Clicca per scegliere un colore o Nessun colore';
   if(absent){const caption=document.createElement('small');caption.className='original-color-caption';caption.textContent=cap?'Tappo centrale nascosto':original?'Colore originale':'Nessun colore';input.after(caption);}
   const choose=event=>{event.preventDefault();if(choosing||input.disabled)return;choosing=true;send('choose-color',{context,id:identity,key}).finally(()=>choosing=false);};
   input.onclick=choose;input.onkeydown=event=>{if(['Enter',' '].includes(event.key))choose(event);};
  });
 }
 return {mountAll};
})();
