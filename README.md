# S5 Studio 1.8.1 — Cambio minuto senza scatti

Editor desktop italiano per Xiaomi Watch S5 M2530W1, 480 × 480. Crea quadranti digitali e analogici, cinque stili e complicazioni con grafica personalizzabile. La UI usa Tailwind CSS compilato offline e QtWebEngine.

Avvia **S5Studio-1.8.1.exe** oppure **Avvia_S5_Studio.cmd**. Salva il lavoro della versione precedente prima di aprire la nuova. Questo eseguibile personale è autonomo: incorpora Python, Qt, UI Tailwind, cataloghi di lancette/bussole/meteo, template verificato e Compiler.exe con DeviceInfo.db. Puoi copiarlo da solo su un altro PC Windows a 64 bit con **.NET Framework 4.7.2 o successivo**. All’avvio estrae le risorse in una cartella temporanea; il recupero del lavoro usa `%LOCALAPPDATA%/S5Studio/`. Non serve installare Python o Node.

Il test sul S5 della build 0.5 è **superato**: installazione, cambio varianti e selezione complicazioni, come confermato dall’utente. Il pacchetto testato resta conservato. La 0.7 aggiunge anteprima delle lancette in hover, immagini oltre 480 px con ritaglio in compilazione e spostamento di ogni livello con le frecce. Le nuove funzioni sono verificate sul PC.

## Correzione 1.8.1 — Sincronizzazione al cambio minuto e ora

Eliminato il salto temporaneo in avanti della lancetta minuti al passaggio dei secondi da 59 a 0. Le notifiche `dataman` di ore, minuti e secondi arrivano separatamente: prima potevano combinare il minuto nuovo con i vecchi 59 secondi. Il nuovo modulo `studio_civil_clock.lua` pubblica un campione coerente; al cambio dell'ora attende anche il nuovo valore delle ore. Vale per le lancette fluide normali e per l'ora civile del Crono Pro, senza aggiungere timer o animazioni.

Il test reale della 1.8 ha confermato l'avanzamento progressivo piacevole dei minuti e ha individuato questo scatto al confine. La correzione 1.8.1 è verificata sui sorgenti; resta da confermare sull'orologio. AOD, conteggio Crono, rientri da 720 ms e flag indipendenti conservano il comportamento precedente.

**Per applicare la correzione:** apri il progetto esistente nella 1.8.1, esporta nuovamente lo ZIP e reinstallalo sull'S5. Non occorre ricreare il progetto o cambiare le impostazioni delle lancette.

**86 test mirati superati. Eseguibile 1.8.1 creato:** 742 risorse incorporate e 16 moduli Python corrispondenti ai sorgenti testati, verificati staticamente senza avviarlo. Set personali controllati: nessun aggiornamento.

[Dettagli e verifiche](docs/EDITOR_1.8.1.md) · [Test](docs/validation-editor-1.8.1.json) · [Verifica EXE](docs/executable-build-1.8.1.json).

## Novità 1.8 — Fluidità separata e schede stabili

Apri il livello **Lancette**, poi la scheda **Lancetta ore**, **Lancetta minuti** o **Lancetta secondi**: ciascuna contiene il proprio flag **Movimento Fluido**. Il selettore comune è stato rimosso. Puoi attivare qualsiasi combinazione. I progetti precedenti conservano la scelta dei secondi; i nuovi flag di ore/minuti partono disattivati.

**Ore e minuti fluidi:** la posizione include i secondi reali, eliminando il salto di un minuto intero. I minuti avanzano di **0,1° al secondo** e le ore di circa **0,0083° al secondo**. La posizione viene calcolata con domini interi precisi dai dati `dataman`, senza aggiungere timer o animazioni a 25 fps. **Secondi fluidi:** resta lo sweep a **25 fps** già collaudato. Ogni ombra segue la propria lancetta con identica geometria.

Il lavoro aggiuntivo previsto è contenuto: ore/minuti sono mossi dalle notifiche dei secondi e non da cicli di ridisegno continuo. Il test reale ha confermato l'avanzamento progressivo dei minuti, ma ha rilevato lo scatto al cambio minuto corretto nella 1.8.1. Il consumo non è stato misurato. La risoluzione angolare del Pointer limita quanto sia visibile un singolo incremento, soprattutto per le ore.

**Crono Pro:** ore/minuti dell’ora seguono i propri flag; i puntatori che misurano il cronografo mantengono il conteggio a scatti e i rientri coordinati già collaudati. **AOD:** i tre controlli sono disabilitati; ore/minuti usano il percorso nativo senza la nuova logica Lua e i secondi restano esclusi. I valori salvati dei flag non vengono cancellati.

**Corretto il ritorno alla scheda Ore dopo Invio o una modifica:** il pannello conserva sia le schede aperte sia quelle chiuse dello stesso livello, oltre alla posizione di scorrimento. Anche Annulla mantiene la scheda corrente.

Superati **70 test mirati e 11 controlli dell’editor**, inclusi esecuzione Lua, indipendenza dei flag, salvataggio/stili, ombre, confronto geometrico, Crono Pro, AOD e compilazione di un binario temporaneo con tre stili misti. Nessun quadrante ZIP dimostrativo o avvio dell’eseguibile. Controllati i set personali: sei set incorporati, **612 modelli**, nessun nuovo aggiornamento.

**Eseguibile 1.8 creato: 741 risorse incorporate e 16 moduli Python corrispondenti ai sorgenti testati**, verificati staticamente senza avviarlo.

[Guida tecnica e limiti](docs/EDITOR_1.8.md) · [Test](docs/validation-editor-1.8.json) · [Verifica EXE](docs/executable-build-1.8.json).

## Correzione 1.7.7 — Secondi dell’ora nell’anteprima

La lancetta piccola impostata su **Secondi completi (0–59)** avanza ora anche con **Movimento Fluido disattivato**, quando è attivo **Simula movimento**: un aggiornamento al secondo. Il difetto era nella sola anteprima, che applicava il tempo trascorso soltanto con il flag fluido attivo. Se cambi manualmente il campo **Secondi** o lo scenario durante la simulazione, il conteggio riparte dal nuovo valore, senza sommare la fase precedente.

**La posizione iniziale era corretta**, come confermato dall’utente: la lancetta indica i secondi scelti nell’anteprima, **30** nello scenario Normale, e non lo zero del cronografo. Per verificare lo zero scegli **Secondi = 0** nella barra della simulazione. La scala completa consigliata resta **Valore iniziale 0 / Intervallo 60 / Angolo iniziale 0° / Rotazione totale 360°**. Il parametro Valore iniziale definisce l’origine della scala, non l’istante di avvio della simulazione.

Pivot, grafica, sorgente nativa `timeSecond`, compilazione delle lancette e runtime Crono/Crono Pro restano invariati. La sorgente esportata continua a seguire i secondi reali dell’orologio; resta esclusa dall’AOD. Nessun valore del progetto personale è stato riscritto. Integrati i nuovi set **Omega moon** e **Omega moon piccole**: sei set personali incorporati e **612 modelli totali**.

**17 test mirati e 15 controlli dell’editor superati**, compresa una compilazione binaria temporanea che verifica sorgente, aggiornamento a 1 Hz, scala, pivot, due stili Crono Pro e assenza dei secondi in AOD. Nessun ZIP dimostrativo, backup o avvio dell’EXE. La segnalazione della posizione è stata chiarita in anteprima; non è stato dichiarato un nuovo test hardware.

**Eseguibile 1.7.7 creato: 740 risorse incorporate e 15 moduli Python corrispondenti ai sorgenti testati**, verificati staticamente senza avviarlo.

[Dettagli](docs/EDITOR_1.7.7.md) · [Test](docs/validation-editor-1.7.7.json) · [Verifica EXE](docs/executable-build-1.7.7.json).

## Novità 1.7.6 — Dato live e selettore colore universale

