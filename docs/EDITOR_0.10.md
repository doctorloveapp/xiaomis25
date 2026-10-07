# S5 Studio 0.10

Avvia `S5Studio-0.10.exe` o `Avvia_S5_Studio.cmd`. L’eseguibile personale incorpora anche il framework Lua e funziona senza cartelle accanto, su Windows a 64 bit con .NET Framework 4.7.2 o successivo. Il progetto NASA e gli eseguibili precedenti restano conservati.

## Movimento fluido e AOD

Seleziona un livello Lancette e attiva **Movimento Fluido**: i secondi usano 25 fps. Il compilatore supporta realmente `_smooth[40]`, che scrive 40 ms nel parametro del puntatore. Il manifest espone `pointerFps=25` e `parameter=40`, coerenti con il binario: il comportamento non dipende soltanto da un attributo XML. Ombre e grafica principale condividono la frequenza. Per una lancetta piccola vale sulle sorgenti Secondi completi e Secondi Crono; sui decimi abilita i valori intermedi. Non cambia l’aggiornamento degli altri sensori.

AOD: lancetta secondi e ombra analogiche non vengono generate; sono escluse anche le lancette piccole dei secondi e delle loro cifre, tutti i decimi e tutte le lancette Lua Crono. Questo vale anche se un vecchio progetto le conteneva o se una variante ne abilita la visibilità. L’editor le identifica come **Esclusa AOD**. Il validator controlla tutti i temi e rifiuta secondi o app Lua nell’AOD.

## Lancette piccole: decimi e cronografo

Nel menu **Dato che guida la lancetta** trovi:

| Voce | Intervallo preimpostato | Rotazione | Significato |
| --- | ---: | ---: | --- |
| Decimi di secondo | 10 | 360° | Un giro ogni secondo, dieci posizioni; fluido se attivi il flag |
| Ore Crono | 12 | 360° | Ore trascorse, giro ogni 12 ore |
| Minuti Crono | 60 | 360° | Minuti trascorsi, giro ogni ora |
| Secondi Crono | 60 | 360° | Secondi trascorsi, giro ogni minuto |

Non sono codici di sensori inventati: usano script Lua incorporati dal compilatore S5. Le normali sorgenti restano native. I decimi seguono il clock continuo, indipendentemente dal cronografo. Colori, pivot, dimensioni, ombre, posizioni e stili delle lancette rimangono configurabili.

Tocca l’area rettangolare di un sottoquadrante Crono sull’orologio. Azzera → primo tap avvia; in movimento → secondo tap ferma tutte le lancette Crono; fermo dopo lo stop → terzo tap azzera tutte; il tap successivo riparte. I decimi continui non vengono fermati da questi tap. Evita zone Crono sovrapposte a complicazioni modificabili. Nell’editor il pulsante **Avvia/Ferma/Azzera Crono** simula la stessa sequenza; **Anteprima animata** mostra secondi e decimi in movimento.

## Fattibilità e limiti da verificare sul S5

Nel corpus sono presenti widget `jumpApp="chronograph"` (fra gli altri 562700014, 562700015 e 562700103). Questi aprono l’app cronometro dell’orologio. Non forniscono tempi trascorsi né eventi di Start/Stop/Reset alle lancette del quadrante. La scansione dei 38 manifest in `quadranti/` non ha trovato script Lua; sono stati verificati anche i widget del pacchetto ORIGINALE_quadrante.

