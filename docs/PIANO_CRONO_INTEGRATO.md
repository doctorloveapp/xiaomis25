# Piano del cronografo integrato — base stabile 1.0

Valutazione dell’8 ottobre 2026. La 1.0 ha superato il test reale riferito dall’utente su tutte le lancette piccole. Anche **Decimi di secondo è già implementato e collaudato sull’S5**, come nuovamente confermato dall’utente: non è una funzione da rifare. Questa è una proposta di evoluzione: non modifica il runtime, i progetti o l’EXE collaudati.

## Giudizio di fattibilità

La macchina a stati, la lancetta grande ora/crono e i rientri animati sono tecnicamente realizzabili con il backend Lua già funzionante. Il rischio di regressione è **moderato**, perché occorre spostare la gestione dei secondi principali dal motore nativo a Lua e introdurre transizioni intermedie. È possibile limitare il rischio mantenendo il crono separato 1.0 come modalità predefinita e sviluppando il crono integrato in un runtime distinto.

Il successo del crono 1.0 conferma tap, Pointer e stato comune; il funzionamento dei decimi attuali è confermato e resta il riferimento per il loro movimento. La nuova verifica riguarda il collegamento dei decimi ad Avvio/Ferma/Azzera, la coerenza con il tempo trascorso comune e il carico aggiuntivo della lancetta grande. Non esiste ancora una misura che certifichi precisione cronometrica al decimo, 25 frame effettivamente mostrati al secondo, consumo massimo o assenza di shutdown nella **nuova modalità integrata**. Questi aspetti devono essere verificati sul dispositivo prima di promuovere quella modalità a stabile.

## Architettura consigliata: un solo proprietario della lancetta

Non propongo di cambiare a runtime la `source` di un `DataItemPointer` compilato, né di lasciare ora e crono a scrivere simultaneamente lo stesso oggetto. Non abbiamo documentazione che certifichi tale cambio sorgente sul firmware S5.

Nella modalità integrata il compilatore deve:

- mantenere ore e minuti principali come lancette native;
- omettere soltanto secondi principali e relativa ombra dall’elemento analogico nativo;
- ricreare questi secondi come `widgets.Pointer` Lua con gli stessi PNG, posizione, colore, scala e pivot;
- inserirli nella **stessa scena/VM** delle lancette piccole Crono, con un solo gestore del tap;
- mantenere tutti i secondi e il runtime Lua esclusi dall’AOD.

Il runtime riceve l’ora da `dataman.subscribe("timeSecond", ...)`, memorizza il valore e lo usa solo come input. La callback non deve scrivere direttamente l’angolo. Un solo aggiornamento decide quale valore mostrare in base allo stato; la priorità del firmware non viene contesa perché non rimane un secondo controller nativo su quella grafica. L’[esempio PointerTest](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand9Pro/PointerTest/app/lua/main.lua) mostra la sottoscrizione a `timeSecond` e l’impostazione manuale di `Pointer.value`. È una base API, non una prova del nostro futuro switch sull’S5.

Il callback dell’ora continua ad aggiornare il dato memorizzato durante il crono: al Reset abbiamo i secondi correnti. Per il movimento fluido dell’ora, il dato di sistema deve essere ancorato al clock monotono e risincronizzato a ogni aggiornamento reale. Se la sottoscrizione non fornisce un valore iniziale, occorre attendere il primo aggiornamento; non inventare l’ora e non assumere che `os.date` sia supportato o configurato con il fuso corretto.

La separazione grafica richiede attenzione all’ordine dei livelli: il renderer analogico attuale emette ore/minuti/secondi nello stesso elemento nativo. Vanno verificati ordine e ombre dopo la separazione. Anche il limite 1.0 sui livelli dinamici nativi interposti nella scena deve essere rispettato o risolto esplicitamente nel generatore, senza spostamenti silenziosi.

## Stati e sequenza dei tap

