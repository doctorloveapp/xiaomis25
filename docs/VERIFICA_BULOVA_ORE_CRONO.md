# Verifica Ore Crono Pro ? Bulova, 12 ottobre 2026

**Il test reale resta aperto.** L'utente conferma oltre 60 minuti di conteggio, senza Reset o cambio stile/quadrante, e un giro completo dei minuti con ripartenza, mentre le ore restavano a zero. Non ? quindi sufficiente spiegare il sintomo con il normale avanzamento delle ore intere. Il calcolo e il collegamento della lancetta risultano corretti nelle prove PC. Sono stati corretti un difetto riproducibile di contabilizzazione AOD e una fragilit? della cache grafica alla ripresa; la seconda ? compatibile con un renderer che perda la posizione, condizione simulata ma non acquisita sul firmware S5.

## Progetto, catalogo e binario esaminati

Esaminati `projects/Bulova.s5faceproj` e la compilazione esistente `Quadranti Compilati/Bulova-876008762-20261011-213639`, incluso il Lua estratto direttamente da `resource.bin`. Il progetto dell'utente non ? stato modificato. Hash ed esiti della nuova compilazione temporanea: [bulova-chrono-hours-2.3.json](bulova-chrono-hours-2.3.json).

In entrambi gli stili:

| Livello | ID | Sorgente | Scala | Rotazione |
| --- | --- | --- | --- | --- |
| Ore | `f48fcfd637f8` | `studioChronoHour` | 0 / 12 | 0? / 360? |
| Minuti | `6c6b4d09d02b` | `studioChronoMinute` | 0 / 60 | 0? / 360? |

I livelli sono visibili e hanno oggetti `widgets.Pointer` distinti, ciascuno con ombra, pivot e dominio scalato 1000. Entrambi usano `assets/c6a7891edf1ee50ee90640cd.png`; i riferimenti salvati al catalogo terminano rispettivamente in `-hour` e `-minute`. Anche selezionare la stessa identica voce del catalogo per due livelli ? ammesso: il modello determina grafica/pivot, mentre ID, sorgente e calibrazione appartengono al livello. Non viene condiviso il controller della rotazione. Non serve duplicare un set nel catalogo.

Il binding binario corrisponde alle impostazioni salvate. Le risorse Lua della compilazione precedente corrispondono ai sorgenti 2.3 precedenti a questa correzione. La dicitura `applicationVersion: 2.1` nel vecchio build-report era un'etichetta fissa rimasta nel codice di esportazione, non una prova del runtime installato: ora deriva dalla versione dell'applicazione nel rapporto esterno e in quello incorporato.

## Calcolo e prove lunghe

Il controller calcola `floor(elapsedMs / 3600000) % 12`: conta le ore intere. L'anteprima segue la stessa regola. Ogni ora sul sottoquadrante superiore vale 30?; fra due ore non viene interpolata durante Running.

| Tempo trascorso | Ore | Minuti | Angolo ore |
| --- | --- | --- | --- |
| 59:59.999 | 0 | 59 | 0? |
| 1 ora | 1 | 0 | 30? |
| 1:01:01.456 | 1 | 1 | 30? |
| 2 ore | 2 | 0 | 60? |
| 11:59:59.999 | 11 | 59 | 330? |
| 12 ore | 0 | 0 | 0? |
| 13 ore | 1 | 0 | 30? |

Le prime simulazioni del vecchio binario passavano con un solo evento AOD seguito da ON. Non coprivano notifiche ripetute n? un renderer che perdesse la posizione durante la sospensione. La nuova verifica esegue il Lua estratto dalla compilazione temporanea aggiornata del Bulova: entrambi gli stili, clock monotono simulato e fallback Anim, fino a 13 ore virtuali. Verificati riporti, wrap della fase, posizioni di lancetta/ombra, Stop e Reset.

## Correzione 1: conservare il primo istante di sospensione

Nel fallback Anim, `screen(false)` assegnava sempre `sleepWall=wall()`. Una seconda notifica AOD/pausa, oppure `pageOnResume` ricevuto prima di `ScreenStateChangedCB(...,"ON",...)`, sovrascriveva l'inizio della sospensione. L'intervallo precedente veniva perso.

Esempio riprodotto: 30 secondi attivi, 61 minuti in AOD, `pageOnResume` prima di ON. Prima della correzione il conteggio riprendeva da soli 30 secondi. Ora `sleepWall` viene inizializzato soltanto se assente, poi consumato e cancellato alla ripresa. Le notifiche ON ripetute non aggiungono nuovamente il tempo.

Questo ? un difetto software dimostrato con il Lua precedente. Da solo **non spiega** minuti che avevano gi? completato un giro: viene corretto come problema aggiuntivo del ciclo di vita. L'ordine reale degli eventi sull'S5 non ? stato registrato.

## Correzione 2: reinviare la posizione una volta alla ripresa

La cache `view.rendered` evita scritture identiche al Pointer. Prima rimaneva valida attraverso AOD/pausa: se il renderer perdeva la posa, il controller poteva continuare a considerare la lancetta ore gi? su 1 e non riscriverla fino all'ora successiva. Minuti/secondi si riallineavano prima perch? il loro valore cambia pi? spesso.

Riproduzione sul Lua estratto dal vecchio `resource.bin`, con perdita della posa **iniettata nel mock grafico**: dopo 1:02:03.456 il controller ore vale 1; durante AOD la posa grafica viene azzerata; un minuto dopo il conteggio ? 1:03:03.456, i minuti indicano 3, ma il Pointer ore resta a zero perch? la scrittura viene saltata. Il nuovo runtime invalida la cache soltanto passando da inattivo ad attivo e reinvia le posizioni correnti, incluse le ombre. Notifiche ON duplicate e fotogrammi normali conservano il write-on-change. Nessun nuovo timer o aumento della frequenza di conteggio.

La simulazione dimostra la vulnerabilit? della vecchia cache e l'efficacia della protezione **a quella condizione**. Non dimostra che l'S5 abbia perso la posa nel test dell'utente. L'esatta causa sul dispositivo rimane non confermata.

## Controlli e prova reale necessaria

Superati 137 test distinti: suite precedente pi? 22 nuove prove su notifiche AOD, ripresa, cache, ombre e PNG condivisa. Le prove di compilazione verificano manifest interattivo, Lua incorporato, POST e AOD. Il test POST del compilatore ora esclude l'ADB presente accanto al tool locale, come gi? gli altri test e l'esportazione dell'applicazione; il primo tentativo era andato in timeout a causa di quel processo, poi la prova corretta ? passata.

Compilato inoltre il vero Bulova in una cartella temporanea senza ZIP, eseguendo quattro scenari sui suoi due stili con clock diretto/fallback. Il nuovo binario supera anche AOD ripetuto, ripresa anticipata della pagina e ripristino della posa ore invariata. Non cambiano impostazioni del progetto, formula delle ore, fluidit? dei decimi, rientri da 720 ms, runtime classico o esclusioni AOD.

La versione resta **2.3**. Per provare sull'S5, aprire il progetto con l'eseguibile aggiornato, riesportare e reinstallare il nuovo ZIP: i pacchetti precedenti non acquisiscono la correzione. Dopo oltre un'ora verificare insieme ore/minuti, prima e dopo un passaggio AOD e allo Stop. Per 1:05:xx, le ore devono indicare 1 e i minuti 5. Il test fisico della correzione ? **in attesa**, distinto dalla precedente conferma positiva sulla fluidit? della 2.3.

Set personali controllati: nove set, 623 modelli, nessun aggiornamento da integrare. Nessun backup, ZIP dimostrativo o avvio dell'EXE.