Seleziona un livello **Dato live** e usa **Orientamento e arco → Rotazione (°) / Arco (°)**: ora puoi inclinare il dato e adattarlo al bordo del quadrante. Anteprima, selezione, salvataggio, stili e immagini di esportazione usano la stessa geometria. Il valore continua ad aggiornarsi dal sensore sull’orologio: non viene trasformato in una scritta fissa. Giorni della settimana e mesi conservano le rispettive etichette inglesi dinamiche. **Raddrizza livello** riporta entrambi i valori a zero.

La casella **Nessun colore** è ora disponibile in **tutte le finestre colore**, incluse lancette generali, testo, forme, Dato live, complicazioni, sfondo e accento degli stili. Nel colore generale delle lancette nasconde **soltanto il tappo centrale**; nelle PNG mantiene i colori originali; nei colori di testo/forme/sfondo rende il riempimento trasparente. Le singole lancette restano configurabili separatamente. Annulla, Ripeti e salvataggio conservano la scelta.

Verificati **81 test mirati e 20 controlli dell’interfaccia**, inclusi aggiornamenti sensore eseguiti in Lua, confronto pixel con l’anteprima, decimali/allineamento, compilazioni binarie temporanee di due stili Crono Pro e di un progetto senza crono, AOD, grafo finale e manifest. Nessun ZIP dimostrativo e nessun avvio dell’eseguibile. Il nuovo rendering numerico Lua trasformato richiede ancora il test reale sul S5; i runtime già collaudati di Crono e Crono Pro restano invariati. Controllati i set personali: quattro set incorporati, nessun nuovo aggiornamento, 607 modelli totali.

**Eseguibile 1.7.6 creato: 730 risorse incorporate e 10 moduli Python corrispondenti ai sorgenti testati**, verificati senza avviarlo.

[Guida e dettagli tecnici](docs/EDITOR_1.7.6.md) · [Test](docs/validation-editor-1.7.6.json) · [Verifica EXE](docs/executable-build-1.7.6.json).

## Novità 1.7.5 — Nessun colore

Nella finestra **Select Color** delle grafiche importate è disponibile la casella **Nessun colore — mantieni i colori originali**. Selezionala e premi **OK** per togliere la ricolorazione da una singola lancetta principale/piccola, da un’immagine o dalla bussola. La grafica mantiene la propria trasparenza e resta visibile con i colori della PNG. Nel pannello compare **Colore originale** quando la tinta è disattivata.

Scegliere un colore nella finestra disattiva automaticamente la casella e applica la nuova tinta. **Annulla** lascia invariati il progetto e la cronologia; il cambio colore supporta Annulla/Ripeti ed è conservato al salvataggio. L’opzione è disponibile sulle grafiche importate; testo e forme continuano a usare il normale colore del componente.

Il controllo dei cataloghi personali ha trovato e integrato **Hamilton Lancette**, con tutte e tre le lancette e le rispettive ombre. La release include ora **quattro set personali**, **12 modelli aggiuntivi**, **19 PNG distinte** e **607 modelli totali**. [Integrazione](docs/hand-set-integration-1.7.5.json).

**Eseguibile 1.7.5 creato; 729 risorse incorporate verificate staticamente**, senza avviarlo. [Verifica EXE](docs/executable-build-1.7.5.json).

**21 test mirati e 10 controlli dell’interfaccia superati**, compresa la vera finestra colore Qt, ripristino dei pixel/trasparenza, salvataggio, esportazione PNG nativa, annullamento e disponibilità di Hamilton su un catalogo utente vuoto. [Verifica](docs/validation-editor-1.7.5.json). Runtime Lua e risorse originali invariati; nessun backup, quadrante dimostrativo o avvio dell’EXE isolato.

## Novità 1.7.4 — Tutti i set modificabili

**Integrati nell’eseguibile:** **Seiko 5 ombra**, **Swatch Orange ombra** e **Swatch orange piccole**. Le nove lancette e le tredici PNG distinte, incluse le ombre, mantengono pivot, spostamenti e impostazioni di generazione. Sono disponibili anche copiando il solo EXE su un nuovo PC. Il catalogo comprende ora **604 modelli**, rispetto ai 595 originali.

Apri **Set lancette**, cerca il nome e premi **Modifica**: ora puoi modificare anche **ogni set del catalogo originale**, incluse le lancette piccole e AOD. Puoi cambiare nome, PNG, pivot, ombre e generazione automatica. Gli stili e le varianti originali sono distinguibili nel nome; i filtri separano principali, piccole, personali/integrati e catalogo originale. I set originali privi dei secondi mantengono i loro ruoli esistenti. **Ripristina** recupera la versione incorporata di un set modificato.

Le modifiche sono persistenti in `%LOCALAPPDATA%/S5Studio/hand-sets/` e hanno precedenza sui valori incorporati, senza duplicare i set. I file originali restano intatti. I quadranti già creati conservano le proprie PNG: per applicare un set aggiornato a un livello esistente scegli nuovamente **Usa modello**. Il comando **Elimina** sui set personali/integrati agisce sul catalogo locale e non sui progetti.

**Controllo automatico a ogni release:** `scripts/package.ps1` esegue, tramite `prepare_runtime.py`, la sincronizzazione dei cataloghi in `data/hand-sets/` e `%LOCALAPPDATA%/S5Studio/hand-sets/` dentro `resources/hand-sets/`. Include sia nuovi set sia aggiornamenti, verifica hash/PNG/pivot e interrompe il packaging se una risorsa è danneggiata. Il catalogo dell’app Windows ha precedenza in caso dello stesso ID; la sincronizzazione non scrive nei cataloghi sorgente. Il controllo è richiamabile anche con `python -X utf8 scripts/sync_hand_sets.py` ed è richiesto dalle istruzioni del progetto a ogni nuova modifica. [Guida](docs/EDITOR_1.7.4.md), [integrazione](docs/hand-set-integration-1.7.4.json).

**Eseguibile 1.7.4 creato e 723 risorse incorporate verificate staticamente**, senza avviarlo. [Verifica EXE](docs/executable-build-1.7.4.json).

**41 test mirati e 38 controlli dell’interfaccia superati**, comprese modifica di tutte le 595 grafiche originali, pivot esterni, abbinamenti, ombre, persistenza, ripristino, disponibilità dei set integrati senza dati utente e integrità delle PNG. Runtime Lua e risorse originali invariati. [Rapporto](docs/validation-editor-1.7.4.json). Nessun nuovo backup, quadrante ZIP dimostrativo o avvio dell’EXE in ambiente isolato.

## Correzioni 1.7.3 — Calendario inglese e allineamento

**Dato live → Giorno settimana:** mostra **MON, TUE, WED, THU, FRI, SAT, SUN**, sempre tre lettere maiuscole. L’anteprima iniziale è **MON**. **Dato live → Mese:** mostra i nomi completi inglesi, da **January** a **December**, come richiesto dall’utente. Font importato, dimensione, grassetto memorizzato, colore, opacità e allineamento si applicano a tutti i nomi. Cifre, decimali e zeri iniziali sono nascosti quando la sorgente è un calendario testuale; restano disponibili per gli altri dati numerici.

Le parole sono rasterizzate sul PC con il font scelto e compilate in un **DataItemImageValues nativo**, collegato a `dateWeek` o `dateMonth`. Il dispositivo seleziona quindi la scritta del giorno/mese effettivo, senza Lua e senza dipendere dalla lingua del telefono. La codifica dei quadranti forniti è `dateWeek: 0=SUN, 1=MON, …, 6=SAT`; i mesi usano valori espliciti `1…12`. [Evidenza del formato](docs/calendar-native-mapping-1.7.3.json). Le anteprime complete e degli stili usano lo stesso testo dell’esportazione. Il normale oggetto **Data DD/MM** conserva il mese numerico; anche le sorgenti che guidano le lancette rimangono numeriche.

Alla selezione di una sorgente calendario il campo viene allargato, solo se necessario, per ospitare tutti i nomi con il font corrente, mantenendolo sul canvas. Le geometrie già salvate non vengono riscritte all’apertura: se un campo esistente è troppo piccolo per il nome più lungo, aumenta la larghezza o riduci il font. La validazione controlla l’intero elenco, non soltanto il nome mostrato nell’anteprima.

