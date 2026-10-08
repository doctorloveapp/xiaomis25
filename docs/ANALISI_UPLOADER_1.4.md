# Analisi del pacchetto locale NASA e del catalogo

Fonte: `Documenti/L00000000001/designer.zip` e relativa cartella estratta. Il build-report identifica la versione **1.3**, durata Pro 480 ms; il nome del progetto conserva «NASA S5 Crono Pro 1.2», ma non identifica la versione del compilatore.

## Risultati osservati

- Nell’archivio ci sono 300 file e relative directory. Tutti sono presenti nella cartella estratta.
- Le PNG complete di NASA, comprese `resources/studio/Studio_02000002.png` e `preview/preview.png`, mostrano lancette grandi e piccole. Sono state ispezionate visivamente.
- Tra archivio e cartella cambia solo `resource.bin`: i 12 byte diversi sono nell’ID. Il contenuto grafico, Lua e le anteprime binarie non vengono modificati. L’ID diventa `L00000000001`.
- Nella cartella restano **5.752 file aggiuntivi** rispetto all’archivio. La loro provenienza e l’eventuale uso come cache non sono dimostrati; non sono stati cancellati o modificati.
- Sono state esaminate tutte le 39 cartelle del catalogo. In 33 è disponibile `editor.config.json`: i suoi **133 temi** referenziano `_preview/`. Sei cartelle non hanno una configurazione disponibile.
- Le 33 configurazioni non contengono oggetti `App`, neppure nei gruppi. NASA ha un oggetto `App` Lua per ciascuno stile normale. Questo è compatibile con l’ipotesi che un renderer della mod disegni soltanto i livelli nativi, ma non lo prova.
- I WebP NASA indicati come animati contengono un solo fotogramma. La 1.4 usa il riferimento PNG statico.

## Correzione 1.4 e limiti

Le anteprime complete restano rasterizzate e codificate nativamente. I loro percorsi diventano `resources/_preview/Style_N_NormalPreview.png` e `Style_N_AODPreview.png`; `Theme.preview` resta associato alla risorsa binaria corretta e `editor.config.json` usa il percorso relativo `_preview/`. Si compilano la mappa `formats` e i riferimenti `Image.resources.pointer0`. La correzione riguarda i metadati, senza aggiungere immagini statiche al layout operativo o sostituire le lancette Lua.

La mod non è stata modificata. Il database dei quadranti locali e il codice dell’uploader non sono nel materiale condiviso: non si può stabilire quale immagine scelga l’app, né promettere che il cambio di percorso risolva un renderer che ignora Lua. Il prossimo test deve distinguere le preview nel selettore stili da quella del catalogo locale. Nome generico e test capabilities non derivano da immagini mancanti nel nostro archivio.

Dati e inventari: [local-uploader-analysis-1.4.json](local-uploader-analysis-1.4.json), [local-uploader-files-1.4.json](local-uploader-files-1.4.json). Nessuna cartella condivisa, capacità o firma del template è stata alterata.
