# S5 Studio 1.4.1

Avvia **S5Studio-1.4.1.exe** oppure **Avvia_S5_Studio.cmd**. Apri il progetto NASA: l’anteprima mostra subito la dimensione effettiva delle lancette Crono Pro, senza dover modificare un controllo.

La correzione riguarda il rendering dell’anteprima. Usa le stesse viste Pointer già utilizzate nell’esportazione, con dimensioni, pivot, colore e ombre coerenti. Il valore Lunghezza minuti 10% del primo NASA continua a produrre una grafica di 5×46 px: lo ZIP era corretto. Per ingrandirla aumenta Lunghezza e osserva subito il risultato.

Il progetto fornito non è stato modificato. Durante il lavoro l’utente ha sostituito la cartella iniziale con una nuova compilazione, dopo aver regolato i minuti. Il confronto finale verifica le 12 PNG e le due scene Lua del nuovo NASA, byte per byte identiche al suo ZIP. Le anteprime dei due stili coincidono con quelle grafiche; la prova riproduce anche i controlli iniziali del primo NASA. [Analisi](nasa-geometry-analysis-1.4.1.json).

Durante l’ora normale, il flag del gruppo analogico rende fluida solo la grande dei secondi, mai le grandi di ore/minuti. Crono Pro: conteggio a scatti e rientri orari coordinati da 720 ms, sempre fluidi. Secondi e Lua restano esclusi dall’AOD. Questi comportamenti e il runtime non cambiano. Il renderer comune corregge anche le anteprime degli stili e le immagini complete esportate. La preview nella lista della mod resta da confermare sul telefono; [guida 1.4](EDITOR_1.4.md).

30 test mirati superati, comprese compilazioni temporanee e conferma nel binario del movimento fluido limitato ai secondi del gruppo analogico. [Rapporto](validation-editor-1.4.1.json), [contenuto dell’eseguibile](executable-build-1.4.1.json). Nessuna prova isolata dell’EXE, nessun nuovo backup e nessun quadrante dimostrativo consegnato.
