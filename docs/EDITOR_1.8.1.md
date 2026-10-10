# S5 Studio 1.8.1 — Campioni civili coerenti

## Causa e correzione

Il test reale della 1.8 ha confermato l'avanzamento progressivo dei minuti, ma ha rilevato un salto in avanti e subito indietro al cambio minuto. Le sorgenti `timeHour`, `timeMinute` e `timeSecond` notificano separatamente. Il codice aggiornava il Pointer dopo ciascuna notifica: alle 12:04:59, ricevendo prima `minute=5`, emetteva temporaneamente `5×60+59=359`, quasi il minuto 6, prima di ricevere `second=0` e correggere a 300, minuto 5.

`studio_civil_clock.lua` raccoglie i valori Q8 e pubblica una copia del campione completo. Ore/minuti ricevuti senza un secondo nuovo rimangono in attesa. Al passaggio 59→0, anche se i secondi arrivano prima, attende il minuto aggiornato; al passaggio 59:59→00:00 attende anche l'ora aggiornata. La stessa barriera copre un singolo secondo perso. Un cambiamento non adiacente dell'ora civile può riallineare il campione, senza forzare artificialmente l'orario sempre in avanti. Valori negativi, fuori dominio, non numerici o non finiti vengono scartati.

Il modulo è usato da `studio_civil_hand.lua` e dalla sola acquisizione dell'ora civile di `studio_core_pro.lua`. I timer esistenti del Pro leggono l'ultimo campione pubblicato, anche se vengono eseguiti tra due notifiche. Grafica e ombra ricevono lo stesso valore. Non vengono aggiunti Timer, Anim, tap o richieste di dati. Conteggio del cronografo, rientri orari coordinati da 720 ms e configurazione AOD mantengono il percorso precedente.

Gli esportatori includono il nuovo modulo nelle App civili e nelle scene Pro. Il validator rifiuta un pacchetto che richiede il modulo senza includerlo e registra `interactive.civilClock` nel `build-report.json`. I pacchetti storici che non lo richiedono conservano il proprio rapporto verificabile.

## Verifiche e uso

**86 test mirati superati**, inclusi 16 nuovi test che esercitano 72 sequenze: tutti i sei ordini H/M/S per cambio minuto, cambio ora, mezzanotte e un secondo saltato, sia nelle App civili ore/minuti sia nel Pro. Il controllo registra ogni scrittura ai Pointer, comprese quelle intermedie; non si limita alla posizione finale. Verificati inoltre campioni immutabili, notifiche ripetute, secondi vecchi accodati dopo il minuto/ora nuovi, correzione dell'orario, input non validi, AOD/ripresa, geometria, ombre, Crono e una compilazione binaria temporanea a tre stili. Due test d'integrazione che producono pacchetti non sono stati eseguiti.

Controllati i set personali: sei set, 17 modelli aggiuntivi, 29 PNG, 612 modelli complessivi; nessun aggiornamento. Nessun backup, ZIP dimostrativo o avvio dell'EXE in ambiente isolato. L'eseguibile viene controllato staticamente. **Test reale della correzione superato sull'S5**, confermato dall'utente il 10 ottobre 2026: «ho fatto test reale e ti confermo che adesso funziona alla perfezione». [Evidenza riferita dall'utente](hardware-test-1.8.1.json).

Apri **S5Studio-1.8.1.exe**, carica il progetto esistente, riesporta lo ZIP e reinstallalo. Le impostazioni salvate non richiedono modifiche. Osserva il passaggio 59→0 e, quando disponibile, il cambio dell'ora.

Rapporti: [test](validation-editor-1.8.1.json), [bundle](executable-build-1.8.1.json), [catalogo](hand-set-integration-1.8.1.json).
