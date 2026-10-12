# S5 Studio 2.3 — Aggiornamenti Crono Pro e decimi fluidi

## Uso

1. Apri `S5Studio-2.3.exe` e il progetto esistente.
2. Mantieni **Crono Pro** attivo nella scheda della lancetta grande secondi.
3. Seleziona la lancetta piccola con sorgente **Decimi crono**. Attiva **Movimento Fluido** per la rotazione a 25 fps; disattivalo per dieci posizioni al secondo. **Decimi continui** resta un'animazione indipendente dal cronografo.
4. Verifica in anteprima Prepara → Avvia → Ferma → Rientro. Allo Stop confronta la lettura numerica con le lancette. Riesporta lo ZIP e reinstallalo sull'S5: gli ZIP già compilati conservano il vecchio runtime.

Il flag usa il campo esistente `smooth_seconds`, salvato separatamente per livello e stile. Non si migra né si azzera una preferenza precedente. Se era già attivo ma ignorato durante Running nella 2.1, ora abilita la fluidità dei decimi Pro. Centesimi/Millesimi POST non acquisiscono un flag di movimento continuo.

### Lettura dei decimi — aggiornamento della stessa versione 2.3

Per **Decimi crono · Start/Stop/Reset** e **Decimi continui** è disponibile **Lettura dei decimi → Singola cifra / Frazione completa**, salvata nel campo esistente `post_readout` e indipendente per stile. Nei decimi la frazione completa del secondo ha una sola cifra: entrambe le scelte rappresentano 0–9 decimi. Esempio: a 0,456 s la cifra è 4 in entrambi i casi, mentre nei centesimi la frazione completa è 45 e la singola cifra 5.

Il cambio della lettura dei decimi non azzera la scala, non cambia l'arco e non disattiva Movimento Fluido. Con la fluidità attiva la posizione può essere intermedia fra due tacche, come già collaudato nella 2.3. La riscalatura 100/1000 → 10 al cambio di lettura rimane riservata ai POST. Il runtime Lua non è modificato: il nuovo controllo rende accessibile una preferenza già presente nei progetti e nei binding Pro esportati.

## Scheduling e misura

`s5studio/lua/studio_core_pro.lua` conserva la macchina a stati e il clock scelto dal runtime: tick monotono LVGL, clock `/proc/uptime`, oppure fase dell'animazione LVGL. Non risultano API verificate che pubblichino un evento ufficiale `elapsedMs`; la soluzione utilizza il callback `Anim.exec_cb` già supportato. Nel fallback il callback aggiorna `engineTick` dalla differenza di fase, quindi chiama `refresh(clock())`. Con clock diretto la fase è soltanto una notifica di fotogramma: il tempo viene letto dal clock monotono, conservandone l'origine e la gestione del wrap a 32 bit.

Quando esistono decimi Pro, Running è guidato dal callback. Lo stesso vale per il fallback Anim anche senza decimi. I due handle Timer già presenti restano sospesi in questo percorso; il Timer Running ha periodo 1000 ms e non viene creato un Timer indipendente da 100 ms. Le scene senza decimi con clock diretto mantengono il percorso lento a 1000 ms; il relativo timer dell'ora civile a riposo conserva il comportamento precedente.

`refresh` filtra i callback in base a intervalli del tempo trascorso: 40 ms con almeno una lancetta decimi fluida, 100 ms con soli decimi a scatti, 1000 ms senza decimi. Non conta le invocazioni per ricostruire il tempo. Se il firmware salta un fotogramma, il successivo raggiunge il tempo reale disponibile senza accumulare ritardo. La cache `view.rendered` evita i `Pointer:set` ripetuti sullo stesso valore, comprese le ombre. Ore/minuti crono, POST e secondi grandi non vengono riscritti inutilmente a ogni fotogramma.

Il target 25 fps non garantisce 25 fotogrammi renderizzati al secondo sul dispositivo. Nei decimi a scatti un motore a 40 ms può alternare intervalli visivi di 80/120 ms, poiché 100 non è multiplo di 40. È rimosso il doppio campionamento Timer/Anim; non viene alterata la risoluzione fisica del clock dell'S5.

## Posizioni e Stop

Con `elapsed` in millisecondi, i decimi fluidi usano `(elapsed % 1000) / 1000 * valueRange`; quelli a scatti usano `floor((elapsed % 1000) / 100) / 10 * valueRange`. Il valore iniziale, la scala, il pivot, la grafica e le ombre restano quelli del progetto. La lancetta grande crono usa sempre `floor(elapsed / 1000) % 60`, indipendentemente dal suo flag per l'ora civile. Ore/minuti crono mantengono i divisori 3600000 e 60000.

Stop cattura un solo `elapsed` per tutto il gruppo. Esempio: a 1,456 s i decimi fluidi indicano 4,56 sulla scala 0–10, quelli a scatti 4, i POST completi 45 e 456. La cifra numerica Decimi 4 è la parte intera, non una diversa misura. Dopo Stop la lancetta fluida resta ferma anche tra due tacche. I POST raggiungono la lettura con la transizione esistente; il Reset coordina tutte le lancette con gli stessi 720 ms e il verso precedente. Gli archi POST restano entro la scala calibrata, anche antioraria.

