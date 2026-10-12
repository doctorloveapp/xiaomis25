# S5 Studio 2.6 — Simulazione del calendario

**Aggiornamento esportazione Longine:** la 2.6 aggiornata risolve il blocco sui datari fra il disco lunare e le lancette Crono Pro, conservando l'ordine dei livelli. Usa **S5Studio-2.6-aggiornato.exe**. Il nuovo modulo di composizione mantiene i dati dinamici; i sei runtime Lua precedenti restano invariati. [Analisi e verifiche](LONGINE_LIVELLI_2.6.md).

In **Simula l'orologio**, sotto l'ora, trovi **Giorno del mese**, **Mese** e **Anno**. Puoi usare i pulsanti degli input oppure scrivere un numero e confermare con Invio/uscita dal campo. Il giorno va da 1 a 31; il calendario deve essere valido per il mese e anno scelti. Lo scenario Normale propone 15/10/2026.

La stessa data aggiorna contemporaneamente:

- **Dato live → Giorno del mese**, comprese le opzioni di complicazione collegate al giorno;
- l'oggetto **Data**, con giorno e mese;
- una **Lancetta piccola** abbinata a **Giorno del mese**, incluso il modello Datario;
- il **disco lunare giornaliero a 59 posizioni**, secondo riferimento e correzione propri di ogni disco.

Esempio: imposta ottobre 2026 e prova i giorni 1, 15 e 31. Il dato e la lancetta indicano quei giorni; il disco lunare passa fra le corrispondenti posizioni del suo ciclo da 59 giorni. Cambiare mese e anno permette di verificare la progressione oltre la fine del mese, senza aspettare sull'orologio.

Cambiare mese/anno conserva il giorno quando possibile, altrimenti usa l'ultimo giorno del nuovo mese. Da ottobre 31 a febbraio 2026 si passa a febbraio 28; nel 2028 febbraio accetta anche il 29. Un giorno esplicitamente non valido, come febbraio 31, viene rifiutato con un messaggio e la data precedente resta intatta.

**Verifica calendario** nelle proprietà dei dischi usa lo stesso calendario: **Mostra riferimento** riporta tutti i campi alla data di riferimento del disco selezionato, **Data attuale** usa la data del PC. Le date iniziali degli scenari vengono sincronizzate quando cambi scenario; l'anteprima animata conserva il calendario scelto.

La simulazione non viene salvata come dato fisso nel progetto o nello ZIP. Geometrie, pivot, angoli, riferimenti lunari e correzioni rimangono indipendenti dalla data di anteprima. Sul Watch S5 i dati seguono sempre il calendario effettivo del dispositivo. Le sorgenti native a otto fasi e il giorno lunare mantengono i loro campioni precedenti; la simulazione giornaliera da data completa riguarda la sorgente **Fasi lunari · 59 posizioni (giornaliero)**.

Il simulatore Crono Pro esclude ora i dischi lunari dai propri binding, come già faceva il runtime esportato: non può più assegnare loro un valore fisso di riposo durante l'anteprima. Questo intervento sul simulatore non modifica clock, timer o tap del quadrante. La successiva correzione Longine aggiunge soltanto il modulo di composizione descritto sopra.

Verifiche: controlli dell'editor dai sorgenti, confronto delle immagini dei quattro oggetti su più giorni, limiti numerici, date impossibili, mesi corti, anni bisestili, scenari, anteprima animata e calendario del disco. Test mirati anche sull'indipendenza del disco dal Pro e sui calendari esistenti. Eseguibile ispezionato staticamente, senza avviarlo; nessuno ZIP dimostrativo o backup di regressione. [Rapporto](validation-editor-2.6.json).
