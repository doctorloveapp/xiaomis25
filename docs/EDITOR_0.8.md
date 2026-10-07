# S5 Studio 0.8

Avvia `S5Studio-0.8.exe` dalla cartella del progetto o usa `Avvia_S5_Studio.cmd`. La finestra si apre massimizzata, con barra del titolo e pulsanti Windows. La label è **Version 0.8**. Il pulsante **Salva progetto** e Ctrl+S chiedono ogni volta il nome del file, suggerendo quello precedente. Annullare conserva percorso e modifiche. Il recupero automatico continua senza finestre.

## Lancette e ombre

Seleziona un livello Lancette, apri Lancetta ore, scegli un modello e premi **Usa modello**. Verranno applicati anche i membri minuti/secondi disponibili dello stesso set, con le rispettive ombre. Apri Lancetta minuti o Lancetta secondi per scegliere una grafica diversa: le altre restano come le hai impostate. Un set senza secondi li disattiva; puoi riattivarli e scegliere il modello desiderato. **Mostra le ombre abbinate** nasconde o mostra tutte le ombre del livello. Ogni lancetta mantiene il proprio colore; Ripristina colore originale conserva la grafica del modello.

Le ombre sono risorse separate: mantengono colore, alpha, perno e offset ricavati dal campione. Seguono la stessa ora o sorgente, anche in AOD. Non tutti i modelli originali contengono un’ombra: la voce del menu lo indica. Importa PNG/SVG e Usa lancetta disegnata da Studio rimuovono l’abbinamento precedente per quella sola lancetta. Gli asset vengono incorporati nel progetto, comprese le ombre e le scelte per variante.

La scelta del modello ore è un’operazione unica nell’Annulla. **Modifica soltanto questo stile** applica set e ombre solo allo stile attivo. Una scelta comune sostituisce le proprietà corrispondenti anche negli override degli stili.

Il menu contiene ricerca, provenienza/autore, stile, ruolo, indicazione Piccola/AOD e disponibilità dell’ombra. La voce sotto il mouse si evidenzia e mostra la preview; soltanto clic/Invio confermano la voce, e **Usa modello** la applica al progetto. Il riquadro vuoto non carica un’immagine mancante.

## Lancette piccole

Aggiungi Lancetta piccola e posiziona il livello: il centro del livello è il punto di rotazione sul quadrante. **Perno all’estremità della lancetta** è attivo di default e sceglie l’estremità inferiore visibile della grafica orientata alle ore 12, ignorando il padding trasparente. La lunghezza percentuale si riferisce alla parte visibile. È possibile scegliere tutti i modelli, con quelli piccoli elencati per primi, o importare la propria PNG/SVG. Le ombre vengono trasformate insieme alla grafica madre.

Per una posizione di rotazione particolare disattiva il flag e usa Pivot manuale X/Y: −1 ripristina il pivot automatico tradizionale. Modificare direttamente un pivot manuale disattiva il flag all’estremità. La stessa funzione calcola bitmap e perni per anteprima, FPRJ e descrittore nativo. Non sono cronometri azionabili: il livello ruota in base alla sorgente scelta, come secondi, minuti, batteria o altri valori del framework.

## Analisi e verifica

Il vecchio catalogo selezionava soltanto puntatori di primo livello, normali, con rotazione completa 360°/720°. In diversi quadranti questo individuava le ombre e saltava le grafiche madri suddivise in segmenti e gli indicatori nei gruppi. Il nuovo estrattore segue tutti i riferimenti di tema, slot, widget e gruppo, comprende AOD e risorse non collocate. Mantiene le bitmap originali e i pivot nativi quando concordano con XML; evita i UID riutilizzati per risorse differenti. Gli indicatori ad arco con pivot esterno alla bitmap vengono conservati e rasterizzati con padding trasparente quando necessario.

| Corpus personale | Risultato |
| --- | ---: |
| Cartelle esaminate | 39 |
| Puntatori inventariati/coperti | 1.310 / 1.310 |
| Modelli e combinazioni di set distinti | 595 |
| Bitmap grafiche madri distinte | 526 |
| Modelli ore / minuti / secondi / indicatori | 194 / 191 / 114 / 96 |
| Modelli classificati piccoli | 108 |
| Modelli con ombra abbinata | 407 |
| Errori di estrazione | 0 |

L’abbinamento delle ombre usa contenitore, sorgente, centro di rotazione e grafica scura corrispondente. Le lancette scure prive di una madre corrispondente restano modelli selezionabili. Colori e segmenti della stessa forma possono produrre più modelli; 595 non significa 595 sagome differenti. Dati e copertura dettagliata: `library-analysis/hands-0.8.json` e `data/watchface-library.json`. Sono asset dei quadranti forniti dall’utente, per uso personale, con i diritti dei rispettivi autori.

Le nuove regole di `.gitignore` coprono eseguibili versionati, pacchetti personali, dipendenze frontend, cache Python, log e configurazione locale. Il contenuto precedente è conservato come prefisso byte per byte; rapporto `gitignore-preservation-0.8.json`.

Progetto pronto: `projects/S5_Studio_Lancette_0.8.s5faceproj`. ZIP pronto: `S5_Studio_Lancette_0.8_TEMPLATE.zip`. Comprende cinque set grafici, tre sottoquadranti, cinque complicazioni, dieci schermate normal/AOD e 25 istanze native di slot. Le anteprime sono render dei suoi elementi, con dati simulati.

Le verifiche sul PC coprono salvataggi ripetuti/cancellazione, hover senza scelta, set e override manuali, flag ombre, conservazione asset, endpoint di immagini custom e sintetiche, compilazione di sorgenti/range/angoli identici per madre e ombra, AOD, struttura del template e compatibilità dei progetti precedenti. Rapporti: `validation-editor-0.8.json`, `screenshots/executable-0.8.json`, `executable-build-0.8.json`.

Per la prova fisica copia lo ZIP senza estrarlo sul telefono, installalo con la procedura già riuscita e verifica set, lancette piccole e AOD. L’uploader locale può mantenere il problema di nome/preview/capabilities osservato anche sull’originale. La build 0.5 resta quella confermata dall’utente sull’orologio; la 0.8 non è ancora certificata da una prova hardware.