**Dato live → Giorno del mese, allineamento Destra:** un giorno come **6** occupa la posizione delle unità di **16**, sul lato destro del campo. Era errata sia l’anteprima, che aggiungeva spazi a destra, sia l’esportazione, che forzava sempre l’allineamento sinistro. Ora Sinistra/Centro/Destra allineano il valore visibile; gli zeri iniziali continuano a produrre **06** quando richiesti. I metadati e il validator verificano anche l’allineamento effettivo del binario.

**22 test mirati e 9 controlli dell’editor superati**, incluse compilazioni binarie temporanee di calendario e allineamenti, associazioni giorno/mese, AOD, font, colore/opacità, anteprime, giorno singolo e conservazione del DD/MM numerico. [Rapporto](docs/validation-editor-1.7.3.json). Nessun quadrante ZIP dimostrativo, nuovo backup o avvio dell’EXE in ambiente isolato. Runtime Crono/Pro e catalogo originale invariati. Le ombre della 1.7.2 sono confermate corrette dall’utente; l’utente ha successivamente confermato che il lavoro della 1.7.3 è ben fatto.

## Correzione 1.7.2 — Ombre tra le lancette

Le lancette principali rispettano ora questo ordine, dal basso verso l’alto:
**ombra ore → ore → ombra minuti → minuti → ombra secondi → secondi → copriperno centrale**.
L’ombra dei minuti può quindi cadere sulla lancetta delle ore; quella dei secondi può cadere sulle lancette di ore e minuti. Prima tutte le ombre venivano disegnate sotto tutte le lancette: si vedevano sul quadrante, ma erano coperte dalle lancette stesse.

La correzione si applica ad **anteprima, miniature degli stili, esportazione nativa e Crono Pro**, sia con ombre originali sia con quelle generate dal software. Nel percorso nativo le singole lancette sono emesse come puntatori separati, con la propria ombra immediatamente sotto: restano gli stessi sei puntatori quando sono presenti tre lancette e tre ombre. La scena Lua crea le immagini nello stesso ordine e conserva gli abbinamenti ombra/lancetta del controller. Pivot, dimensioni, colori, spostamenti, conteggio e animazioni non sono modificati. Il flag **Mostra ombre** continua a nasconderle tutte.

**58 test mirati superati**: verifica dei pixel delle ombre su lancette sovrapposte, miniature, ordine dei figli nella scena Lua realmente eseguita, ombre disattivate, geometria e generazione dei set. Una sola compilazione binaria temporanea verifica ordine, sorgenti, centri e periodi nel formato nativo, incluso AOD senza secondi; nessun quadrante ZIP dimostrativo. Il movimento fluido ordinario riguarda ancora soltanto i secondi; ore/minuti rimangono a 1.000 ms. I due runtime Lua restano invariati. [Rapporto](docs/validation-editor-1.7.2.json). Nessun nuovo backup e nessun avvio dell’EXE in ambiente isolato.

**Il test della correzione 1.7.1 è confermato dall’utente**, che riferisce «il problema è stato risolto». L’utente conferma successivamente «perfetto adesso le ombre sono perfette»: [esito](docs/user-test-1.7.2.json).

## Correzione 1.7.1 — Decimi e visibilità Crono Pro

Il flag **Crono Pro** della lancetta grande dei secondi rimane l’unico selettore del sistema integrato, per ogni stile. Il menu della lancetta piccola sceglie il dato da mostrare:

| Sorgente | Comportamento |
| --- | --- |
| **Decimi di secondo · continui** | Un giro al secondo, indipendente dal cronografo. Continua anche a cronografo fermo e non segue Avvio, Stop o Reset. Non richiede Crono Pro. |
| **Decimi crono · Start/Stop/Reset** | Decimi del tempo misurato dal Crono Pro: zero a riposo, dieci scatti al secondo durante la misura, fermi alla lettura su Stop, azzerati con il rientro fluido al Reset. Richiede il flag generale nello stesso stile. |

Per un cronografo usa **Decimi crono · Start/Stop/Reset**; la voce non introduce una seconda modalità Pro. Entrambe le sorgenti restano escluse dall’AOD. I progetti mantengono le sorgenti salvate, senza conversioni automatiche.

**Corretto il falso messaggio bloccante quando si nascondeva il livello delle lancette grandi.** Il controllo verificava contemporaneamente il flag e la visibilità del livello: occultare la grafica veniva interpretato come disattivare Crono Pro. Ora la modalità dipende dalla configurazione, mentre anteprima ed esportazione omettono la grafica dei livelli nascosti. Le piccole visibili continuano a usare il controller Pro; nascondere/mostrare, anche con Annulla/Ripeti, non azzera il conteggio nell’editor. L’avviso resta corretto se il flag manca davvero nello stile corrente o si tenta di disattivarlo lasciando visibili i decimi crono.

**47 test mirati e 10 controlli dell’editor superati**, inclusi esecuzione della scena Lua con gruppo grande nascosto, conteggio di ore/minuti/decimi, Stop/Reset, persistenza e indipendenza degli stili. I due file runtime Lua sono identici alla 1.7. Nessuna compilazione di quadranti di prova, nessun nuovo backup e nessun avvio dell’EXE in ambiente isolato. [Verifica](docs/validation-editor-1.7.1.json). **L’utente conferma che la 1.7 ha funzionato bene sul proprio dispositivo**; l’utente conferma successivamente che la correzione 1.7.1 ha risolto il problema: [esito](docs/hardware-test-1.7.1.json).

## Novità 1.7 — Genera ombre

Apri **Set lancette**, crea un nuovo set oppure premi **Modifica** su uno dei tuoi set esistenti. Attiva **Genera ombre**: Studio crea subito le PNG mancanti ricavando la sagoma dalla trasparenza delle lancette. Funziona sia per i set principali sia per quelli piccoli. Le ombre importate manualmente vengono conservate; il flag completa soltanto quelle mancanti.

Default: ombra nera, **opacità 45%**, **sfocatura 1,5 px**, **spostamento X +2 / Y +3 px** nelle coordinate della PNG. Puoi regolare opacità (1–100%), sfocatura (0–4 px) e spostamento (−20…20 px). Il pivot automatico segue quello della lancetta, con margini trasparenti quando disponibili, entro 480×480 px. Cambiando PNG, pivot o impostazioni, si aggiorna solo l’ombra automatica. Per una forma fedele usa PNG con sfondo trasparente.

Premi **Salva/Aggiorna set nel catalogo**, poi torna sul livello del quadrante e premi **Usa modello** per applicare anche le ombre. Il flag **Mostra ombre** del livello le rende visibili o nascoste. Disattivare **Genera ombre** rimuove dalla bozza soltanto quelle automatiche; salva e riapplica il modello per aggiornare i livelli già creati. Puoi importare una tua PNG al posto di un’ombra automatica: diventa manuale e non viene più rigenerata. Le PNG originali delle lancette restano intatte e i progetti incorporano le ombre applicate.

**37 test mirati e 32 controlli dell’editor superati**, inclusi set piccoli, pivot, aggiornamento, ombre importate, salvataggio e confronto delle PNG native/Lua. La generazione avviene sul PC e utilizza i componenti ombra esistenti, senza aggiungere timer o nuove API al firmware. Nessun backup, quadrante dimostrativo o test isolato dell’EXE. [Guida](docs/EDITOR_1.7.md), [verifica](docs/validation-editor-1.7.json). **Il test reale 1.6.1 è pienamente superato**, come confermato dall’utente il 9 ottobre 2026; l’utente conferma successivamente che la 1.7 ha funzionato bene: [esito](docs/hardware-test-1.7.json).

## Correzioni 1.6.1

**Nuovi livelli Lancette e Lancetta piccola:** Lunghezza **50%** e Spessore **15 px**. I progetti già salvati conservano i propri valori. Quando premi **Usa modello**, sia nel catalogo originale sia nei set personali, vengono attivate immediatamente entrambe le regolazioni per ogni lancetta applicata, comprese minuti/secondi abbinati e ombre. Il modello usa i valori visibili nei controlli fin dal primo render; non serve modificarli per aggiornare l’anteprima. Anche Crono Pro usa la medesima geometria. Riapplica il modello per attivare questo comportamento su un livello esistente; i suoi valori numerici non vengono azzerati.

