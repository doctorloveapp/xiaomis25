# S5 Studio 0.7 — anteprime, inquadratura e tastiera

Avvia **S5Studio-0.7.exe** oppure **Avvia_S5_Studio.cmd** dalla cartella del progetto. Salva il lavoro aperto nella versione precedente prima di passare alla nuova. I progetti esistenti restano leggibili. Mantieni accanto all’eseguibile `data/`, `quadrante_funzionante.zip` e `tools/easyface-4.23/Compiler.exe`.

## Anteprima delle lancette

Seleziona un livello **Lancette** o **Lancetta piccola** e apri il menu dei modelli. Il passaggio del mouse su una voce mostra la sua grafica sia nel menu sia nel riquadro sottostante, su uno sfondo a scacchi per distinguere anche lancette nere o bianche. Il margine trasparente viene escluso dalla miniatura per mostrare meglio la grafica. L’hover non modifica il quadrante. Clicca una voce, poi **Usa modello** per applicarla. Le frecce nel menu spostano il focus e mostrano l’anteprima; Invio conferma la voce. Chiudendo il menu si torna all’anteprima della scelta confermata.

Se non hai scelto un modello, il riquadro contiene un testo e nessuna immagine: non compare l’icona di immagine mancante. **Usa modello** rimane disabilitato. Questo riquadro riguarda la galleria; le immagini personalizzate importate restano incorporate nel progetto.

## Immagini oltre il bordo

1. Importa un’immagine e seleziona il suo livello.
2. Aumenta **Larghezza/Altezza**, trascina le maniglie oppure usa **Scala (% del quadrante)**. 100% significa larghezza 480 px; 150% significa 720 px. La scala mantiene le proporzioni e il centro dell’immagine.
3. Premi **Centra immagine** e trascina sul quadrante per rifinire l’inquadratura. Le coordinate X/Y possono essere negative. Per un’immagine 720×720 centrata, X e Y sono −120.
4. Salva e premi **Esporta ZIP**. L’esportazione ritaglia automaticamente il rettangolo 480×480 del quadrante, senza ridimensionare nuovamente la porzione visibile. Le bitmap inviate all’orologio non superano 480 px; un’immagine parzialmente esterna produce una bitmap più piccola, una completamente esterna non produce un widget. La maschera circolare resta visibile nell’editor.

Il limite di lavoro delle immagini è 4096 px per lato; X/Y consentono −4096…4096. Il progetto conserva la risorsa importata e la geometria completa, quindi puoi cambiare inquadratura anche dopo la compilazione. Anteprima e sorgenti EasyFace usano lo stesso ritaglio. Immagini, tinta, opacità, ordine dei livelli e modifiche per stile continuano a funzionare insieme.

## Spostamento con la tastiera

Seleziona un elemento con un clic sul quadrante o sulla sua riga e usa **← ↑ → ↓**: ogni pressione sposta di **1 px**. **Maiusc + freccia** sposta di **10 px**. Puoi tenere premuto un tasto. Funziona per immagini, testi, forme, ora/data, lancette principali e piccole, dati e complicazioni. **Annulla** ripristina lo spostamento.

Quando scrivi in un campo o navighi in un menu aperto, le frecce restano dedicate a quel controllo. Per tornare a spostare il livello, clicca sul quadrante. **Blocca posizione** impedisce anche lo spostamento da tastiera. **Modifica soltanto questo stile** limita lo spostamento allo stile corrente; altrimenti vengono traslate anche le posizioni personalizzate degli altri stili. L’AOD usa le proprie posizioni comuni agli stili.

## Esempio e verifiche

Apri `projects/S5_Studio_Ritaglio_0.7.s5faceproj`: contiene un’immagine 720×720 a X/Y −120, cinque stili, cinque complicazioni e tre lancette piccole. Il relativo ZIP è `S5_Studio_Ritaglio_0.7_TEMPLATE.zip`. Puoi modificarlo e compilarlo normalmente.

Sono passati **58 test**, comprese compilazioni EasyFace reali, ritaglio e salvataggio dell’originale, geometria per stile, tastiera, annulla e blocco. Le prove nel vero QtWebEngine verificano anche hover senza applicazione, riquadro vuoto, scala 150%, trascinamento oltre il bordo e frecce ripetute. L’eseguibile viene verificato separatamente; i rapporti sono `validation-editor-0.7.json` ed `executable-build-0.7.json`.

Il test hardware 0.5 è confermato dall’utente. Le nuove funzioni 0.7 sono verificate sul PC; il nuovo ZIP resta da provare sul S5. Il comportamento della lista locale della mod già osservato sul template originale non è modificato da questo aggiornamento.