| Stato | Lancetta grande dei secondi | Lancette piccole | Azione del tap |
| --- | --- | --- | --- |
| RIPOSO | Secondi dell’ora | Decimi crono, minuti e ore a zero | Inizia il rientro a zero |
| POSIZIONAMENTO | Rotazione breve verso zero | Zero | Ignorato durante la transizione |
| PRONTO | Zero | Zero | Avvia il conteggio comune |
| IN_MARCIA | Secondi Crono | Decimi, minuti e ore Crono | Congela una sola misura per tutte |
| FERMO | Valore Crono congelato | Valori congelati | Inizia il Reset animato |
| RIENTRO | Ritorno ai secondi correnti dell’ora | Ritorno allo zero grafico | Ignorato durante la transizione |

Terminato RIENTRO si torna a RIPOSO. Il primo tap prepara il crono; il **secondo** lo avvia, come richiesto. Il tempo di posizionamento non entra nella misura. Se si tocca in PRONTO, tutte le lancette partono dallo stesso istante. Un tap in FERMO resetta: non introduce una funzione Riprendi che non è stata richiesta.

Usare l’evento `PRESSED` già collaudato, con filtro dei tocchi duplicati, un solo evento per pressione e blocco dei nuovi comandi durante i rientri. La pausa temporanea legata al tocco non deve nascondere la scena. Al ritorno da pausa/AOD, uno stato IN_MARCIA deve ricalcolare il tempo; una transizione incompleta deve terminare in uno stato definito, senza restare bloccata in POSIZIONAMENTO/Rientro. Ricreazione della VM o cambio quadrante continuano ad azzerare lo stato, come nella 1.0.

## Decimi crono e precisione

Estendere i decimi già funzionanti con una sorgente applicativa distinta, per esempio `studioChronoDecisecond`, con etichetta **Decimi crono**, intervallo 10, rotazione 360° e flag **Movimento Fluido**. Riutilizzare la grafica, il Pointer e il movimento già collaudati; aggiungere il legame con lo stato e il tempo del crono. La sorgente `studioDecisecond` esistente resta l’animazione continua indipendente, senza cambiare il comportamento dei progetti già salvati.

Con un clock monotono adeguato, tutte le lancette derivano da un’unica lettura di `elapsedMs`:

```text
decimiFluidi = (elapsedMs modulo 1.000) / 100
decimiAScatti = parteIntera(decimiFluidi)
secondiCrono = (elapsedMs / 1.000) modulo 60
minutiCrono = (elapsedMs / 60.000) modulo 60
oreCrono = (elapsedMs / 3.600.000) modulo 12
```

Un giro dei decimi dura un secondo, cioè 1 Hz; il disegno a 25 fps offre un campione ogni 40 ms. Frequenza di giro, frequenza di aggiornamento e precisione di misura sono proprietà diverse. Al comando Stop congelare `elapsedMs` prima di calcolare tutte le posizioni: il decimo letto deve corrispondere agli stessi secondi/minuti/ore.

**Prerequisito da verificare:** disponibilità e risoluzione effettiva di `lvgl.tick_get` o `/proc/uptime` sul firmware dell’utente, andamento monotono, wrap e comportamento durante schermo spento. Il fallback `os.time` della 1.0 restituisce secondi interi: con quella sola sorgente non si possono dichiarare decimi misurati. Incrementare un contatore di 40 ms a ogni callback introdurrebbe deriva e perderebbe il tempo durante le sospensioni; non è una soluzione affidabile.

La diagnostica iniziale deve quindi rendere visibile il clock scelto, la risoluzione osservata e i ritardi degli aggiornamenti con un campionamento limitato, senza log continui a 25 Hz. Se manca un clock adeguato, la modalità integrata può mantenere secondi/minuti/ore alla precisione disponibile, ma **Decimi crono va dichiarato non disponibile**, senza usare un’animazione decorativa come misura. Un’eventuale interpolazione tra secondi di sistema deve essere etichettata come stima e non spacciata per precisione certificata.

## Sweep to zero e rientro all’ora

Il `Pointer:set {value=...}` usato e collaudato nella 1.0 permette di impostare valori intermedi. Non serve un’API speciale per azzerare: il runtime può interpolare dal valore visualizzato allo zero, rispettando intervallo e angolo iniziale.

