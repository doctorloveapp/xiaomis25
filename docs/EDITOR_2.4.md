# S5 Studio 2.4 — Dischi, calendario e Only Crono

## Catalogo Dischi

La nuova scheda **Dischi**, accanto a **Set lancette**, contiene 89 modelli recuperati dai 39 pacchetti: 13 celesti, 12 bussole, 1 rotore meccanico e 63 quadranti/ghiere. Sono conservate 515 immagini, incluse le sequenze complete. L'inventario e la provenienza sono in [discs-2.4.json](library-analysis/discs-2.4.json).

Esistono due modalità:

- **Disco rotante**: una PNG ruota attorno al pivot. Seleziona il dato nativo e calibra valore iniziale, intervallo, angolo iniziale e rotazione totale. La bussola usa `systemSensorCompass`, intervallo 360 e rotazione −360°. Un disco giornaliero può usare Ore, intervallo 24 e rotazione 360°.
- **Immagini per valore**: il firmware sceglie l'immagine della sequenza originale. I dischi lunari usano `dateLunarDay` (giorni 1–30), `dateMoon` (otto fasi), oppure la sorgente specifica recuperata. Non vengono trasformati arbitrariamente in dischi giornalieri. Il selettore **Immagine della sequenza** permette di sostituire ciascuna PNG; **Nuovo valore** aggiunge un'immagine.

Le grafiche statiche recuperate ricevono come punto di partenza un giro in 24 ore; questo è un default dell'editor, non la ricostruzione di una funzione astronomica originale. Il rotore meccanico recuperato usa i secondi nativi: la sequenza sprite originale non viene riprodotta. Le immagini che già contengono numeri o indicazioni mantengono quegli elementi nella PNG; non diventano livelli separati.

Per usare un modello premi **Aggiungi** nel catalogo, oppure **Disco** nella barra degli oggetti e **Usa modello** nelle proprietà. Ogni disco è un livello indipendente, posizionabile, ridimensionabile e riordinabile; ogni stile conserva i propri livelli. Un disco dinamico, come la precedente bussola, deve stare sopra o sotto il gruppo di lancette Lua Crono Pro quando l'editor richiede una scena unica.

Per creare un disco scegli **Nuovo disco**, assegna nome, categoria e sorgente, importa una PNG statica fino a 480×480 px e salva. Il pivot parte dal centro della PNG e può essere regolato con un clic o con coordinate. Per le sequenze il pivot è comune a tutte le immagini, che devono avere le stesse dimensioni. Cambiare modalità conserva solo la prima immagine della bozza, dopo conferma nell'interfaccia.

**Genera ombre** crea ombre nere semitrasparenti dalla sagoma, con opacità, sfocatura e spostamento regolabili. Le ombre importate non vengono sovrascritte. Le sequenze generano un'ombra per ogni immagine; le ombre importate di una sequenza devono coprire tutte le immagini e condividere geometria. Nel progetto **Mostra le ombre abbinate** le abilita o nasconde. Il pivot dell'ombra automatica segue quello del disco. Le ombre delle sequenze sono rasterizzate all'esportazione, senza timer Lua aggiuntivi.

Tutti i modelli possono essere modificati o eliminati, inclusi quelli incorporati. **Elimina** rimuove il modello dal catalogo e dai selettori, con persistenza tra gli avvii. I modelli incorporati eliminati si recuperano dalla sezione **Dischi incorporati eliminati → Ripristina**, nella versione originale. I file sorgente non vengono cancellati e i livelli già inseriti nei progetti rimangono utilizzabili. Le modifiche persistono in `%LOCALAPPDATA%/S5Studio/disks/` (avvio dai sorgenti: `data/disks/`). La cartella dei dischi PNG e quella delle ombre sono ricordate separatamente. Le PNG vengono incorporate nel progetto: modificare il catalogo non cambia un progetto già salvato; riapplica **Usa modello** per aggiornarlo.

**Calibrazione lunare:** i valori 24 / 360° sono il default generico del disco rotante. **Fasi lunari** fornisce otto stati, non giorni; **Giorno lunare** avanza ogni giorno ma riparte da 1 dopo 29/30. Impostare 59 come intervallo non genera una progressione continua di 59 giorni. L'aiuto contestuale è visibile nel catalogo e nelle proprietà. [Esempi di calibrazione e spiegazione della ruota a 59 denti](DISCHI_LUNARI_2.4.md).

Il catalogo iniziale è incluso nell'EXE sotto `resources/disks/`. I pacchetti sorgente e il vecchio catalogo bussole rimangono intatti. Rigenerazione dal corpus: `python -X utf8 scripts/create_disk_catalog.py`.

