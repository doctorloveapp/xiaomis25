# S5 Studio 0.6 — uso dell’editor

Avvia `S5Studio-0.6.exe` dalla cartella principale. Salva e chiudi l’app precedente prima di usare la nuova. `Avvia_S5_Studio.cmd` preferisce automaticamente la 0.6.

1. Apri il tuo progetto o `projects/S5_Studio_Crono_0.6.s5faceproj`.
2. Seleziona un livello dalla lista a destra. **×** elimina; **Canc** funziona quando non stai scrivendo in un campo. **Annulla** ripristina.
3. Trascina la riga sopra/sotto un’altra. La linea indica dove verrà inserita. I livelli in cima alla lista coprono quelli sottostanti. L’ordine è comune agli stili, separato per Quadrante/AOD.
4. Per un’immagine, trascina le maniglie agli angoli oppure inserisci larghezza/altezza. **Riempi quadrante** riempie 480 × 480 ritagliando; **Adatta al bordo** contiene tutta l’immagine nel quadrante. Disattiva Mantieni proporzioni per deformarla liberamente.
5. Imposta **Opacità (%)** col numero o il cursore: 0 invisibile, 100 opaco, ogni numero intermedio è valido. Se scegli un colore sull’immagine si attiva la tinta; disattiva Applica il colore come tinta per recuperare la tavolozza originale.
6. Sul livello Lancette apri Ore, Minuti o Secondi e scegli il relativo colore. Le immagini importate conservano alfa e ombreggiatura; Ripristina colore originale elimina la tinta. Per i componenti disegnati da Studio il colore generale rimane quello di tacche/centro e delle lancette che non hanno un colore specifico.
7. **Complicazione** aggiunge un livello con solo il valore. Trascinalo sul quadrante e riordinalo dalla lista. **Scegli le informazioni disponibili** apre la scheda con le sorgenti selezionabili sull’orologio. Etichetta, unità, cornice e icona meteo sono opzionali. Se aggiungi un’etichetta aumenta l’altezza almeno a 64 px.
8. **Lancetta piccola** crea una singola lancetta per un sottoquadrante. Il perno coincide con il centro del livello. Usa un modello della galleria, importa PNG/SVG o la grafica di Studio. Lunghezza e dimensioni riducono automaticamente la bitmap importata. Duplica per creare più lancette.
9. Scegli il dato che guida la lancetta: Secondi → intervallo 60, rotazione 360°; Ore → intervallo 24, rotazione 720°; Batteria → intervallo 100; Bussola → intervallo 360. Puoi regolare valore iniziale e angoli per indicatori a settore. Sono lancette guidate dai dati dell’orologio, senza comandi start/stop di un cronometro separato.
10. Salva, poi **Esporta ZIP**. Copia il file `*_TEMPLATE.zip` sul telefono senza estrarlo e installalo seguendo il percorso già collaudato.

I menu confermano una scelta solo con clic o Invio. Il passaggio del mouse non modifica né evidenzia un valore diverso come selezionato; le frecce spostano il focus, Invio conferma. I menu lunghi hanno una ricerca.

Il precedente test 0.5 è registrato come superato in `data/hardware-tests/analogico-05-superato.json`. L’esempio 0.6 contiene cinque stili, cinque complicazioni solo valore, tre lancette piccole e uno sfondo immagine con opacità regolabile. Il suo nuovo comportamento grafico richiede la prova sul S5; la preview esportata mostra il progetto reale con dati simulati.
