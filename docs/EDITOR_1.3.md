# S5 Studio 1.3

Avvia **S5Studio-1.3.exe** oppure **Avvia_S5_Studio.cmd**. L?eseguibile contiene il runtime personale completo, come la 1.2; i progetti restano in schema 3.

## Velocit? del Crono Pro

Preparazione allo zero e Reset coordinato della lancetta grande dei secondi e delle piccole passano da **320 a 480 ms**. Velocit? nuova = velocit? precedente ? 2/3: un terzo pi? lenta; durata nuova = durata precedente ? 3/2. Il tempo ? comune a tutte le lancette e all?anteprima dell?editor.

Sono conservati il percorso esclusivamente orario, il profilo di accelerazione/decelerazione precedente, il target di 25 fps e la sequenza **Prepara ? Avvia ? Stop ? Reset**. Il conteggio continua a scatti; l?AOD interrompe le transizioni come prima. Il Crono separato e le varianti indipendenti mantengono il comportamento collaudato.

## Anteprime complete degli stili

Le miniature dell?editor vengono composte con tutti i livelli visibili di ciascuno stile, nell?ordine stabilito, con dati di esempio dello scenario Normale. Non dipendono dallo stato AOD o dal cronografo simulato nello stile attivo.

Anche le anteprime native esportate per l?app e il selettore dell?orologio contengono lancette principali/piccole, testo, dati e complicazioni visibili. EasyFace non esegue la scena Lua quando genera un?anteprima: per questo le lancette Pro potevano mancare. `native_graph.preview_factory` rasterizza prima il quadrante completo con `render`, quindi codifica tutte le immagini in un solo batch EasyFace. Le bitmap codificate sostituiscono soltanto le anteprime nel binario; la struttura e i livelli del quadrante operativo restano quelli del progetto. L?AOD usa il proprio rendering con le esclusioni previste.

## Test e documentazione

Il [test reale della 1.2](hardware-test-1.2.json) ? pienamente superato sullo Xiaomi Watch S5, secondo la conferma dell?utente dell?8 ottobre 2026. **25 verifiche mirate superate**: 23 test Crono Pro (durata, rientri orari, Stop/Reset e AOD), una verifica delle miniature con tutti i livelli e una compilazione temporanea che controlla anteprime native, manifest, interattivit? e AOD. Sintassi dell?interfaccia verificata. Si esegue inoltre la verifica statica delle risorse nell?eseguibile. La suite completa e il collaudo grafico dell?editor non vengono ripetuti. Rapporti: [validation-editor-1.3.json](validation-editor-1.3.json) e [executable-build-1.3.json](executable-build-1.3.json).

Nessun nuovo backup di regressione, nessun quadrante dimostrativo consegnato e nessun avvio dell?EXE in ambiente isolato, secondo le preferenze dell?utente. Le istruzioni su livelli, varianti e AOD sono nella [guida 1.2](EDITOR_1.2.md).