Gli esempi pubblici [HandImageAnim](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand8Pro/AnalogTimeAnimated/app/lua/image.lua) e [AnalogTimeAnimated](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand8Pro/AnalogTimeAnimated/app/lua/main.lua) mostrano `Anim` con callback che imposta la rotazione e riavvio dell’animazione all’aggiornamento dei secondi. Si può usare un progresso Anim comune per aggiornare i Pointer, oppure il timer comune se il clock subsecondo è disponibile. Non è necessario presumere supporto di callback Lua non osservate, come `ready_cb`, o di trasformazioni native non verificate.

Proposta iniziale: transizioni da **250–400 ms**, percorso breve e deterministico, interpolazione angolare continua senza salti a 359°/0°, grafica e ombra aggiornate insieme. Usare angoli non avvolti durante il rientro e normalizzare soltanto al disegno. Lo zero deve essere quello della grafica configurata, non un angolo assoluto identico per tutte le lancette.

Nel rientro della lancetta grande, la destinazione è l’ora **corrente alla fine dell’animazione**: non il secondo memorizzato al tap. Il runtime continua a ricevere il tempo e completa la transizione senza uno scatto al riaggancio. Una pausa durante il rientro deve cancellare/riconciliare la transizione e ripristinare la destinazione corretta al risveglio.

## Consumo, prestazioni e stabilità

25 fps è un obiettivo prudente già usato dal timer Crono e dai secondi fluidi nativi, ma **non certifica un limite energetico del firmware**. Una lancetta lunga può invalidare un’area molto più grande di una piccola; ombre e altre animazioni aumentano il lavoro. Aggiornare quattro lancette in una scena a 25 Hz è plausibile, ma non abbiamo misure per escludere micro-scatti, consumi anomali o chiusura del quadrante.

La nuova modalità deve usare un solo scheduler da 40 ms e una sola lettura del clock per aggiornamento, limitando anche i rientri a tale obiettivo. Non assumere che il motore `Anim` abbia un parametro Lua `fps=25`: non è stato osservato. Se Anim produce callback più frequenti, limitare gli aggiornamenti grafici e applicare sempre l’ultimo valore di fine transizione.

Precaricare bitmap e ombre; evitare creazione/distruzione di oggetti, decodifica immagini, letture di file per ogni lancetta e log a ogni frame. Aggiornare soltanto i valori cambiati. Minuti/ore senza flag fluido non richiedono una nuova scrittura grafica 25 volte al secondo. In FERMO e PRONTO le viste Crono restano statiche; in RIPOSO si aggiorna solo la lancetta grande; in AOD/schermo spento non si disegna e non si mantiene un timer di animazione attivo.

La fluidità dell’ora civile e l’esattezza del tempo trascorso devono restare separate. Una correzione dell’ora/Bluetooth cambia l’ora mostrata a riposo, ma non deve cambiare un crono basato su clock monotono. Il fallback al clock civile conserva le limitazioni già documentate della 1.0.

## Piano di implementazione progressivo