Il pulsante attende la decodifica della nuova immagine e i vecchi fotogrammi dell’anteprima animata vengono scartati, evitando che coprano una modifica recente. Il problema era nei flag di regolazione lasciati disattivati dopo l’applicazione del modello: una modifica manuale li attivava soltanto in seguito.

**Dato → Giorno del mese:** lo scenario iniziale **Normale** mostra **15**, per valutare subito l’ingombro di due cifre. Gli scenari limite mantengono i loro dati e lo ZIP continua a usare la data reale del S5.

**26 test mirati e 24 controlli dell’editor superati**, compresi confronto fra primo render e modifica a valori invariati, PNG native/Lua, modelli principali/piccoli, set personali e compatibilità Crono Pro. [Rapporto](docs/validation-editor-1.6.1.json). Nessun nuovo backup, nessun quadrante dimostrativo e nessun avvio dell’EXE in ambiente isolato. **Test reale della 1.6.1 pienamente superato**, confermato dall’utente: [esito](docs/hardware-test-1.6.1.json); i runtime Crono e Crono Pro rimangono invariati.

## Novità 1.6

Nuova sezione **Set lancette** nella barra laterale. Assegna un **nome**, scegli **Lancette principali** oppure **Lancette piccole**, poi importa le PNG nei ruoli Ore, Minuti e Secondi. Per un set principale servono tutte e tre; per le piccole basta una grafica. Ogni PNG deve essere statica, da 1 a 480 pixel per lato, preferibilmente trasparente e rivolta verso le ore 12. Clicca sull’immagine per impostare il pivot, oppure usa le coordinate in pixel. Puoi importare anche le ombre, con pivot e spostamento indipendenti.

Premi **Salva set nel catalogo**. Torna su **Quadrante**, seleziona il livello Lancette e scegli il nuovo nome nel menu delle ore: **Usa modello** abbina automaticamente anche minuti, secondi e ombre. Resti libero di sostituire ogni lancetta separatamente. Per le lancette piccole scegli la grafica dal loro menu; il pivot salvato viene rispettato, mentre la sorgente del dato resta quella scelta nel livello. Puoi modificare, rinominare o eliminare i set dal pannello dedicato.

Il catalogo personale è persistente in **`%LOCALAPPDATA%/S5Studio/hand-sets/`** nell’eseguibile, oppure `data/hand-sets/` avviando i sorgenti. Dalla 1.7.4 i set presenti sul PC di sviluppo vengono integrati automaticamente nelle nuove release; la cartella continua a contenere le modifiche locali. Per trasferire modifiche non ancora incluse in una release puoi copiarla su un altro PC. **Le PNG applicate sono incorporate nei progetti e nell’esportazione:** modificare o eliminare un set non altera i quadranti già salvati. L’importazione singola PNG/SVG rimane disponibile nelle proprietà delle lancette.

**30 test mirati e 18 controlli del nuovo pannello superati**, compresi importazione, pivot, ombre, persistenza e applicazione del set. La 1.6 conserva tutte le funzioni della 1.5, poi incluse nella 1.6.1 collaudata dall’utente. Nessuna modifica al runtime Crono/Pro sul S5. [Guida set lancette](docs/EDITOR_1.6.md), [verifica della release](docs/validation-editor-1.6.json).

## Novità 1.5

Seleziona un livello **Testo, Immagine o Forma** e apri **Orientamento e arco** nelle proprietà. **Rotazione (°)** gira il livello attorno al suo centro: positivo in senso orario, negativo in senso antiorario. **Arco (°)** adatta la grafica al bordo rotondo: 0 mantiene il livello diritto, valori positivi creano un arco superiore e negativi uno inferiore. **Raddrizza livello** azzera entrambi. Il riquadro di selezione segue l’ingombro trasformato; puoi continuare a trascinare, ridimensionare e usare le frecce.

La trasformazione è identica nell’anteprima, negli stili e nello ZIP: viene incorporata nelle PNG, ritagliando la parte oltre i 480×480 px. Anche immagini ingrandite fino a 4.096 px restano supportate. Le immagini a scelta dinamica, come le icone meteo, mantengono la sorgente nativa; ciascuna immagine riceve la stessa trasformazione. Non viene aggiunta logica Lua per queste operazioni. Lancette, bussola, numeri live, Ora/Data e complicazioni numeriche conservano i loro componenti nativi e non espongono questi controlli. Riduci l’arco o l’altezza se il software segnala che la grafica si ripiegherebbe su sé stessa.

**Forma:** scegli **Rettangolare** o **Circolare** nelle proprietà. Il passaggio al cerchio mantiene il centro e usa dimensioni uguali; puoi poi ridimensionarlo. La scelta è indipendente per stile e supporta Annulla/Ripristina.

**Catalogo lancette:** gli otto nomi cinesi presenti sono tradotti in inglese, compresi cinque nomi di stile e due nomi autore. Grafiche, ID, pivot, ombre e abbinamenti sono conservati; i nomi originali restano disponibili nei dati di provenienza. [Rapporto traduzioni](docs/catalog-english-1.5.json).

**22 test mirati superati**, inclusa una compilazione temporanea con due stili, AOD, Crono Pro, sensori nativi e icone meteo trasformate. Controllo visivo di rotazione e dei due versi dell’arco superato. Nessun quadrante dimostrativo, nessun nuovo backup e nessun avvio EXE in ambiente isolato. [Guida](docs/EDITOR_1.5.md), [verifica](docs/validation-editor-1.5.json). Il test reale della **1.4.1 è confermato dall’utente il 9 ottobre 2026**; le trasformazioni sono poi incluse nella release 1.6.1, il cui test reale è stato confermato dall’utente.

## Correzione 1.4.1

**L’anteprima Crono Pro mostra subito le dimensioni impostate**, anche aprendo un progetto senza modificare i controlli. Nel primo NASA analizzato, Lunghezza minuti 10% generava correttamente una grafica di 5×46 px. L’anteprima usava invece la geometria analogica originale di 40×480 px finché non venivano modificati i controlli, dando un’idea sbagliata della misura esportata.

Il renderer dell’anteprima usa ora le stesse viste `pro_views` dell’esportazione Lua, inclusi pivot, colori e ombre. **La geometria nello ZIP resta invariata:** tutte le 12 PNG delle lancette/ombre e le due scene Lua rigenerate dal nuovo progetto NASA sono byte per byte identiche al pacchetto creato dall’utente dopo la regolazione. La prova riproduce anche i controlli iniziali minuti 10% e spessore 5 senza regolazioni attivate. Le anteprime complete e degli stili usano lo stesso renderer.

**Movimento Fluido durante l’ora normale:** il flag del gruppo analogico riguarda soltanto la grande dei secondi; non abilita il movimento fluido sulle grandi di ore e minuti. Il Crono Pro mantiene il conteggio a scatti e i rientri coordinati sempre fluidi da 720 ms, indipendenti dal flag. Il runtime resta invariato.

**30 test mirati superati**, inclusi anteprima al primo render e dopo una modifica, quattro combinazioni di regolazione, compilazioni temporanee, varianti e AOD. Il binario nativo verifica secondi a 25 fps e ore/minuti al periodo normale di 1.000 ms. [Analisi del NASA](docs/nasa-geometry-analysis-1.4.1.json), [verifica](docs/validation-editor-1.4.1.json). Nessun nuovo backup, nessuna prova EXE isolata e nessun quadrante dimostrativo.

Apri il progetto con **S5Studio-1.4.1.exe**: vedrai subito la dimensione esportata. Modifica Lunghezza/Spessore per ottenere la misura desiderata, poi genera lo ZIP. Non serve toccare un controllo per risvegliare l’anteprima.

## Novità 1.4