## Mesi e fasi lunari in Dato live

Con **Dato live → Mese**, il flag **Mese abbreviato** sceglie `JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC`. Senza flag restano January–December. Font, allineamento, colore, ombra, rotazione e arco continuano ad applicarsi. Il dato nativo resta `dateMonth`, valori 1–12; anteprima e compilazione condividono la stessa tabella.

**Dato live → Fasi lunari** mostra i nomi inglesi delle otto fasi: New Moon, Waxing Crescent, First Quarter, Waxing Gibbous, Full Moon, Waning Gibbous, Last Quarter, Waning Crescent. L'anteprima normale mostra **Full Moon**. Il collegamento è il dato nativo `dateMoon`, codice `7012`, osservato nel corpus; non si aggiunge un calcolo astronomico Lua. Per la rappresentazione grafica scegli invece un modello nella scheda Dischi.

## Lancetta piccola a 24 ore

**Dato che guida la lancetta → Ore (24h · giorno/notte)** segue l'ora solare, da 0 a 23. Imposta automaticamente 0 / 24 / 0° / 360° e disattiva un eventuale arco precedente. Alle 6, 12 e 18 indica rispettivamente 90°, 180° e 270°. L'angolo iniziale può essere adattato alla grafica.

Il progetto conserva `timeHour24` per identificare la scelta; il binario e il manifest usano il binding osservato `timeHour` (`0811`). Non viene inventato un nuovo sensore. La voce precedente **Ora completa (0–23)** conserva la calibrazione a 12 ore, 24 valori / 720°. Ore Crono rimane indipendente.

## Lancetta grande secondi Only Crono

Il flag **Only Crono**, nella sezione secondi grandi, abilita automaticamente Crono Pro e la lancetta secondi. A riposo resta a zero anziché indicare i secondi civili. La sequenza dei tap è quella esistente: Prepara → Avvia → Stop → Reset. Il conteggio dei secondi grandi resta a scatti; al Reset la lancetta torna a zero insieme alle piccole con il rientro fluido orario da 720 ms. Ore e minuti grandi continuano a mostrare l'ora solare.

La scena trasmette `onlyChrono=true` soltanto alla vista `studioIntegratedSecond`. La VM usa questo flag per il riposo e la destinazione del Reset, mantenendo lo stesso clock e la stessa macchina a stati. A riposo evita il ciclo a 25 fps della lancetta civile; l'AOD interrompe le transizioni e continua a escludere i secondi. Disattivando Only Crono ritorna il comportamento Crono Pro già collaudato. Disattivando Crono Pro o la lancetta secondi si disattiva anche Only Crono.

Il validator controlla che il flag della scena corrisponda al progetto; `build-report.json` elenca i gruppi Only Crono in `interactive.chronoPro.onlyChronoMainSeconds`.

## Verifiche e distribuzione

Controlli sui sorgenti, sul codice Lua eseguito con clock diretto e alternativo, sull'interfaccia e su un'esportazione temporanea con due stili e AOD. Nessun ZIP dimostrativo viene conservato. L'eseguibile non viene avviato né copiato in un ambiente isolato; il bundle viene verificato staticamente. La conferma sul dispositivo riguarda la 2.3: le nuove funzioni della 2.4 attendono il test reale dell'utente.

**Risultati:** 154 test sui sorgenti, 8 controlli dell'editor e 9 verifiche dell'esportazione superati. `S5Studio-2.4.exe` incorpora 1.236 risorse, compreso il catalogo dischi. Verificata senza avvio la corrispondenza dei 41 moduli Python, dell'entry point e dei cinque moduli Lua con i sorgenti testati.

**Aggiornamento eliminazione dischi:** 10 test sui dischi superati (8 precedenti e 2 nuovi), più 10 controlli dell'editor. Verificati pulsanti di eliminazione/ripristino dei modelli incorporati, persistenza su disco, conservazione delle PNG nei progetti salvati e aiuto contestuale lunare. Runtime Lua e percorso di esportazione invariati rispetto alla prima build 2.4.

L'eseguibile aggiornato è **S5Studio-2.4-aggiornato.exe**, con la stessa versione interna 2.4. Il precedente EXE era in uso e Windows ne impediva la sostituzione: la nuova build è stata prodotta con nome distinto senza interrompere la sessione dell'utente. Il launcher dà precedenza al nuovo file. Verificate staticamente tutte le 1.236 risorse, 41 moduli Python, entry point e cinque moduli Lua; nessun avvio dell'EXE.

[Editor](editor-2.4.json) · [Esportazione](export-validation-2.4.json) · [Validazione](validation-editor-2.4.json) · [Eseguibile](executable-build-2.4.json).
