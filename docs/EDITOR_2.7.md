# S5 Studio 2.7 — Ore 24 e secondi piccoli fluidi

**Test reale confermato il 2026-10-13:** l'utente riferisce «perfetto adesso funziona ogni cosa» e dichiara **M2530W1 / firmware 3.221.024**. È una conferma del proprietario, senza misurazioni indipendenti di clock, fps o consumo. [Esito hardware](hardware-test-2.7.json). [Documentazione internazionale](README.md).

La 2.7 corregge il collegamento dei puntatori civili inseriti nella scena Lua comune a disco lunare, calendario e Crono Pro. Mantiene la disposizione dei livelli introdotta nella 2.6: non occorre spostare i datari o modificare il progetto Longines.

## Ore 24 (giorno/notte)

Il modulo `studio_scene_data.lua` riceve le notifiche `dataman` in Q8, cioè valori scalati per 256. Nella 2.6 divideva per 256 e poi arrotondava il valore del puntatore all'intero più vicino. Questo poteva trasformare 14,75 in 15, anticipando la posizione della lancetta 24h.

La 2.7 tronca i contatori `timeHour`, `timeMinute` e `timeSecond` prima di renderizzarli, applicando lo stesso criterio di `studio_civil_clock.lua`. Accetta soltanto ore 0–23 e minuti/secondi 0–59; sentinelle e campioni fuori intervallo non spostano la lancetta. L'alias `timeHour24` continua a usare `timeHour` con intervallo 24. Non vengono sottratte ore né applicati cambi di fuso. Angoli, verso, pivot e scala del progetto sono conservati.

Il test riproduce il problema con bit frazionari Q8 e verifica tutti i valori delle tre sorgenti. È un difetto dimostrato del percorso di arrotondamento; il successivo test utente conferma il funzionamento della versione corretta. Non sono stati registrati i campioni grezzi del firmware, quindi la causa interna non è misurata direttamente. Anche l'anteprima tronca i contatori prima di applicare l'eventuale interpolazione dei secondi.

## Movimento Fluido dei secondi piccoli

L'animazione mantiene durata 1.000 ms e interpolazione lineare, avviate dalla notifica del secondo reale. Le modifiche riguardano il suo avvio:

- Oggetto trasparente dedicato da 1 × 1 px, privo di interazione, come nelle transizioni Crono Pro già collaudate sull'S5.
- `repeat_count=1`, al posto di 0, coerente con quel percorso funzionante. Questo non implica che 0 abbia lo stesso significato in ogni versione di LVGL o dei suoi binding.
- Arresto esplicito prima di ogni nuovo avvio, anche se l'animazione precedente è ancora in corso.
- Notifiche duplicate dello stesso secondo non riavviano lo sweep; i valori grafici identici non vengono riscritti.

Il callback interpola fra il secondo corrente e quello successivo, gestendo il passaggio 59 → 0 e aggiornando insieme lancetta e ombra. Non aggiunge un timer di polling e non cambia il clock del cronografo. Pausa, AOD e cancellazione interrompono l'animazione; in AOD la scena normale viene nascosta e resta la configurazione AOD senza secondi. Il frame rate effettivo dipende dal firmware e non è stato misurato.

Il nuovo percorso riusa la configurazione di animazione del motore Pro già verificata sul dispositivo; il successivo test reale 2.7 è confermato dall'utente. Riferimento pubblico per Pointer e notifiche Q8: [m0tral, PointerTest](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand9Pro/PointerTest/app/lua/main.lua). L'esempio è per un altro modello; non costituisce di per sé una prova sul firmware S5.

## Ambito e verifiche

La segnalazione che i secondi piccoli si fermassero all'avvio del cronografo è stata ritirata dall'utente dopo verifica. Non è stata introdotta una modifica al controller del cronografo per quel comportamento. I puntatori civili continuano a essere esclusi dal gruppo Start/Stop/Reset.

I sei moduli Lua preesistenti sono identici a quelli di `S5Studio-2.6.exe`, rinominato dall'utente dalla build aggiornata. Cambia soltanto `studio_scene_data.lua`. Il report di ogni esportazione con questi elementi aggiunge il criterio di decodifica civile e i parametri di avvio dell'animazione sotto `interactive.sceneDynamicData`; il validatore controlla ancora hash del modulo e binding di ogni stile.

Superati **114 test mirati** su dati di scena, secondi civili, sincronizzazione ai riporti, movimento delle lancette civili, Crono Pro e disco lunare. Tre test generici di integrazione sono stati esclusi; è stata eseguita separatamente l'esportazione con EasyFace del progetto reale `Quadranti Compilati/Longines-835194487-20261012-194802/Longines.s5faceproj`.

L'esportazione temporanea ha verificato due stili, flag fluido ON/OFF, AOD, ZIP, binario, manifest interattivo, calibrazione 24h e binding del calendario. Durata **11,09 s**. L'attivazione del flag nel primo stile è stata fatta solo sulla copia in memoria per la verifica. Il progetto originale è rimasto identico, controllato con SHA-256; i file compilati temporanei sono stati rimossi. [Rapporto esportazione](export-validation-2.7.json).

Cataloghi personali ricontrollati e incorporati: **11 set, 629 modelli**, nessuna variazione da integrare. Cataloghi sorgente e `.gitignore` preservati. Nessun backup, ZIP dimostrativo o avvio dell'eseguibile. Il bundle è stato verificato staticamente: **1.251 risorse, 43 moduli Python, entry point e sette moduli Lua** corrispondono ai sorgenti testati; i sei moduli Lua preesistenti risultano identici alla 2.6 aggiornata. [Rapporto test](validation-editor-2.7.json) · [Rapporto eseguibile](executable-build-2.7.json).

## Applicazione delle correzioni

Salva il lavoro, chiudi la versione precedente e avvia **S5Studio-2.7.exe** oppure il launcher. Riapri il progetto, esporta lo ZIP e reinstallalo sull'orologio. La correzione del compilatore non modifica i pacchetti già installati. **Test reale 2.7 superato secondo il riscontro dell'utente del 2026-10-13, su M2530W1 / 3.221.024.** La conferma aggiorna solo i documenti: codice ed eseguibile restano quelli testati.