**Crono Pro più lento:** preparazione e Reset passano da **480 a 720 ms**, riducendo la velocità di un altro terzo rispetto alla 1.3. Il tempo resta comune e deterministico, con rientri orari, simultanei, target 25 fps e annullamento immediato in AOD. Anche la simulazione usa 720 ms. A parità di durata, una lancetta che percorre più gradi ruota più velocemente: questa differenza rimane per conservare il completamento simultaneo del gruppo; la 1.4 rallenta tutti i percorsi di un terzo.

**Anteprime della mod:** il confronto del materiale NASA recuperato con tutte le **39 cartelle** del corpus trova **33 configurazioni disponibili e 133 temi**, tutti con anteprime nella cartella `_preview/`. Le PNG NASA della 1.3 contengono già tutte le lancette; la mod le estrae senza modificarle. Nel binario cambia soltanto l’ID, che diventa `L00000000001`. Le configurazioni online esaminate non contengono oggetti `App`, mentre le nostre lancette Pro sono gestite da una scena Lua `App`: il comportamento del renderer della mod resta da confermare.

La 1.4 usa PNG complete in `resources/_preview/`, riferimenti statici nel manifest e in `editor.config.json`, mappa `formats` e risorse `Image` conformi agli esempi. Il riferimento `previewAni` ai WebP con un solo fotogramma viene rimosso. Un validator controlla questi riferimenti prima dell’esportazione. Le capacità, il template e i livelli del quadrante operativo non vengono alterati da questa correzione dei metadati.

**La correzione della preview nella mod richiede il prossimo test reale:** la cartella non include il database del catalogo locale né il codice dell’app. Non consente di dimostrare che la mod usi le PNG statiche anziché ricostruire una preview ignorando Lua. Nome locale e controllo capabilities dipendono ancora dal percorso di importazione della mod. Analisi: [ANALISI_UPLOADER_1.4.md](docs/ANALISI_UPLOADER_1.4.md), [rapporto tecnico](docs/local-uploader-analysis-1.4.json). Guida: [EDITOR_1.4.md](docs/EDITOR_1.4.md).

**25 verifiche mirate superate**, comprese una compilazione temporanea, integrità delle anteprime e rifiuto dei riferimenti incoerenti. Nessun nuovo backup e nessun avvio EXE in ambiente isolato. [Rapporto di verifica](docs/validation-editor-1.4.json).

Per il test: apri il progetto nella 1.4, esporta un nuovo ZIP e importalo sul telefono. Usa il nuovo pacchetto e verifica le anteprime dello stile normale e dello Stile 2; aggiornare soltanto l’EXE non modifica il pacchetto già installato.

## Novità 1.3

La 1.3 aveva portato i rientri da 320 a 480 ms e rasterizzato tutte le lancette prima della codifica delle anteprime native. Il test reale conferma il funzionamento del Crono Pro, ma la mod mostra ancora una preview con il solo sfondo. [Esito reale](docs/hardware-test-1.3.json). La 1.4 allinea i metadati delle anteprime al catalogo online e rallenta ulteriormente le transizioni.

## Novità 1.2

**Rientri Crono Pro sempre in senso orario**: preparazione allo zero e Reset del gruppo usano il percorso orario, anche quando è più lungo. Restano sincronizzati, fluidi per 320 ms con target 25 fps; conteggio a scatti e annullamento immediato in AOD. La simulazione usa lo stesso criterio. Sono gestite anche scale parziali o con rotazione inversa: il rientro fisico resta orario.

**Ogni stile possiede i propri livelli.** Nel pannello **Livelli e proprietà → Stile in modifica** scegli la variante. Duplica uno stile, poi aggiungi, cancella, nascondi, trascina, riordina e modifica le sue immagini, lancette, sorgenti o complicazioni: gli altri stili non vengono alterati. Non serve più il flag “Modifica soltanto questo stile”. “Sfondo da immagine” sostituisce lo sfondo dello stile selezionato, senza lasciare l’immagine coperta dal quadrante principale.

I progetti precedenti vengono convertiti in memoria conservando l’aspetto di ogni stile. Il salvataggio usa lo **schema 3**, con risorse di tutti gli stili; salva una copia per conservarne una apribile nelle versioni precedenti. L’AOD rimane una schermata comune abbinata agli stili. Il compiler genera risorse, anteprime reali e complicazioni da ciascuna lista indipendente. Guida: [EDITOR_1.2.md](docs/EDITOR_1.2.md).

Il **primo test reale Crono Pro 1.1 è superato**, con fluidità confermata dall’utente. Sorgenti, risorse ed EXE 1.1 sono conservati nel [backup verificato](docs/stable-baseline-1.1.json); il crono separato mantiene il core 1.0. Il test reale della 1.2 è pienamente superato: [conferma dell’utente](docs/hardware-test-1.2.json). Verifica PC: **127 test automatici e 100 controlli dell’editor superati**. Rapporti: [validation-editor-1.2.json](docs/validation-editor-1.2.json), [executable-build-1.2.json](docs/executable-build-1.2.json). Nessuna prova EXE in ambiente isolato; viene consegnato solo l’eseguibile.

## Novità 1.1 — Crono-Pro

Nuovo flag **Crono Pro** nelle proprietà della lancetta grande dei secondi, disattivato per default. Attivo: Riposo → Prepara allo zero → Avvia → Stop → Reset fluido e ritorno all’ora corrente. Le piccole possono usare **Decimi crono**, Minuti Crono e Ore Crono. Durante il conteggio il flag Movimento Fluido viene ignorato: secondi e decimi avanzano a scatti; nei rientri tutto il gruppo usa obbligatoriamente un’animazione comune da 320 ms, target 25 fps. Il runtime aggiorna soltanto gli angoli cambiati e usa 100 ms con i decimi, 1.000 ms negli altri casi. In AOD interrompe i rientri, nasconde la scena e usa l’AOD del progetto, sempre senza secondi o Lua.

Il **Crono separato 1.0 rimane distinto e conserva il runtime collaudato**. I decimi continui già funzionanti mantengono la propria voce; Decimi crono è la nuova voce legata allo stato Pro. Per rispettare i livelli, l’analogico Pro viene disegnato nella scena Lua, ricevendo l’ora tramite dataman; i secondi hanno un solo controller. Guida: [EDITOR_1.1.md](docs/EDITOR_1.1.md).

Verifica PC: **112 test automatici superati**, compilazioni temporanee con varianti/AOD e **91 controlli nell’editor da sorgente**. **Primo test reale Pro 1.1 superato**, con rientro fluido confermato dall’utente; consumo non misurato. [Evidenza riferita dall’utente](docs/hardware-test-1.1.json). L’EXE 1.0 e il backup verificato restano conservati. Nessun quadrante dimostrativo prodotto e nessuna prova EXE in ambiente isolato.

## Novità 1.0

Il test prolungato della 0.11 ha mostrato minuti Crono fermi dopo il primo giro dei secondi, pur con sorgenti corrette. La 1.0 sostituisce gli App separati con **un’unica scena Lua per stile**: ore, minuti e secondi condividono lo stesso conteggio, timer e tap. La sincronizzazione non dipende più dalla condivisione della VM tra widget separati. **Test reale 1.0 pienamente superato**, confermato dall’utente l’**8 ottobre 2026**: il crono funziona su tutte le lancette piccole. I test automatici coprono anche il passaggio del minuto e dell’ora, Stop/Reset e il giro oltre 12 ore. Verifica PC: **95 test passati** e **84 controlli dell’editor**, compresa la compilazione reale con due stili e AOD. Guida: [EDITOR_1.0.md](docs/EDITOR_1.0.md); evidenza fisica riferita dall’utente: [hardware-test-1.0.json](docs/hardware-test-1.0.json).

## Crono

La **1.0 è il riferimento stabile collaudato sull’Xiaomi Watch S5 M2530W1**. Il cronografo è locale al quadrante: non controlla l’app Cronometro del sistema. Le sorgenti `studioChronoSecond`, `studioChronoMinute` e `studioChronoHour` sono abbinamenti del nostro runtime Lua, non nuovi identificatori di sensori Xiaomi.

### Come abbiamo ottenuto il funzionamento completo

