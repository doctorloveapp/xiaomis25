# S5 Studio 2.1

Avvio: `S5Studio-2.1.exe` o `Avvia_S5_Studio.cmd`. Eseguibile personale autonomo per Windows 64 bit; il compilatore richiede .NET Framework 4.7.2 o successivo.

## Set piccoli: Decimi

In **Set lancette → Lancette piccole** trovi sei categorie: Ore, Minuti, Secondi, Decimi, Centesimi e Millesimi. La nuova **Lancetta piccola · Decimi** supporta PNG, pivot manuale, ombra importata o generata, modifica del set, catalogo e integrazione nella distribuzione. Basta una PNG per salvare un set piccolo; i set principali mantengono Ore/Minuti/Secondi.

Quando applichi il modello Decimi con **Usa modello**, un dato già impostato su Decimi continui o Decimi crono conserva sorgente, scala e arco. Per una nuova associazione viene proposto Decimi continui, valore iniziale 0, intervallo 10 e giro completo 360° (la geometria dell'arco resta se attiva). Per misurare il cronografo scegli Decimi crono nella scheda della lancetta e attiva Crono Pro nel gruppo grande. Centesimi/Millesimi mantengono il comportamento POST della 2.0.

## Cartelle di lavoro

Le finestre native ricordano l'ultima cartella scelta per queste categorie:

| Operazione | Categoria condivisa |
| --- | --- |
| Apri progetto | Progetti in lettura |
| Salva progetto, Salva con nome | Progetti in scrittura |
| Importa immagine, sfondo stile | Immagini |
| Importa lancetta singola (grande o piccola) | Grafiche lancette |
| Importa bussola | Grafiche bussole |
| Importa font | Font |
| PNG del set, qualunque ruolo | Grafiche set |
| PNG ombra del set, qualunque ruolo | Ombre set |
| Seleziona compilatore | Compilatore |
| Esporta ZIP | Cartella compilazioni |
| Salva anteprima | Anteprime PNG |

Persistenza: `%LOCALAPPDATA%/S5Studio/dialog-paths.json` nella distribuzione, `data/dialog-paths.json` da sorgente. La preferenza si aggiorna quando confermi la selezione nella finestra; Annulla la lascia intatta. Un percorso non più disponibile torna al predefinito o al suo primo antenato esistente. Nei salvataggi viene conservato il nome suggerito del file, cambiando la cartella di partenza. Salva progetto continua a chiedere il nome ogni volta. Le preferenze sono locali al PC e separate dai progetti.

## Lettura del cronografo nell'anteprima

Al termine dello Stop compare il tempo a destra di **Crono fermo**. Esempio: `01:02:03 · Decimi 4 · Centesimi 48 · Millesimi 488` corrisponde a un'ora, due minuti e 3,488 secondi. Decimi e centesimi vengono troncati dalla stessa frazione, non arrotondati. Le ore mostrano il totale trascorso, anche oltre 12; una lancetta con scala da 12 ore ripete il giro.

`StudioBridge` invia `chronoElapsedMs` sia nello stato completo sia nei fotogrammi dell'anteprima. Il valore proviene da `chrono_elapsed`/`ProPreview.elapsed`, congelato sullo stesso Stop usato dai puntatori. Durante la breve fase `reading` dei POST il tempo non avanza; la lettura appare quando le lancette raggiungono la posizione. Ulteriori fotogrammi dell'ora civile non modificano il tempo fermato; le risposte obsolete vengono scartate con `stateSequence`. Il Reset nasconde la lettura.

Non vengono aggiunti timer o file Lua al quadrante. La precisione hardware resta quella documentata per la 2.0: mostrare millesimi non garantisce risoluzione fisica di 1 ms sul firmware.

## Distribuzione e verifiche

Controllati e integrati i set personali prima delle modifiche; trovato **Bulova_lancette_piccole**. Catalogo: 9 set personali, 28 modelli aggiuntivi e 623 modelli totali. Cataloghi sorgente e `.gitignore` conservati.

Superati 56 test mirati e 12 controlli dell'editor. Creato `S5Studio-2.1.exe` e verificati staticamente 760 risorse, 22 moduli Python e i file Lua contro i sorgenti. [Rapporto](validation-editor-2.1.json), [editor](editor-2.1.json), [EXE](executable-build-2.1.json), [integrazione set](hand-set-integration-2.1.json). Nessun backup di regressione, quadrante ZIP dimostrativo o avvio dell'eseguibile. Il test sul dispositivo delle novità 2.1 resta da effettuare; il runtime del crono non è stato modificato.
