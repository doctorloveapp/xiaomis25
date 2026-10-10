# S5 Studio 1.7.7 — Anteprima dei secondi civili

## Come verificare una lancetta piccola dei secondi

1. Scegli **Secondi completi (0–59)** come sorgente.
2. Per una scala ordinaria usa **Valore iniziale 0**, **Intervallo valori 60**, **Angolo iniziale 0°**, **Rotazione totale 360°**.
3. Nella barra superiore imposta **Secondi = 0** per verificare l’allineamento dello zero. La PNG deve essere rivolta verso le ore 12 e avere il proprio pivot corretto.
4. Attiva **Simula movimento**. Con Movimento Fluido disattivato, la lancetta avanza di uno scatto ogni secondo e torna a zero dopo 59.

Il campo **Valore iniziale** rappresenta il minimo della scala del sensore, non l’ora da cui partire. Lo scenario Normale indica inizialmente **30 secondi**: è corretto che la lancetta punti verso il basso. Dopo quattro secondi di simulazione indica 34. Non è un errore del pivot o un offset di 34 secondi. L’utente ha confermato questa spiegazione e non aveva ancora installato questo progetto sul S5.

## Modifiche tecniche

Il renderer aggiungeva `__secondFraction` a `timeSecond` solo quando `smooth_seconds` era attivo. Ora aggiunge la parte intera del tempo trascorso anche quando il flag è disattivato, conservando il conteggio a scatti. Gli alias `second` e `timeSecond` sono equivalenti. La lancetta civile non usa il tempo trascorso del cronografo.

L’azione `time`, quando modifica i secondi, e l’azione `scenario` impostano una nuova origine monotona e azzerano la fase della simulazione. Una richiesta di Secondi = 0 durante il movimento mostra quindi subito zero, anche se la simulazione era in corso da tempo.

La compilazione nativa conserva sorgente **1811 (`timeSecond`)**, intervallo **60 in Q8**, periodo **1.000 ms** e pivot condivisi con l’anteprima. Il test binario controlla anche lancetta e ombra esterne al gruppo Lua Crono Pro, due stili e AOD senza secondi. Nessuna modifica ai controller Lua o alla logica delle lancette esportate; i progetti esistenti conservano tutti i propri valori.

## Catalogo e verifiche

Integrati **Omega moon** e **Omega moon piccole**, senza scrivere nei cataloghi sorgente. Totale: **6 set personali, 17 modelli aggiuntivi, 29 PNG, 612 modelli complessivi**.

Superati **17 test mirati** (`test_civil_seconds`, `test_bundled_hand_sets`) e **15 controlli dell’editor dai sorgenti**. Nessun ZIP dimostrativo, backup di regressione o avvio dell’eseguibile in ambiente isolato. L’EXE viene verificato staticamente. Rapporti: [test](validation-editor-1.7.7.json), [editor](civil-seconds-editor-1.7.7.json), [set](hand-set-integration-1.7.7.json), [EXE](executable-build-1.7.7.json).