1. **Packaging Lua reale.** `s5studio/native.py` genera un App EasyFace tramite **Shape 34**. `s5studio/lua_runtime.py::write_scene` scrive un solo entry point `app/lua/studio_vN_scene.lua` per stile normale, insieme a `studio_core.lua`, PNG delle lancette e ombre. EasyFace compila queste risorse nel binario; non basta aggiungere uno script esterno allo ZIP.
2. **Un solo stato per tutte le lancette.** Nella 0.11 ogni lancetta era un App separato. `_G` e la cache di `require` non garantivano uno stato comune fra questi App: nei test con VM isolate, il tap avviava soltanto l’App dei secondi. La 1.0 registra tutte le viste tramite `core:add` nello stesso entry point; ore, minuti e secondi condividono certamente il medesimo runtime. La separazione effettiva delle VM del firmware non è stata misurata, ma non è più necessaria per il funzionamento.
3. **Tempo trascorso, non conteggio dei callback.** Il runtime seleziona una sola sorgente temporale: `lvgl.tick_get`, altrimenti `/proc/uptime`, altrimenti `os.time`. Memorizza l’istante di partenza e calcola il tempo trascorso dal clock; un callback in ritardo non perde secondi. La sorgente non viene cambiata durante una misura, per evitare di mescolare origini temporali diverse. `os.time` ha precisione di un secondo e può risentire delle correzioni dell’ora; il test positivo non identifica quale clock sia disponibile sul singolo firmware.
4. **Un timer e un calcolo comune.** Un `lvgl.Timer` da **40 ms**, cioè un obiettivo di 25 aggiornamenti al secondo, aggiorna tutte le lancette Crono. Dallo stesso `elapsedMs` ricava secondi `/ 1.000`, minuti `/ 60.000` e ore `/ 3.600.000`. Senza Movimento Fluido applica la parte intera; poi applica il modulo 60, 60 o 12, rispettivamente. `Pointer:set {value=...}` trasforma il valore nell’angolo definito da intervallo, rotazione e pivot del progetto. Una sola lista aggiorna grafica e ombra insieme.
5. **Un solo tap per il quadrante.** Una superficie trasparente 480×480 usa `lvgl.EVENT.PRESSED`, con `CLICKED` come fallback. La sequenza è **Azzera → Avvia → Ferma → Azzera**. Stop memorizza il tempo e ferma tutte le viste; Reset azzera insieme ore, minuti e secondi. Le lancette non devono gestire tap o timer indipendenti.
6. **Pause senza scomparsa delle lancette.** `pageOnPause` sospende gli aggiornamenti senza nascondere le immagini durante una pausa temporanea legata al tocco. Se necessario, un tap viene conservato fino a `pageOnResume`. Lo schermo spento/AOD sospende il disegno e ignora i tap; al ritorno, se il crono è in movimento e il clock è disponibile, il tempo trascorso viene ricalcolato. Ricreare la VM o cambiare quadrante azzera lo stato: non è prevista persistenza del cronometro.
7. **Coerenza di esportazione.** Manifest interattivo, script, PNG e binario sono verificati insieme. `build-report.json` registra hash, entry point e `crossWidgetVmSharingRequired=false`; il validator controlla tutte le viste e un solo gestore del tap per stile. Secondi e App Lua sono esclusi dall’AOD. Il packaging conserva capability e record protetti del template. `hardwareVerified:false` nei rapporti automatici significa che il validator non esegue prove fisiche: la conferma manuale della 1.0 è documentata separatamente.

Per un sottoquadrante da 60 secondi/minuti usa valore iniziale 0, intervallo 60 e rotazione 360°. Per le ore su scala 12 usa 0/12 e 360°. L’angolo iniziale dipende dalla grafica, dal pivot e dallo zero del sottoquadrante; un vecchio progetto conserva le sue impostazioni.

**Decimi attuali, già funzionanti e collaudati sull’S5:** `studioDecisecond` usa `root:Anim`, con durata 1.000 ms e ripetizione continua. Il callback ricava la fase del giro e aggiorna lancetta/ombra; il flag fluido abilita i valori intermedi. L’utente ha confermato nuovamente il funzionamento l’8 ottobre 2026. Questa funzione è indipendente da Start/Stop/Reset. La futura voce **Decimi crono** estende il comportamento già disponibile, collegandolo ad Avvio/Ferma/Azzera e allo stesso tempo trascorso delle altre lancette; non sostituisce i decimi continui dei progetti esistenti.

Gli esempi primari mostrano [Pointer con timeSecond](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand9Pro/PointerTest/app/lua/main.lua) e [rotazione animata di immagini](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand8Pro/AnalogTimeAnimated/app/lua/image.lua). La prova dell’utente sull’S5 conferma il nostro runtime 1.0; gli esempi pubblici su altri modelli non certificano da soli ogni nuova funzione.

L’evoluzione proposta, con lancetta grande condivisa fra ora e crono, è descritta nel [piano di fattibilità](docs/PIANO_CRONO_INTEGRATO.md). Il codice 1.0 rimane invariato in questa fase; il [punto di ripristino](docs/stable-baseline-1.0.json) conserva sorgenti e risorse con hash verificabili.

## Novità 0.11

**Prima prova reale 0.11 positiva**, confermata dall’utente il **7 ottobre 2026**: decimi, tap Crono e secondi funzionanti, compilazione in pochi secondi. Un test successivo più lungo ha rilevato minuti Crono fermi; le ore non sono state provate per un’ora. La correzione è nella 1.0. Evidenza aggiornata: [hardware-test-0.11.json](docs/hardware-test-0.11.json).

- Esportazione: notifica collegata alla reale fine del worker, pulsante riabilitato anche dopo errori, aggiornamento finale senza render di tutte le anteprime. L’animazione della UI è sospesa durante la build e usa intervalli dopo il render. Il report esterno registra tempi delle fasi, pubblicazione, pulizia e ritardo della notifica UI.
- Decimi: animazione LVGL ciclica da 1000 ms, indipendente da `tick_get` e `/proc/uptime`. Anche un vecchio intervallo 60 copre la rotazione configurata in un secondo; scala consigliata 0/10 e rotazione 360°.
- Cronografo: tap esteso al quadrante e fallback `os.time` se i clock monotoni non sono disponibili. Questo fallback ha precisione di un secondo e risente della sincronizzazione dell’ora. Tap e secondi Crono sono confermati sull’S5; la sincronizzazione dei minuti viene corretta nella 1.0.

**Esito iniziale delle correzioni 0.11:** risolti nel test reale i decimi fermi e il cronografo non avviato della 0.10. L’utente conferma inoltre la compilazione in pochi secondi. Restano conservati i rapporti storici della 0.10; il successivo difetto dei minuti è documentato nella 1.0. Dettagli: [EDITOR_0.11.md](docs/EDITOR_0.11.md).

Verifica PC: 90 test della suite completa e 14 test mirati dopo l’ultimo feedback sul tap (91 test distinti); 84 controlli nell’editor, senza prova EXE isolata. [Rapporto](docs/validation-editor-0.11.json). Il runtime gestisce anche un tap durante una pausa temporanea, senza nascondere esplicitamente le lancette; i tocchi in AOD vengono ignorati.

## Novità 0.10

- **Movimento Fluido** per secondi: 25 fps / periodo nativo 40 ms, applicato anche alle ombre. Secondi, decimi e componenti Lua sono sempre esclusi in AOD, in tutti gli stili.
- Lancette piccole: **Decimi di secondo** (un giro al secondo), **Ore Crono**, **Minuti Crono**, **Secondi Crono**. Framework Lua con tap sul sottoquadrante: Avvia → Ferma → Azzera. Pulsante di simulazione nell’editor.
- **Ctrl + clic** sul canvas o nei livelli per selezione multipla; drag e frecce muovono il gruppo. Sei allineamenti al quadrante, distanze relative conservate, un solo Annulla.
- ZIP con `build-report.json`: hash degli script incorporati nel binario, interattività verificata, frequenze native e controllo AOD. `interactive=true` solo con componenti Lua.
- EXE personale autonomo, con runtime Lua incorporato. Nessun nuovo quadrante dimostrativo consegnato.

