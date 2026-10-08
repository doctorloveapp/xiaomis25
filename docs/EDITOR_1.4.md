# S5 Studio 1.4

Avvia **S5Studio-1.4.exe** oppure **Avvia_S5_Studio.cmd**. Progetti e varianti mantengono lo schema 3.

## Crono Pro

Il tempo comune di preparazione e Reset è **720 ms**, contro 480 ms nella 1.3: la velocità è ridotta di un terzo, la durata aumenta del 50%. L’anteprima usa lo stesso tempo. Restano rientri orari e coordinati, target 25 fps, conteggio a scatti e annullamento AOD. Il completamento simultaneo comporta velocità angolari diverse quando le distanze sono diverse; non è un sistema a velocità angolare costante.

## Anteprime della mod

La 1.4 conserva le immagini complete e allinea i metadati ai 133 temi online disponibili: PNG statiche sotto `_preview/`, mappa `formats` e riferimenti risorse `Image`. I WebP a un solo fotogramma non vengono più indicati come animazioni nel selettore.

Il materiale NASA dimostra che la 1.3 esportava PNG complete, estratte senza modifiche dalla mod. Il problema osservato può dipendere dalla scelta della preview o da un renderer che ignora gli oggetti Lua; resta da verificare sul telefono. [Analisi e limiti](ANALISI_UPLOADER_1.4.md).

Apri il progetto, genera un nuovo ZIP, importalo e verifica le preview dei due stili e i rientri Pro. La 1.3 ha superato il funzionamento del crono, ma non la preview della mod. La 1.4 richiede questa conferma reale.

**25 verifiche mirate superate**, incluse durata, AOD, metadati preview e compilazione temporanea. Verifiche e contenuto dell’EXE: [validation-editor-1.4.json](validation-editor-1.4.json), [executable-build-1.4.json](executable-build-1.4.json). Nessun nuovo backup di regressione, nessun avvio dell’EXE in ambiente isolato e nessun quadrante dimostrativo consegnato.