1. **Conservare il riferimento stabile.** Snapshot dei sorgenti e delle 707 risorse runtime, hash dell’EXE 1.0 e archivio sorgenti verificato. L’EXE resta invariato. Il percorso e il contenuto del punto di ripristino sono in [stable-baseline-1.0.json](stable-baseline-1.0.json).
2. **Verificare il clock sull’S5.** Diagnostica minima nella futura build sperimentale per misurare la risoluzione disponibile. Questo passaggio decide se offrire decimi Crono reali. Non richiede riscrivere o distribuire il crono 1.0.
3. **Introdurre la modalità facoltativa.** Campo progetto `chronoMode` con default `separate`; runtime distinto, per esempio `studio_core_integrated.lua`. I progetti precedenti e la compilazione separata continuano a usare il percorso 1.0. Migrazione esplicita, senza sovrascrivere il progetto NASA esistente.
4. **Separare i secondi principali.** Render/compilazione di ore e minuti nativi, secondi e ombra Lua nella scena condivisa. Provare prima il solo movimento dell’ora, ordine dei livelli, pivot, varianti, ritorno da AOD e assenza di due lancette sovrapposte.
5. **Macchina a stati senza animazioni.** Verificare prima RIPOSO → PRONTO → IN_MARCIA → FERMO → RIPOSO, calcoli comuni e congelamento. Poi aggiungere i rientri brevi, gestione dei tocchi rapidi e riconciliazione delle pause.
6. **Decimi crono.** Aggiungere menu, help, flag fluido, simulazione, render, salvataggio e backend; sincronizzazione sul clock unico, 25 Hz e Stop coerente. Con clock insufficiente mostrare il limite, senza decimi fittizi.
7. **Validator e rapporto.** Verificare un’unica scena, un solo proprietario dei secondi principali, bitmap/ombre/script identici al binario, manifest interattivo, esclusione AOD e retrocompatibilità dei report 1.0. Registrare modalità, clock/precisione richiesti, periodo 40 ms, transizioni e file iniettati. La risoluzione effettiva del clock può essere misurata solo a runtime, non certificata dal compilatore.
8. **Verifica e release sperimentale separata.** Test Lua con timer irregolari, clock che avvolge o viene corretto, Stop vicino a un decimo/minuto/ora, tap duplicati, pausa durante ogni transizione, ripresa da AOD, cinque stili e scale/pivot personalizzati. Verificare anche la parità della modalità separata con la base 1.0. Poi test reali progressivi su S5: prima secondi principali, poi stati, poi decimi/rientri, infine prova prolungata e confronto del consumo con la 1.0 nelle stesse condizioni. Niente prova EXE in ambiente isolato, secondo la preferenza dell’utente.

La promozione a stabile richiede un test fisico positivo della modalità integrata, senza sparizione delle lancette, doppio comando, deriva evidente, rientri errati o degrado significativo rispetto alla 1.0. Un test sintetico non può garantire da solo questi risultati.

## Ripristino e alternativa conservativa

Il ripristino è concreto: l’archivio `build/recovery/S5Studio-1.0-stable-20261008.zip` contiene **786 file**, comprese le **707 risorse runtime**, i sorgenti e una copia dell’**esatto EXE 1.0**. Tutti i payload sono stati verificati tramite SHA-256 e CRC ZIP, senza avviare l’eseguibile. Il manifest interno `stable-baseline-manifest.json` permette di verificarli anche in futuro. Il rapporto esterno è [stable-baseline-1.0.json](stable-baseline-1.0.json); il backup resta locale e non è incluso nel repository perché si trova in `build/`.

Per ripristinare: verificare l’hash dell’archivio riportato nel rapporto, estrarlo in una **cartella nuova**, verificare gli hash del manifest e usare la copia `S5Studio-1.0.exe`. Il backup contiene anche i file ignorati dal Git ma necessari al runtime, senza progetti personali o corpus originale. Non serve `git reset --hard` e non si sovrascrivono i progetti dell’utente. Le dipendenze Python devono essere disponibili per ricompilare; per riusare il software stabile basta l’EXE conservato. Conservare il backup anche fuori da `build/` prima di eventuali pulizie della cartella di build.

Il backup non può annullare eventuali aggiornamenti esterni di firmware, Windows o toolchain né promettere un nuovo EXE byte per byte identico dopo una ricompilazione. Garantisce invece il recupero dei sorgenti/risorse archiviati e l’uso del **medesimo EXE 1.0 verificato**, finché vengono conservati. I progetti della nuova modalità vanno salvati con nome diverso e gli ZIP funzionanti conservati: tornare al software non reinstalla automaticamente un quadrante precedente sull’orologio.

Se la gestione Lua dei secondi principali si rivela instabile, mantenere i secondi dell’ora nativi e il crono separato già collaudato; aggiungere soltanto rientri animati alle lancette piccole e Decimi crono quando il clock lo consente. Questa è l’alternativa più vicina con minore impatto. Nascondere/mostrare due lancette sovrapposte è una seconda possibilità, ma dipende dal controllo di visibilità del layer nativo: non la assumiamo supportata senza verifica. Non propongo modifiche al firmware o agganci a sorgenti non documentate.
