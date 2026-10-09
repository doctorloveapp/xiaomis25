# Editor 1.7.6

## Ruotare e arcuare Dato live

1. Seleziona **Dato live** nel canvas o nel pannello livelli.
2. Apri **Orientamento e arco** e imposta **Rotazione (°)** e **Arco (°)**. Puoi combinarli. La rotazione positiva è oraria; arco positivo adatta la scritta al bordo superiore, arco negativo al bordo inferiore.
3. Regola posizione, larghezza e altezza del campo. L’allineamento sinistro/centrale/destro resta riferito al campo completo, anche quando cambia il numero di cifre.
4. **Raddrizza livello** azzera rotazione e arco. Salva ed esporta normalmente.

I valori sono indipendenti per stile. Il ritaglio resta entro 480 × 480. La validazione rifiuta archi che ripiegherebbero la grafica su sé stessa: in quel caso riduci l’arco o l’altezza del campo. Le lancette continuano a usare la propria rotazione attorno al pivot.

## Nessun colore, ovunque

Tutti i selettori aprono la stessa finestra **Select Color**, con casella **Nessun colore** e spiegazione dell’effetto:

| Controllo | Risultato |
| --- | --- |
| Colore generale delle lancette principali | Nasconde solo il tappo centrale. Colori delle lancette e tacche restano invariati. |
| Colore di una lancetta PNG, immagine, bussola o immagini dinamiche | Mantiene colori e alfa originali, senza ricolorazione. |
| Colore di una lancetta disegnata da Studio | Rende trasparente quella lancetta. |
| Testo, forma, Dato live e colore della complicazione | Rende trasparente quel colore. |
| Sfondo di progetto/stile | Rende trasparente lo sfondo; l’AOD conserva la propria base nera. |
| Accento dello stile | Disattiva l’applicazione dell’accento, mantenendo i colori già presenti. |

Scegliere una tinta disattiva la casella. **Annulla** non modifica nulla. Le scelte supportano cronologia e salvataggio. I vecchi progetti mantengono il tappo centrale visibile per default.

## Implementazione e limiti verificati

Il mesh di `s5studio/transforms.py` è condiviso dall’anteprima e dalle risorse esportate. I datari inglesi usano ancora gli array immagine nativi, con tutte le sette/dodici etichette trasformate e il binding dateWeek/dateMonth originale.

Per un numero ruotato/arcuato, `s5studio/live_data.py` prepara soltanto i caratteri del font nelle posizioni valide per lunghezza e allineamento. `studio_live_data.lua` riceve gli aggiornamenti `dataman.subscribe`, formatta il valore e seleziona le PNG già trasformate. La convenzione numerica Q8 (valore/256) e l’uso delle notifiche derivano dall’API pubblica documentata nell’[esempio PointerTest di m0tral](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand9Pro/PointerTest/app/lua/main.lua). Il codice del renderer è originale. Non esporta il valore simulato come dato fisso e non crea timer, polling o animazioni. Non riscrive le immagini quando il testo non cambia. Mantiene decimali, zeri iniziali, segno, dati assenti e allineamento destro delle cifre singole.

I dati tra lancette Crono/Decimi condividono la scena già esistente; quelli esterni hanno un entry point autonomo. Restano i vincoli precedenti sui widget nativi interposti nel gruppo di lancette Lua. Le etichette calendario native possono stare sopra o sotto quel gruppo.

EasyFace 4.23 alloca record App in AOD ma non esegue `SetupApp` per quella schermata (verificato in `research/DefaultPacker-decompiled.cs`). `complete_aod_apps` completa esclusivamente quei record vuoti con i record App già compilati e risolve gli entry point AOD per nome esatto. Non cambia i descrittori sensore né la compressione delle immagini. La validazione controlla che gli entry point AOD eseguano soltanto il renderer live senza tap/cronografo. I file comuni presenti nelle tabelle non vengono eseguiti da soli. Il runtime sospende il disegno fuori dalla propria modalità e alla pausa; i dati AOD non hanno animazioni. Le lancette dei secondi restano escluse secondo le regole esistenti.

Il limite del backend EasyFace è **256 file App** complessivi: moduli, entry point e PNG Lua. Le PNG identiche vengono deduplicate. Se si supera il limite con molti dati trasformati o stili differenti, l’esportazione si interrompe con un messaggio chiaro prima di produrre un binario con identificatori duplicati. I numeri senza rotazione/arco mantengono il percorso nativo e non consumano file App.

`build-report.json` include `interactive.liveDataTransforms`, con stato dell’iniezione, notifiche dataman, assenza di valori simulati e assenza di timer. Il manifest abilita automaticamente `interactive=true` quando sono necessari gli App. Gli script e le PNG vengono inclusi nel grafo esportato e nel pacchetto, con hash verificati.

## Verifica della release

81 test mirati e 20 controlli DOM del sorgente. Compilazioni EasyFace temporanee con due stili Crono Pro e con AOD senza crono, seguite da ricostruzione del grafo finale/manifest in memoria. Confronto dei pixel dei valori realmente aggiornati in Lua con l’anteprima, incluso cambio cifra, segno, decimali e allineamenti. Nessun quadrante ZIP dimostrativo, backup di regressione o avvio EXE isolato.

I moduli `studio_core.lua` e `studio_core_pro.lua` restano byte per byte quelli collaudati. Il nuovo renderer numerico trasformato è verificato sui sorgenti e nel binario; l’accettazione delle nuove trasformazioni sul firmware S5 richiede il test reale dell’utente.

Controllo cataloghi personali: quattro set, 12 modelli aggiuntivi, 19 PNG; nessun aggiornamento da integrare. La release mantiene 607 modelli complessivi e incorpora il nuovo modulo Lua nel suo runtime autonomo.