**Cronografo e decimi 0.10: verificati sul PC, ma il successivo test firmware è fallito. Vedere le correzioni 0.11 sopra.** Sono richiesti un clock monotono accessibile e una VM condivisa fra i sottoquadranti. Senza clock il cronografo resta azzerato. Durante AOD il disegno e il timer sono sospesi, mentre il tempo trascorso continua. Cambio quadrante o nuova VM azzerano il conteggio. Non è collegato all’app cronometro dell’orologio.

Verifica finale 0.10: **85 test passati**, **81 controlli UI nell’EXE**, **707 risorse incorporate verificate** e compilazione isolata senza tool esterni; il binario Lua con due stili e AOD coincide con quello prodotto dai sorgenti. Rapporti: [validation-editor-0.10.json](docs/validation-editor-0.10.json), [executable-build-0.10.json](docs/executable-build-0.10.json).

Guida e fattibilità: [EDITOR_0.10.md](docs/EDITOR_0.10.md). Rapporti: [validation-editor-0.10.json](docs/validation-editor-0.10.json), [executable-build-0.10.json](docs/executable-build-0.10.json).

## Novità 0.9

- Clicca nella preview **Pivot · clicca sulla grafica applicata** per impostare X/Y nel file originale. La croce mostra il perno attuale; per le lancette piccole il clic disattiva il perno automatico. Preview valida anche per PNG/SVG personalizzati e ombre abbinate.
- Lunghezza e spessore funzionano sulle lancette importate: trasformazione condivisa da anteprima, bitmap FPRJ e binario. I progetti precedenti mantengono la propria geometria finché modifichi un controllo; le immagini originali rimangono intatte. Lunghezza 1–100% del lato più corto del livello, spessore 1–100 px della parte visibile più larga.
- Menu delle sorgenti senza alias duplicati, con spiegazioni in hover. **Ora completa** è distinta da **Cifra delle ore · unità / decine**: alle 14, rispettivamente 14, 4 e 1.
- Nuovo livello **Bussola analogica**, con 10 modelli: otto grafiche osservate e due rose complete composte. Pivot al centro, sensore `systemSensorCompass`, intervallo 360°, rotazione −360°. Puoi importare un PNG/SVG, ricolorarlo, ridimensionarlo e usarlo nelle varianti. Il campo **Bussola °** modifica solo la simulazione.
- Zoom anteprima 50–400%, Ctrl + rotella e centratura della selezione. Spazio + trascina o tasto centrale per la panoramica. Zoom e scorrimento non modificano le coordinate o i 480×480 px esportati.
- Eseguibile personale completo, verificato in una cartella contenente soltanto l’EXE. Nessun nuovo quadrante dimostrativo prodotto per questa versione.

Verifica finale: **77 test automatici passati**, **66 controlli UI nell’eseguibile reale**, 705 risorse incorporate controllate e compilazione senza toolchain/template esterni. Il binario della fixture temporanea coincide con quello dei sorgenti, anche con due stili e AOD. Rapporti: [validation-editor-0.9.json](docs/validation-editor-0.9.json) e [executable-build-0.9.json](docs/executable-build-0.9.json).

Il **test reale NASA della 0.8 è superato**, come confermato dall’utente. Il progetto `projects/NasaS5.s5faceproj` resta intatto e la sua anteprima 0.9 è identica a quella della 0.8. Il successivo test reale della 0.9 è stato dichiarato completamente positivo dall’utente, inclusa la bussola analogica; evidenza in docs/hardware-test-0.9.json. Guida: [EDITOR_0.9.md](docs/EDITOR_0.9.md).

### Perché data/ è nel .gitignore?

`.gitignore` decide cosa viene salvato nel repository, non cosa entra nell’eseguibile. La **0.8 da sola non era completa**: richiedeva data, template e compilatore accanto al file. La **0.9 preparata per questo progetto** include tutte queste risorse tramite `scripts/prepare_runtime.py` e `scripts/package.ps1`; esclude progetti, recuperi automatici, corpus originale e ADB. Non cambiamo le regole personali del gitignore.

Un clone dei soli sorgenti non contiene automaticamente il corpus personale né il compilatore: per ricostruire l’EXE completo servono `data/watchface-library.json`, i relativi asset (rigenerabili dai 39 quadranti con `scripts/create_watchface_library.py`), il template collaudato e EasyFace 4.23 verificato. Lo script interrompe il packaging se qualcosa manca. Questa copia incorpora risorse dell’utente per uso personale; provenienza e avvisi sono in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Novità 0.8

- Avvio in finestra massimizzata; label **Version 0.8**.
- **Salva progetto chiede sempre il nome**, anche dopo il primo salvataggio. Annullare conserva percorso e modifiche; il recupero automatico resta senza dialoghi.
- Voce in hover evidenziata nei menu, anteprima delle lancette senza applicare la scelta.
- Catalogo completo dei 39 quadranti: **595 modelli**, 526 bitmap madri distinte, **108 modelli piccoli** e 407 abbinamenti con ombre. Comprende risorse nei gruppi/slot, AOD e rotazioni segmentate; tutti i 1.310 puntatori del corpus sono inventariati.
- Scegli il modello **ore** e premi **Usa modello**: abbina minuti e secondi disponibili dello stesso set. Minuti e secondi possono poi essere cambiati separatamente. Le ombre corrispondenti si importano automaticamente; il flag **Mostra le ombre abbinate** ne controlla la visibilità. Un set privo di secondi li disattiva; puoi riattivarli e scegliere la grafica.
- Le lancette piccole ruotano dall’estremità visibile e scalano rispetto alla lunghezza effettiva della grafica. Il perno è identico nella preview e nel binario; puoi usare anche un pivot manuale.
- `.gitignore` ampliato conservando byte per byte tutte le righe precedenti.

Guida: [EDITOR_0.8.md](docs/EDITOR_0.8.md). Esempio: `projects/S5_Studio_Lancette_0.8.s5faceproj`; ZIP: `S5_Studio_Lancette_0.8_TEMPLATE.zip`. Verifica: **66 test passati**, compilazioni EasyFace reali e prove DOM. Il successivo test reale NASA della 0.8 è stato superato dall’utente.

## Novità 0.7

- Hover sui modelli: anteprima grafica, senza applicare la scelta. Il riquadro vuoto non carica immagini mancanti.
- Immagini fino a 4096 px per lato, coordinate negative, scala percentuale e centratura. Anteprima ed esportazione conservano solo la finestra 480×480.
- Frecce: 1 px; Maiusc + frecce: 10 px, per qualsiasi livello selezionato. Sono rispettati campi di testo, menu, blocco, stili, AOD e annulla.

Guida: [EDITOR_0.7.md](docs/EDITOR_0.7.md). Esempio: `projects/S5_Studio_Ritaglio_0.7.s5faceproj`; ZIP: `S5_Studio_Ritaglio_0.7_TEMPLATE.zip`. Verifica: 58 test passati e prove DOM nell’eseguibile reale.

## Funzioni dell’editor

- Elimina un livello con × sulla riga, con Elimina nelle proprietà o con Canc; Annulla ripristina anche cancellazione e ordine.
- Trascina una riga del pannello livelli sopra/sotto un’altra: le righe in cima sono davanti. Anche le complicazioni seguono questo ordine nell’anteprima e nel binario.
- Colore per livello, tinta facoltativa sulle immagini e colori distinti di ore, minuti e secondi, anche su modelli PNG/SVG.
- Ridimensiona le immagini con le maniglie agli angoli, larghezza/altezza o Riempi quadrante / Adatta al bordo. Il mantenimento delle proporzioni è disattivabile.
- Opacità da **0 a 100**, a passi di 1: 0 invisibile, 100 completamente visibile. Le immagini originali sono conservate nel progetto.
- Le nuove complicazioni sono livelli con **solo il valore**, senza cornice, etichetta o icona preimpostata. Spostale sul canvas e scegli le informazioni nella scheda Complicazioni; le decorazioni restano facoltative. I progetti precedenti conservano la propria grafica.
- Lancetta piccola indipendente: posizione, dimensioni, grafica, pivot, colore, sorgente dati, intervallo e angoli. Puoi duplicarla per più sottoquadranti. Secondi/minuti dell’ora, batteria o altri dati del quadrante guidano la rotazione; dalla 0.10 le voci Crono usano il framework Lua interattivo descritto sopra.
- Menu a tendina con scelta confermata tramite clic o Invio; passaggio del mouse e frecce non cambiano il valore salvato.

