# S5 Studio 0.9

Apri **S5Studio-0.9.exe**. Questa copia personale contiene UI, librerie, template e compilatore: su un altro PC servono l’EXE e Windows a 64 bit con .NET Framework 4.7.2 o successivo. Il contenuto di `data/` non deve essere copiato separatamente. Gitignore e contenuto dell’eseguibile sono indipendenti; un clone dei soli sorgenti richiede invece le risorse personali prima del packaging.

## Pivot con un clic

1. Seleziona il livello lancette o lancetta piccola. Scegli **Usa modello** oppure importa la tua immagine.
2. Nelle proprietà apri la lancetta interessata. Sotto la galleria trovi **Pivot · clicca sulla grafica applicata**: mostra anche le immagini personalizzate.
3. Clicca sul perno desiderato. X e Y vengono calcolati in pixel del file originale, considerando il ritaglio della preview e la scala dello schermo. La croce mostra il nuovo perno; puoi ancora correggere i numeri manualmente.
4. Per una lancetta piccola il clic disattiva **Perno all’estremità**. Riattivalo per tornare alla scelta automatica. Le ombre abbinate mantengono il riferimento geometrico del modello.

L’anteprima in hover del menu serve per esplorare i modelli. Il riquadro Pivot agisce sulla grafica già applicata al livello, evitando di cambiare il progetto quando passi sul catalogo. Annulla ripristina pivot e modalità automatica; anche le varianti possono avere pivot diversi.

## Lunghezza e spessore

Funzionano anche con PNG/SVG importati e modelli del catalogo. Lunghezza è la distanza verticale tra perno e punta, espressa in percentuale del lato più corto del livello; spessore è la larghezza massima visibile in pixel. Entrambe le trasformazioni sono applicate anche alle ombre. Preview, FPRJ e binario usano le stesse bitmap e lo stesso pivot.

I progetti della 0.8 conservano la dimensione nativa degli asset fino alla prima modifica del relativo controllo. La lunghezza precedente delle lancette piccole resta attiva. Modificare una sola dimensione conserva l’altra dove possibile; le bitmap emesse restano entro 480 px per lato. Puoi usare valori di lunghezza 1–100% e spessore 1–100 px. I file originali non vengono riscritti. Salva i progetti modificati con la 0.9 e riaprili con la 0.9.

## Informazioni delle lancette piccole

Il menu offre 58 sorgenti native distinte, senza i doppioni dei vecchi nomi Studio. Il passaggio del mouse o il focus da tastiera mostra una breve spiegazione nel popup. Clic o Invio confermano il valore.

| Voce | Alle 14:37 |
| --- | --- |
| Ora completa (0–23) | 14 |
| Cifra delle ore · unità | 4 |
| Cifra delle ore · decine | 1 |
| Minuti completi (0–59) | 37 |
| Cifra dei minuti · unità | 7 |
| Cifra dei minuti · decine | 3 |

Le cifre separate servono per indicatori della singola cifra. Per una lancetta oraria usa Ora completa; per minuti e secondi usa il valore completo con intervallo 60 e rotazione 360°. Intervallo e angoli rimangono modificabili. Meteo e barometro sono distinti, come direzione del vento e bussola reale.

### Sottoquadrante NASA a 24 ore

La scala dello screenshot `Documenti/screen_lancetta_piccola_ore.png` mostra 6 a destra, 12 in basso e 18 a sinistra: richiede un giro completo in 24 ore. Scegli Ora completa (0–23), valore iniziale 0, intervallo valori 24, angolo iniziale 0° e rotazione totale **360°**. Il modello mostrato nella preview punta verso l’alto, come lo zero della scala.

Il suggerimento generico 24/720 del menu descrive una scala a **12 ore**, che deve compiere due giri al giorno. Valore iniziale è il dato associato all’angolo iniziale, non un orario da impostare all’installazione. Per controllare l’allineamento usa Simula: 00:00 in alto, 06:00 a destra, 12:00 in basso, 18:00 a sinistra. Cambia l’angolo iniziale solo per un offset costante della grafica o per uno zero disegnato in una posizione diversa.

## Bussola analogica

Premi **Bussola analogica**: viene aggiunto un livello con la rosa completa Ferrari. Nel catalogo scegli un modello, guarda la preview e premi **Usa modello**. Puoi importare una grafica orientata al nord verso l’alto, spostarla, ridimensionarla, cambiare opacità e attivare Ricolora. Le bussole sono indipendenti e possono stare sopra/sotto qualsiasi livello.

Sono disponibili otto grafiche originali osservate in Bouldering, Gear jungle, Ferrari e LLATH, più le due rose complete Bouldering e Ferrari. La composizione Ferrari comprende lettere/tacche e ago dello screenshot fornito. I file originali restano intatti e la provenienza è nel catalogo.

Il pivot è sempre al centro della bitmap. La sorgente nativa è `systemSensorCompass`, codice osservato `5042`, con valori 0–360 e angoli 0→−360°. La rotazione inversa mantiene il nord della rosa nella direzione del nord reale. Il campo **Bussola °** nell’area Simula modifica esclusivamente l’anteprima: il quadrante compilato legge il sensore dell’orologio. Il funzionamento reale della nuova bussola sul Watch S5 è stato confermato dall’utente nel successivo test positivo della 0.9 (hardware-test-0.9.json).

## Zoom e panoramica

Usa i pulsanti −/+, il menu 50–400% o Ctrl + rotella. A 100% il canvas ha 480 px sullo schermo. **Centra selezione** porta l’oggetto selezionato al centro dell’area visibile; **Ripristina** torna al 100%. Scorri oppure tieni Spazio mentre trascini; è disponibile anche il tasto centrale del mouse.

Il livello mantiene posizione e dimensioni del progetto, qualunque sia lo zoom. Le frecce spostano di 1 px, Maiusc + frecce di 10 px. Il canvas esportato rimane 480×480. Zoom e panoramica sono impostazioni della vista e non rendono il progetto modificato.

## Evidenze e distribuzione

Il test reale NASA della 0.8 è stato dichiarato superato dall’utente. `projects/NasaS5.s5faceproj` non è stato modificato: la preview prodotta dalla 0.9 coincide byte per byte con quella dell’eseguibile 0.8. Evidenza: `nasa-migration-0.9.json`.

Sono passati **77 test automatici** e **66 controlli dell’interfaccia reale** nell’EXE isolato. Le 705 risorse incorporate corrispondono ai rispettivi SHA-256. La compilazione temporanea con due stili e AOD produce un binario identico a quello dei sorgenti, con bussola 5042, range 360° e perni centrali su tutte e quattro le schermate. I test della 0.9 comprendono geometria, ombre, pixel del pivot, salvataggio, sorgenti, trasformazioni bitmap, descrittore bussola compilato e interazioni nel vero QtWebEngine, oltre alla regressione precedente. La verifica dell’EXE si svolge in una cartella temporanea senza `data/`, `tools/` o template adiacenti; usa fixture di compilazione temporanee, non produce un nuovo quadrante dimostrativo nella root. Manifest delle risorse: `runtime-manifest-0.9.json`; rapporto finale: `executable-build-0.9.json`.

All’avvio PyInstaller estrae le risorse incorporate in una cartella temporanea. I progetti si salvano nel percorso scelto; il recupero automatico usa `%LOCALAPPDATA%/S5Studio/`. La copia è personale, con asset del corpus fornito: provenienza e licenze sono documentate in `THIRD_PARTY_NOTICES.md` incorporato. Le regole aggiunte dall’utente al gitignore restano inalterate.
