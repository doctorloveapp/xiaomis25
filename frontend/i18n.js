'use strict';
// Source-language message IDs preserve Italian fallback and project identifiers.
window.S5I18n=(()=>{
 let language='it',base={},messages={},patterns=[],observer=null,pending=new Set(),scheduled=false;
 const originals=new WeakMap(),attributes=new WeakMap();
 const protectedSelector='[data-i18n-skip],script,style,textarea,#project-title,#current-style,#editing-style,.user-content,select[data-preset],#compass-preset';
 const escapeRegex=value=>value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 function interpolate(value,parameters={}){return value.replace(/\{(\w+)\}/g,(whole,key)=>Object.hasOwn(parameters,key)?String(parameters[key]):whole);}
 function t(key,parameters={}){return interpolate(String(Object.hasOwn(messages,key)?messages[key]:Object.hasOwn(base,key)?base[key]:key),parameters);}
 function translateText(value){
  const leading=value.match(/^\s*/)[0],trailing=value.match(/\s*$/)[0],source=value.trim();
  if(!source)return value;
  if(Object.hasOwn(messages,source)||Object.hasOwn(base,source))return leading+t(source)+trailing;
  for(const item of patterns){const match=source.match(item.regex);if(match){const params={};item.keys.forEach((key,i)=>params[key]=match[i+1]);return leading+t(item.key,params)+trailing;}}
  return value;
 }
 function skipped(element){return !element||Boolean(element.closest(protectedSelector));}
 function text(node){
  if(skipped(node.parentElement))return;
  let saved=originals.get(node);
  if(!saved||node.nodeValue!==saved.rendered)saved={source:node.nodeValue,rendered:node.nodeValue};
  const rendered=translateText(saved.source);saved.rendered=rendered;originals.set(node,saved);
  if(node.nodeValue!==rendered){node.nodeValue=rendered;const select=node.parentElement.closest('select');if(select)select._refreshStudioLabel?.();}
 }
 function element(node){
  if(skipped(node))return;
  if(node.dataset.i18n){
   const translated=t(node.dataset.i18n);
   if(node.textContent!==translated)node.textContent=translated;
   // Explicit keys own this leaf; generic traversal must not reverse its text.
   for(const child of node.childNodes)if(child.nodeType===Node.TEXT_NODE)originals.set(child,{source:base[node.dataset.i18n]??node.dataset.i18n,rendered:child.nodeValue});
  }
  let saved=attributes.get(node)||{};
  for(const name of ['title','placeholder','aria-label','alt']){
   const value=node.getAttribute(name);if(value===null)continue;
   const key=node.getAttribute('data-i18n-'+name);
   if(!saved[name]||value!==saved[name].rendered)saved[name]={source:value,rendered:value};
   const rendered=key?t(key):translateText(saved[name].source);saved[name].rendered=rendered;
   if(value!==rendered)node.setAttribute(name,rendered);
  }
  attributes.set(node,saved);
 }
 function apply(root=document.body){
  if(!root)return;
  if(root.nodeType===Node.TEXT_NODE){text(root);return;}
  if(root.nodeType===Node.ELEMENT_NODE)element(root);
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT);
  let node;while((node=walker.nextNode())){if(node.nodeType===Node.TEXT_NODE)text(node);else element(node);}
 }
 function observe(){
  if(observer)return;
  observer=new MutationObserver(records=>{
   for(const record of records){if(record.type==='childList')for(const node of record.addedNodes)pending.add(node);else pending.add(record.target);}
   if(!scheduled){scheduled=true;queueMicrotask(()=>{scheduled=false;const nodes=[...pending];pending.clear();nodes.forEach(node=>{if(node.isConnected)apply(node);});});}
  });
  observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['title','placeholder','aria-label','alt']});
 }
 function configure(code,italian,catalog){
  language=['it','en'].includes(code)?code:'it';base=Object.fromEntries(Object.entries(italian||{}).filter(([,v])=>typeof v==='string'));messages={...base,...Object.fromEntries(Object.entries(catalog||{}).filter(([,v])=>typeof v==='string'))};patterns=[];
  for(const key of Object.keys(base)){
   if(!/\{\w+\}/.test(key))continue;
   const keys=[],parts=[];let end=0;
   for(const match of key.matchAll(/\{(\w+)\}/g)){parts.push(escapeRegex(key.slice(end,match.index)),'(.*?)');keys.push(match[1]);end=match.index+match[0].length;}
   parts.push(escapeRegex(key.slice(end)));patterns.push({key,keys,regex:new RegExp('^'+parts.join('')+'$','su')});
  }
  document.documentElement.lang=language;apply();observe();
 }
 return {t,apply,configure,translateText,get language(){return language;}};
})();