## AOD e ciclo di vita

Le guardie `active`, `screenOn` e proprietario della scena impediscono a callback sospesi o vecchi di scrivere. All'ingresso AOD il runtime ferma clock Anim, aggiornamenti e transizioni; il grafo AOD nativo rimane privo dei secondi e delle lancette crono. Alla riattivazione il clock riprende secondo la strategia precedente: clock monotono quando disponibile, tempo civile a precisione di un secondo per la sospensione del fallback. Il cambio stile sospende il controller precedente; la cancellazione della scena ferma anche l'animazione del clock. Il cronografo classico `studio_core.lua` è invariato.

### Aggiornamento 12 ottobre — sessioni lunghe Bulova

L'utente ha segnalato ore crono ferme oltre 60 minuti mentre i minuti avevano completato il giro. Formula delle ore e binding Bulova risultano corretti. Due livelli possono usare lo stesso modello del catalogo/PNG: le rotazioni restano indipendenti.

Corretti due punti in `studio_core_pro.lua`: il primo `sleepWall` viene conservato attraverso sospensioni ripetute; al passaggio inattivo → attivo si invalida `view.rendered` per reinviare una volta le posizioni. Il primo difetto perdeva tempo AOD con `pageOnResume` prima di ON. Il secondo evita che una posa persa dal renderer rimanga errata fino al successivo cambio del dato, particolarmente lento per le ore. La perdita della posa è stata simulata, non osservata sul firmware: **il sintomo reale specifico resta da confermare**. Cache e frequenze normali, transizioni, POST e schermata AOD sono conservati. [Analisi e prova richiesta](VERIFICA_BULOVA_ORE_CRONO.md).

## Tacche e compilazione

`s5studio/native.py` e `s5studio/lua_runtime.py` aggiungono `_ticks.png` soltanto quando `show_ticks` è vero. Con il flag falso non viene rasterizzata l'immagine e non esiste il relativo nodo Image nel progetto compilato. Posizioni, ordine e risorse delle lancette non cambiano. La scelta è per livello/stile/schermata: un AOD con tacche abilitate conserva le proprie tacche.

Il `build-report.json` conserva i controlli interattivi e aggiunge `chronoPro.decisecondMovement`: sorgente callback, assenza del Timer indipendente da 100 ms, target 25 fps, dieci posizioni a scatti e flag effettivo per ogni lancetta/stile. `mainSecondsStepped` e `chronoHoursMinutesStepped` documentano i vincoli del conteggio. La validazione confronta il flag del progetto con il binding Lua compilato. `runningSmoothForcedOff` è falso nella nuova architettura perché esiste l'eccezione esplicita dei decimi; i report di runtime precedenti mantengono il significato storico.

Corretto anche `applicationVersion`: rapporto esterno e incorporato derivano dalla versione dell'applicazione (2.3), eliminando l'etichetta fissa 2.1. Gli hash dei moduli incorporati distinguono questa revisione dai pacchetti precedenti.

## Verifiche e limiti

Superati **137 test mirati**: 115 prove precedenti più 22 su sospensione, cache e grafica condivisa. Il selettore dei decimi conserva i **12 controlli dell'editor sui sorgenti** già eseguiti; la UI non è cambiata nella correzione della ripresa. Eseguiti test Lua tramite Lupa e compilazioni EasyFace temporanee senza ZIP dimostrativi, oltre a quattro scenari fino a 13 ore sul binario temporaneo del vero Bulova. Due test di packaging ZIP completo non sono stati rieseguiti: grafo binario, manifest interattivo, script incorporati, POST e AOD sono verificati nei test di compilazione selezionati.

Le prove coprono 25 posizioni fluide o dieci scatti in un secondo simulato, cache delle scritture, clock diretto e fallback, tick wrap, Stop comune, minuti/ore, transizioni, AOD/ripresa, cambio scena, ombre e flag salvati. La UI verifica il checkbox reale, riapertura del progetto, cadenza anteprima 40/100 ms e lettura POST. Il packaging ripete la sincronizzazione dei set personali: 9 set, 623 modelli, cataloghi sorgente conservati.

L'eseguibile è stato creato e verificato staticamente, senza avviarlo: 760 risorse incorporate, tutti i 40 moduli Python del pacchetto presenti nel bundle, entry point e cinque moduli Lua corrispondenti ai sorgenti. **Fluidità della prima 2.3 confermata sul dispositivo:** decimi fluidi e nessun lag più riscontrato nei secondi grandi. [Esito precedente](hardware-test-2.3.json). La successiva segnalazione Bulova e le protezioni della ripresa richiedono un nuovo test reale, escluso dalla conferma precedente. Fps e consumo non sono misurati. Il percorso nativo dei secondi civili è invariato; il beneficio di RAM/fps dell'omissione delle tacche non è quantificato.

[Risultati test](validation-editor-2.3.json) · [Editor](editor-2.3.json) · [Bundle](executable-build-2.3.json)
