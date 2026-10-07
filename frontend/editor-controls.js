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
