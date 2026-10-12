# Longine: datari e lancette nella scena Crono Pro — 2.6 aggiornata

**Aggiornamento 2.7:** questa composizione è conservata. I successivi test sull'orologio hanno segnalato un anticipo della lancetta 24h e secondi piccoli fermi con Movimento Fluido. Corretti il troncamento dei contatori Q8 e l'avvio dell'animazione nel nuovo modulo; cronografo e calendario lunare restano invariati. Usare ora **S5Studio-2.7.exe** e riesportare. [Correzioni e verifiche 2.7](EDITOR_2.7.md).

La disposizione del progetto `projects/Longine.s5faceproj` è corretta. L'esportatore precedente aveva una limitazione: tutti gli oggetti Lua fra il primo e l'ultimo livello Lua venivano riuniti in una scena unica. Questo vincolo serve a far condividere lo stesso stato e lo stesso gestore di tap alle lancette del cronografo; non implica che i datari debbano stare sopra le lancette.

Nel Longine il primo oggetto Lua è **Disco moon**, sotto lo sfondo. L'ultimo è **Lancette**, con Crono Pro attivo, sopra gli altri elementi. Fra questi due estremi si trovano, dal basso verso l'alto:

1. Lo sfondo Longines, che maschera parte del disco.
2. **Dato Giorno** (`dateWeek`, nomi inglesi) e **Dato Mese** (`dateMonth`).
3. Ore e minuti del cronografo.
4. La lancetta normale 24h, quella dei secondi normali e il datario a lancetta.

La vecchia scena accettava immagini, testi, forme e alcuni dati numerici trasformati, ma rifiutava i datari testuali e i puntatori nativi. Segnalava per primo Dato Giorno, anche se era correttamente sotto tutte le lancette. Non si trattava di un errore nei valori del progetto, nelle capabilities o nel posizionamento scelto.

## Correzione

Il compilatore ora può inserire nella stessa scena anche i datari testuali e i puntatori con sorgente nativa. Conserva l'ordine completo, compreso il disco dietro lo sfondo. Il modulo aggiunto `studio_scene_data.lua` riceve notifiche `dataman` in Q8 e usa gli stessi nomi di sorgente delle precedenti risorse native:

- `dateWeek` seleziona SUN–SAT, con 0=SUN e 1=MON.
- `dateMonth` seleziona 1–12, mantenendo nomi completi o abbreviati secondo il livello.
- `timeHour24` viene collegato a `timeHour`, mantenendo la scala di 24 valori.
- `timeSecond` aggiorna la lancetta piccola dei secondi normali, anche durante il cronografo.
- `dateDay` aggiorna il datario a lancetta, mantenendo esattamente i valori iniziali, intervalli, pivot, ombre e angoli salvati.

Le immagini dei nomi dei giorni/mesi sono tutte incluse: la data simulata nell'editor non viene fissata nel quadrante. Puntatori e datari non entrano nella lista controllata da Start/Stop/Reset. I sei moduli Lua precedenti, inclusi cronografo e calendario lunare, non vengono modificati.

Per i soli secondi normali con flag fluido attivo, il nuovo collegamento usa un'animazione LVGL di un secondo avviata dalla notifica effettiva dei secondi. Non introduce un timer di polling. All'ingresso in AOD interrompe questa animazione e nasconde gli elementi della scena normale. Pausa/ripresa, cancellazione e notifiche duplicate sono gestite; le scritture di valori identici vengono evitate. Le altre sorgenti native seguono le notifiche senza animazioni aggiunte.

Il controllo preliminare rimane per gli oggetti non ancora integrabili fra i livelli Lua, per esempio un oggetto Ora/Data composito o una complicazione selezionabile. Il messaggio ora precisa questa limitazione. Tali oggetti possono restare esterni alla scena; non vengono spostati automaticamente né convertiti in immagini statiche.

Il `build-report.json` aggiunge `interactive.sceneDynamicData`, con sorgenti, ID, scala, calibrazione, stili e hash del nuovo runtime. Il validatore confronta questi binding con il progetto e verifica il modulo incorporato.

## Verifica e uso

L'esportazione del **progetto Longine originale**, senza correzioni o riordino, è stata completata dal compilatore EasyFace in circa **10,1 secondi**. Verificati ZIP finale, manifest interattivo, binding, indipendenza del disco dal cronografo, esclusione dei secondi dall'AOD e ordine dei livelli nel codice incorporato. L'esportazione di verifica era temporanea ed è stata rimossa; il file utente è rimasto identico, verificato tramite SHA-256. [Rapporto completo](validation-longine-scene-2.6.json).

Superati **90 test mirati** dei sorgenti, che coprono anche scena classica/Pro, varianti indipendenti, calendario dentro una scena solo lunare, scritture duplicate, ombre, rollover dei secondi, AOD, pausa/ripresa e cancellazione. L'eseguibile è stato ispezionato staticamente senza avviarlo: **1.251 risorse, 43 moduli Python e sette moduli Lua** corrispondono ai sorgenti; i sei moduli Lua preesistenti sono identici a quelli dell'EXE 2.5. Le nuove composizioni richiedono conferma sull'orologio: il test del compilatore non verifica il rendering del firmware.

Salva il lavoro e chiudi la vecchia applicazione, poi avvia **S5Studio-2.6-aggiornato.exe** o il launcher aggiornato. Riapri Longine ed esporta con l'ordine dei livelli già scelto. È stato usato un nome EXE distinto perché la 2.6 precedente risultava in esecuzione: non è stata chiusa forzatamente né sovrascritta. Non è stato creato un backup.

Controllati i cataloghi personali: integrati **Longines** e **Longines_Lancette piccole**, per un totale di 11 set personali e 629 modelli di lancette. Cataloghi sorgente e `.gitignore` preservati.
