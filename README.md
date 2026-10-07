# S5 Studio 1.0

Editor desktop italiano per Xiaomi Watch S5 M2530W1, 480 × 480. Crea quadranti digitali e analogici, cinque stili e complicazioni con grafica personalizzabile. La UI usa Tailwind CSS compilato offline e QtWebEngine.

Avvia **S5Studio-1.0.exe** oppure **Avvia_S5_Studio.cmd**. Salva il lavoro della versione precedente prima di aprire la nuova. Questo eseguibile personale è autonomo: incorpora Python, Qt, UI Tailwind, cataloghi di lancette/bussole/meteo, template verificato e Compiler.exe con DeviceInfo.db. Puoi copiarlo da solo su un altro PC Windows a 64 bit con **.NET Framework 4.7.2 o successivo**. All’avvio estrae le risorse in una cartella temporanea; il recupero del lavoro usa `%LOCALAPPDATA%/S5Studio/`. Non serve installare Python o Node.

Il test sul S5 della build 0.5 è **superato**: installazione, cambio varianti e selezione complicazioni, come confermato dall’utente. Il pacchetto testato resta conservato. La 0.7 aggiunge anteprima delle lancette in hover, immagini oltre 480 px con ritaglio in compilazione e spostamento di ogni livello con le frecce. Le nuove funzioni sono verificate sul PC.

## Novità 1.0

Il test prolungato della 0.11 ha mostrato minuti Crono fermi dopo il primo giro dei secondi, pur con sorgenti corrette. La 1.0 sostituisce gli App separati con **un’unica scena Lua per stile**: ore, minuti e secondi condividono lo stesso conteggio, timer e tap. La sincronizzazione non dipende più dalla condivisione della VM tra widget separati. I test coprono il passaggio del minuto e dell’ora, Stop/Reset e il giro oltre 12 ore. Il nuovo ZIP richiede la conferma sull’S5. Verifica PC: **95 test passati** e **84 controlli dell’editor**, compresa la compilazione reale con due stili e AOD. Guida: [EDITOR_1.0.md](docs/EDITOR_1.0.md).

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

- Eseguibile attuale: **S5Studio-1.0.exe** (autonomo).
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

CSS: `npm ci` e `npm run build` in `frontend/`. Desktop personale autonomo: `scripts/package.ps1`, con preflight dei 707 file tramite `scripts/prepare_runtime.py`. Controllo rapido degli hash del bundle: `scripts/verify_bundle.py`. Su richiesta dell’utente, dalla 0.11 non si esegue più la prova dell’EXE in una cartella isolata. L’app non richiede Node. Gli archivi storici fino alla 0.8 in `deliverables/` escludono compilatore e template; per la 1.0 viene prodotto soltanto l’EXE completo richiesto. Vedere [provenienza e licenze](THIRD_PARTY_NOTICES.md).
