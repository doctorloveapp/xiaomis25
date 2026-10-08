# S5 Studio 1.2 — Stili indipendenti e Crono-Pro orario

Editor desktop italiano per Xiaomi Watch S5 M2530W1, 480 × 480. Crea quadranti digitali e analogici, cinque stili e complicazioni con grafica personalizzabile. La UI usa Tailwind CSS compilato offline e QtWebEngine.

Avvia **S5Studio-1.2.exe** oppure **Avvia_S5_Studio.cmd**. Salva il lavoro della versione precedente prima di aprire la nuova. Questo eseguibile personale è autonomo: incorpora Python, Qt, UI Tailwind, cataloghi di lancette/bussole/meteo, template verificato e Compiler.exe con DeviceInfo.db. Puoi copiarlo da solo su un altro PC Windows a 64 bit con **.NET Framework 4.7.2 o successivo**. All’avvio estrae le risorse in una cartella temporanea; il recupero del lavoro usa `%LOCALAPPDATA%/S5Studio/`. Non serve installare Python o Node.

Il test sul S5 della build 0.5 è **superato**: installazione, cambio varianti e selezione complicazioni, come confermato dall’utente. Il pacchetto testato resta conservato. La 0.7 aggiunge anteprima delle lancette in hover, immagini oltre 480 px con ritaglio in compilazione e spostamento di ogni livello con le frecce. Le nuove funzioni sono verificate sul PC.

## Novità 1.2

**Rientri Crono Pro sempre in senso orario**: preparazione allo zero e Reset del gruppo usano il percorso orario, anche quando è più lungo. Restano sincronizzati, fluidi per 320 ms con target 25 fps; conteggio a scatti e annullamento immediato in AOD. La simulazione usa lo stesso criterio. Sono gestite anche scale parziali o con rotazione inversa: il rientro fisico resta orario.

**Ogni stile possiede i propri livelli.** Nel pannello **Livelli e proprietà → Stile in modifica** scegli la variante. Duplica uno stile, poi aggiungi, cancella, nascondi, trascina, riordina e modifica le sue immagini, lancette, sorgenti o complicazioni: gli altri stili non vengono alterati. Non serve più il flag “Modifica soltanto questo stile”. “Sfondo da immagine” sostituisce lo sfondo dello stile selezionato, senza lasciare l’immagine coperta dal quadrante principale.

I progetti precedenti vengono convertiti in memoria conservando l’aspetto di ogni stile. Il salvataggio usa lo **schema 3**, con risorse di tutti gli stili; salva una copia per conservarne una apribile nelle versioni precedenti. L’AOD rimane una schermata comune abbinata agli stili. Il compiler genera risorse, anteprime reali e complicazioni da ciascuna lista indipendente. Guida: [EDITOR_1.2.md](docs/EDITOR_1.2.md).

Il **primo test reale Crono Pro 1.1 è superato**, con fluidità confermata dall’utente. Sorgenti, risorse ed EXE 1.1 sono conservati nel [backup verificato](docs/stable-baseline-1.1.json); il crono separato mantiene il core 1.0. Le novità 1.2 richiedono la nuova prova sull’S5. Verifica PC: **127 test automatici e 100 controlli dell’editor superati**. Rapporti: [validation-editor-1.2.json](docs/validation-editor-1.2.json), [executable-build-1.2.json](docs/executable-build-1.2.json). Nessuna prova EXE in ambiente isolato; viene consegnato solo l’eseguibile.

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

- Eseguibile attuale: **S5Studio-1.2.exe** (autonomo).
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

CSS: `npm ci` e `npm run build` in `frontend/`. Desktop personale autonomo: `scripts/package.ps1`, con preflight dei 708 file tramite `scripts/prepare_runtime.py`. Controllo rapido degli hash del bundle: `scripts/verify_bundle.py`. Su richiesta dell’utente, dalla 0.11 non si esegue più la prova dell’EXE in una cartella isolata. L’app non richiede Node. Gli archivi storici fino alla 0.8 in `deliverables/` escludono compilatore e template; per la 1.2 viene prodotto soltanto l’EXE completo richiesto. Vedere [provenienza e licenze](THIRD_PARTY_NOTICES.md).

## Workflow delle prossime release

Su richiesta dell’utente dell’8 ottobre 2026, **non creare nuovi backup di regressione**. Aggiornare README, guida della versione e rapporti con modifiche e risultati effettivi dei test. Eseguire le verifiche pertinenti alle parti modificate, ampliandole soltanto quando necessario; creare soltanto l’eseguibile richiesto. Verificare staticamente risorse e codice incorporati, senza avviare l’EXE in ambiente isolato. Non creare quadranti dimostrativi salvo stretta necessità. I backup già esistenti restano documentati.