Il [repository del maintainer m0tral](https://github.com/m0tral/MiWatchLuaWatchfaces) dichiara supporto Lua per Mi Watch S5. Gli [esempi analogici animati](https://github.com/m0tral/MiWatchLuaWatchfaces/tree/master/MiBand8Pro/AnalogTimeAnimated) mostrano Shape 34, animazioni e eventi di pressione; l’[esempio Pointer/Compass](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand9Pro/Compass/app/lua/main.lua) mostra Pointer, timer e pause/resume. Il compiler 4.23 fissato nel progetto ha compilato effettivamente Shape 34 per MiWatchS5. Il codice Studio è originale e la sua macchina a stati è eseguita nei test tramite Lua 5.4, con adattatori LVGL simulati.

**Questo dimostra packaging e logica sul PC, non ancora l’esecuzione del nuovo framework sul firmware dell’utente.** Rimangono da verificare clock monotono, API Pointer/LVGL, VM condivisa fra entry point, ordinamento e proprietà dei root Lua, tap, ritorno dall’AOD e consumo. Se il firmware separa le VM, i quadranti Crono non condividono lo stato: occorrerà adattare il backend a un unico root/script. Non si dichiara certificata la firma Xiaomi né l’accettazione capabilities.

Il tempo trascorso usa `lvgl.tick_get` se esposto, altrimenti legge `/proc/uptime` (clock di uptime NuttX con centesimi, documentato nel [sorgente NuttX](https://github.com/apache/nuttx/blob/master/fs/procfs/fs_procfsuptime.c)). Non usa `os.clock` né il numero di callback: ritardi dei timer non falsano il conteggio. L’esposizione di queste API/file sul firmware S5 è da provare. Senza clock il cronografo resta azzerato. Durante AOD/schermo spento i root sono nascosti e il timer sospeso; al ritorno il conteggio in movimento comprende il tempo trascorso. Eliminare l’ultima vista resetta lo stato; cambio quadrante o nuova VM non conserva il conteggio. Non è un cronometro sincronizzato all’app di sistema.

## Selezione multipla

Ctrl + clic (o Cmd + clic) sul canvas o nel pannello livelli aggiunge/rimuove un livello. Un clic su un livello già selezionato mantiene il gruppo per trascinarlo. Frecce = 1 px; Maiusc + frecce = 10 px. I sei pulsanti allineano il riquadro complessivo del gruppo al quadrante, mantenendo le posizioni relative. Uno spostamento è una sola operazione Annulla/Ripristina. Il limite è applicato a tutto il gruppo, non a ogni elemento separatamente; i livelli immagine conservano i margini estesi. Con un livello bloccato devi prima sbloccare il gruppo. Le proprietà individuali nell’inspector restano quelle dell’ultimo livello selezionato. Gli spostamenti rispettano **Modifica soltanto questo stile**; quelli comuni traducono anche le posizioni già personalizzate nelle altre varianti.

## Validazione di ogni esportazione

Ogni ZIP include `build-report.json`, anche se non contiene componenti Lua. Il rapporto indica `interactive.requested`, `interactive.injected`, `interactive.status`, hash degli script/bitmap effettivamente estratti dalle risorse app del binario, numero di entry point nei temi, flag manifest e esclusione AOD; `secondsMotion.pointers` elenca le frequenze reali per UID/tema. Il rapporto esterno nella cartella di esportazione contiene anche compilatore, template, geometrie e verifiche complete.

Tutti i `.lua` e PNG necessari sono presenti in `app/lua/` e nel binario T5, byte per byte. L’identità fra manifest, UID, layout, binario, file e report è controllata prima della pubblicazione. Script mancanti/alterati, flag interattivo incoerente, report alterato e secondi/Lua in AOD fanno fallire l’esportazione. `interactive=true`/`advanced=true` si attivano quando sono presenti componenti Lua; le capabilities del template restano intatte.

Verifica finale 0.10: **85 test passati**, **81 controlli UI nell’EXE**, **707 risorse incorporate verificate** e compilazione isolata senza tool esterni; il binario Lua con due stili e AOD coincide con quello prodotto dai sorgenti. Rapporti: [validation-editor-0.10.json](validation-editor-0.10.json), [executable-build-0.10.json](executable-build-0.10.json).

Le fixture di compilazione sono temporanee. Per questa versione viene consegnato l’eseguibile, senza un nuovo quadrante dimostrativo.
