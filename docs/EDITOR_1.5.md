# S5 Studio 1.5

Avvia **S5Studio-1.5.exe** o **Avvia_S5_Studio.cmd**. L’eseguibile completo include il catalogo personale e il compilatore, come la versione precedente.

1. Seleziona un livello Testo, Immagine o Forma.
2. In **Orientamento e arco**, imposta **Rotazione (°)** per girarlo attorno al centro; i valori positivi ruotano in senso orario.
3. Imposta **Arco (°)**: positivo per il bordo superiore, negativo per quello inferiore, 0 per rimanere diritto. Sposta e dimensiona il livello osservando l’anteprima. Un arco troppo stretto rispetto all’altezza viene rifiutato per evitare ripiegamenti.
4. Usa **Raddrizza livello** per azzerare la trasformazione.
5. Per una forma, scegli **Rettangolare** o **Circolare**. Il cerchio nasce centrato, con larghezza e altezza uguali; il ridimensionamento ne conserva le proporzioni.
6. Salva ed esporta lo ZIP come prima. Le parti oltre il bordo vengono ritagliate; le PNG inviate all’orologio restano entro 480×480 px.

Le trasformazioni sono locali allo stile attivo; funzionano anche sui livelli statici AOD e fra i livelli di una scena Crono Pro. Anteprime del canvas, stili e compilazione condividono il renderer. Le immagini a scelta dinamica mantengono il sensore, trasformando tutti i fotogrammi con le stesse coordinate. Lancette, bussola, numeri live, Ora/Data e complicazioni numeriche restano nativi e non espongono i controlli di orientamento/arco.

I nomi cinesi delle lancette vengono mostrati in inglese: per esempio **户外探险家 → Outdoor Explorer**, **黑豹 → Black Panther**, **样式2 → Style 2**. Autori: **小米 → Xiaomi**, **三尺设计 → San Chi Design**. Le traduzioni riguardano le etichette: grafica, pivot e abbinamenti restano gli stessi.

Il flag Movimento Fluido del gruppo analogico continua a riguardare la grande dei secondi durante l’ora normale. Il Crono Pro mantiene conteggio a scatti e rientri orari coordinati da 720 ms. Nessuna modifica ai due runtime Lua.

Verifica: 22 test mirati superati, una compilazione temporanea con due stili/AOD, sensori nativi e Crono Pro, confronto PNG/anteprima e controllo visivo degli archi. [Rapporto](validation-editor-1.5.json), [traduzioni](catalog-english-1.5.json), [bundle](executable-build-1.5.json). Nessun nuovo backup, nessuna prova isolata dell’EXE e nessun quadrante dimostrativo consegnato. Il test dispositivo della 1.4.1 è confermato dall’utente; le trasformazioni 1.5 devono ancora essere provate sul S5.
