# S5 Studio 1.8 — Fluidità indipendente delle lancette

## Uso

Seleziona **Lancette**, espandi **Lancetta ore**, **Lancetta minuti** o **Lancetta secondi** e attiva **Movimento Fluido** nella scheda desiderata. I tre flag sono indipendenti. La scelta dei secondi della versione precedente rimane valida; ore/minuti sono disattivati finché non li scegli. Salvataggio, Annulla/Ripeti e stili indipendenti conservano le impostazioni.

I campi di lunghezza, spessore, colore e pivot mantengono la geometria già usata. La modifica di Minuti o Secondi non riapre più Ore: vengono restaurati tutti gli stati aperti/chiusi dello stesso livello, non soltanto le schede aperte. Cambiando livello si applica l’apertura iniziale del nuovo oggetto.

## Fattibilità e scelta energetica

Il compilatore locale EasyFace 4.23 emette il periodo `_smooth` soltanto per `timeSecond`; per ore e minuti mantiene 1.000 ms. Il solo aumento di `pointerFps` non dimostra che il firmware interpolerà il valore intero di ore/minuti. Perciò la nuova opzione usa le API `dataman` e `widgets.Pointer` già usate dal Crono Pro collaudato, calcolando esplicitamente le posizioni intermedie dai secondi dell’ora reale.

- **Minuti:** `(minuti × 60 + secondi)`, dominio `0…3599`, rotazione 360°. Incremento 0,1° per secondo.
- **Ore:** `((ore % 12) × 3600 + minuti × 60 + secondi)`, dominio `0…43199`, rotazione 360°. Incremento circa 0,0083° per secondo.
- **Secondi:** percorso nativo a 25 fps esistente; nel Crono Pro resta il relativo controller integrato.

Le nuove ore/minuti non creano Timer o Anim: seguono le notifiche dei secondi e scrivono solo quando il valore cambia. Per questi movimenti l’incremento è già molto piccolo; un ciclo aggiuntivo a 25 fps aumenterebbe il lavoro senza superare la risoluzione angolare del Pointer. Non è promessa un’animazione fisicamente continua a 25 fps per ore/minuti. L’anteprima adotta la stessa precisione di un secondo.

Il carico aggiuntivo atteso è ridotto, ma consumo, memoria e assenza di scatti sullo specifico firmware non possono essere certificati dai soli test su PC. I flag sono opzionali e disattivabili separatamente. Il primo test consigliato è attivare Minuti, poi Ore, mantenendo il comportamento dei secondi abituale.

## Esportazione, Pro e AOD

Nell’orologio normale, ogni lancetta ore/minuti attivata diventa una piccola App Lua indipendente, inserita nella sua posizione originale tra le altre lancette. `studio_civil_hand.lua` usa lo stesso valore per grafica e ombra, conservando PNG, pivot, dimensioni, spostamenti e ordine. Le App non condividono il tempo del cronografo e non aggiungono gestori di tap. Le lancette non attivate restano native.

In **Crono Pro**, i flag sono riportati alle singole viste; vengono aggiunti i secondi alle sole posizioni civili di ore/minuti scelte. Non cambiano timer, macchina a stati, conteggio, direzione, durata o animazioni di rientro. I puntatori Crono continuano a contare a scatti, indipendentemente dai flag.

In **AOD** i flag non hanno effetto. Ore/minuti restano nativi, senza i nuovi entry point Lua; i secondi vengono sempre esclusi. Il runtime civile sospende le scritture su AOD/OFF, pausa e cancellazione del root, e si riallinea ai dati ricevuti alla ripresa. I file Lua presenti nella tabella comune del compilatore non equivalgono a entry point attivi in AOD: il validator controlla i layout eseguiti.

Il manifest dichiara le App effettive e `build-report.json` documenta `interactive.civilHandMotion`, entry point per stile, flag, origine dei dati, assenza di timer e controllo AOD. Il validator controlla presenza del modulo, entry point previsti, hash dei file e coerenza binario/manifest. L’architettura condivisa del Crono rimane distinta dalle App civili indipendenti.

## Esito hardware successivo

Il test reale dell'utente ha confermato il movimento progressivo dei minuti, ma ha individuato uno scatto al passaggio 59→0 dovuto alle notifiche H/M/S separate. Corretto nella [1.8.1](EDITOR_1.8.1.md); non è ancora dichiarato un test hardware della correzione.

## Verifiche

**70 test mirati e 11 controlli dell’editor dai sorgenti superati.** Compresa compilazione binaria temporanea con tre stili, fluidità diversa per ogni lancetta, Crono classico/Pro, ombre, geometria delle PNG originali e AOD nativo. Esecuzione del codice Lua con tick reali simulati, Stop/Reset e ciclo schermo; i test delle nuove App falliscono esplicitamente se tentano di creare un Timer. Nessun ZIP dimostrativo, backup o avvio dell’EXE in ambiente isolato.

Catalogo personale controllato: sei set, 17 modelli aggiuntivi, 29 PNG, 612 modelli complessivi. Nessun nuovo set o aggiornamento. Sorgenti del catalogo e `.gitignore` intatti.

Fonti di contesto: [EasyFace](https://github.com/m0tral/EasyFace), [release 4.23 con supporto S5](https://github.com/m0tral/EasyFace/releases/tag/v4.23), [esempi Lua m0tral](https://github.com/m0tral/MiWatchLuaWatchfaces). La logica specifica della 1.8 è verificata sul compilatore locale e nei test; queste fonti non certificano consumi o compatibilità del nuovo comportamento sul dispositivo.

Rapporti: [test](validation-editor-1.8.json), [editor](hand-motion-editor-1.8.json), [EXE](executable-build-1.8.json).