Avvio e istruzioni: [EDITOR_0.6.md](docs/EDITOR_0.6.md). Esempio: `projects/S5_Studio_Crono_0.6.s5faceproj`; ZIP: `S5_Studio_Crono_0.6_TEMPLATE.zip`.

## Creare un quadrante

1. Scegli Analogico, Digitale o Salute. Importa uno sfondo PNG/JPEG/WebP/BMP/SVG e posiziona i livelli sul canvas.
2. Seleziona Lancette. Regola dimensioni, lunghezza, spessore, tacche e secondi. Per ogni lancetta scegli un modello dalla galleria o importa PNG/SVG; pivot e bitmap vengono incorporati nel progetto. Sono disponibili **595 modelli** dai tuoi quadranti, con autore, provenienza, ombre abbinate e set, comprese lancette piccole e indicatori. Le immagini personalizzate devono puntare alle ore 12.
3. Apri Varianti grafiche e duplica lo stile, fino a cinque. Cambia colore, sfondo, immagine o proprietà del livello. “Modifica soltanto questo stile” consente anche lancette diverse per variante.
4. Apri Complicazioni e aggiungi cinque o più slot: **fino a 16 nel progetto Studio**, un limite applicativo, non il massimo certificato del firmware. Ogni slot nuovo mostra solo il valore; posizione, dimensioni, colore e ordine sono modificabili come per gli altri livelli. Cornice, etichetta e unità sono facoltative. Seleziona le informazioni offerte all’utente e quella iniziale. La simulazione cambia soltanto la preview, senza cambiare il default del progetto.
5. Le **58 sorgenti dati** osservate comprendono pulsazioni, passi, SpO₂, sonno, movimento, meteo con icone, temperature, umidità, vento, bussola, quota, pressione, batteria e calendario. Sono canali del framework dei quadranti, non accesso arbitrario ai sensori grezzi. Tre sorgenti di testo formattato presenti nei campioni non sono ancora esportabili come testo dinamico; vedi il rapporto.
6. Configura AOD: è comune agli stili, senza secondi e senza slot. Salva `.s5faceproj`, poi Esporta ZIP e scegli la cartella. Apri esportazione mostra il pacchetto pronto.

I progetti incorporano immagini e font, leggono schema 1/2 e salvano schema 2. Riordino, drag, duplicazione, annulla/ripristina e recupero automatico sono disponibili. Nome e ID sono modificabili in Progetto; i nuovi progetti ricevono un ID personale per ridurre collisioni con Suit and tie.

## Prova pronta

- Eseguibile attuale: **S5Studio-1.7.5.exe** (autonomo).
- Esempio storico 0.8 conservato: **S5_Studio_Lancette_0.8_TEMPLATE.zip** e **projects/S5_Studio_Lancette_0.8.s5faceproj**.
- ZIP: **S5_Analogico_Libero_0.5_TEMPLATE.zip**.
- Progetto: **projects/S5_Analogico_Libero_0.5.s5faceproj**.
- Istruzioni: [PROVA_S5_0.5.md](docs/PROVA_S5_0.5.md).

Il test ha cinque colori e cinque slot indipendenti, inizialmente Passi, Pulsazioni, Temperatura, Bussola e Meteo; ogni slot offre quindici scelte. Le anteprime sono render del progetto con valori simulati. Il binario usa sorgenti native aggiornabili. Lo ZIP 0.5 è stato testato con successo dall’utente e rimane conservato. La 0.9 non aggiunge altri pacchetti dimostrativi: crea e salva il tuo progetto dall’applicazione.

L’originale Suit and tie fallisce anch’esso capabilities nel percorso locale della mod, mentre il catalogo e Modifica funzionano. La lista locale può quindi continuare a mostrare un nome generico o nessuna immagine. Non è stata dimostrata una soluzione tramite Regione.

## Packaging e verifica

Ogni build produce ZIP, `resource.bin`, `.face` identico, anteprime, progetto, FPRJ con bitmap, log e rapporto. Il packaging usa il template verificato: **187 file protetti e 8 directory conservano i record ZIP originali**, incluse capability e hashCode. Sostituisce binario e 28 anteprime; rigenera description, manifest, uidmap ed editor insieme alle risorse nuove. Preservare questi ultimi metadati invariati descriverebbe ancora Suit and tie, rendendo incompleto un quadrante modificabile.

È stata compilata e validata anche una configurazione con cinque slot, cinque stili e tutte le 58 sorgenti più Nessuna in ciascuno slot (22.524 voci ZIP); rapporto in `docs/stress-all-sources-0.5.json`. Il validator confronta CRC, file protetti, ID, offset, temi, UID, layout, sorgenti, opzioni, gruppi e anteprime. Rifiuta incoerenze prima dell’esportazione. La firma strutturale locale non è una firma crittografica Xiaomi e non certifica la verifica capabilities della mod.

L’analisi di `quadranti/` copre **39 cartelle e 7.513 file**, senza eseguire contenuti ricevuti. Inventari, hash e metadati: [catalogo](docs/library-analysis/inventory.md). Ferrari è attribuito a HaloX78, come confermato dall’utente, e non trattato come OEM Xiaomi.

Dettagli: [analisi e correzioni 0.5](docs/ANALISI_QUADRANTI_E_CORREZIONI_0.5.md), [analogico e slot](docs/ANALOGICO_VARIANTI_COMPLICAZIONI.md), [stato](docs/STATO_IMPLEMENTAZIONE.md), [analisi iniziale del template](docs/RAPPORTO_TEMPLATE_FUNZIONANTE.md).

## Sviluppo e CLI

```powershell
python -m pip install -r requirements-dev.txt
python main.py
python -m pytest -q
python main.py ui-smoke --screenshot docs/screenshots/ui-test.png
python main.py build projects/S5_Analogico_Libero_0.5.s5faceproj --compiler tools/easyface-4.23/Compiler.exe --output build/prove
python main.py apply-template progetto.s5faceproj quadrante_funzionante.zip output-template
python main.py apply-template progetto.fprj quadrante_funzionante.zip output-template
python main.py validate-template quadrante_funzionante.zip S5_Analogico_Libero_0.5_TEMPLATE.zip
```

`apply-template` riconosce i FPRJ esportati da Studio e ricostruisce anche stili/slot dal progetto incorporato, controllando gli hash dei sorgenti. Per FPRJ esterni supporta immagini, cifre, liste di immagini e lancette; altri widget sono rifiutati quando non è possibile rigenerare metadati coerenti.

CSS: `npm ci` e `npm run build` in `frontend/`. Desktop personale autonomo: `scripts/package.ps1`, con preflight dei 708 file tramite `scripts/prepare_runtime.py`. Controllo rapido degli hash del bundle: `scripts/verify_bundle.py`. Su richiesta dell’utente, dalla 0.11 non si esegue più la prova dell’EXE in una cartella isolata. L’app non richiede Node. Gli archivi storici fino alla 0.8 in `deliverables/` escludono compilatore e template; per la 1.5 viene prodotto soltanto l’EXE completo richiesto. Vedere [provenienza e licenze](THIRD_PARTY_NOTICES.md).

## Workflow delle prossime release

Su richiesta dell’utente dell’8 ottobre 2026, **non creare nuovi backup di regressione**. Aggiornare README, guida della versione e rapporti con modifiche e risultati effettivi dei test. Eseguire le verifiche pertinenti alle parti modificate, ampliandole soltanto quando necessario; creare soltanto l’eseguibile richiesto. Verificare staticamente risorse e codice incorporati, senza avviare l’EXE in ambiente isolato. Non creare quadranti dimostrativi salvo stretta necessità. I backup già esistenti restano documentati.
