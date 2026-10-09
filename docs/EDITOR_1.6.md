# S5 Studio 1.6 — Catalogo personale di set lancette

1. Avvia `S5Studio-1.6.exe` e apri **Set lancette** nella barra laterale.
2. Inserisci un nome e scegli il tipo: **Lancette principali** richiede Ore, Minuti e Secondi; **Lancette piccole** permette anche una sola PNG.
3. Importa le PNG. Usa immagini statiche da 1 a 480 pixel per lato, preferibilmente con trasparenza. La grafica deve puntare verso l’alto per rappresentare lo zero; il pivot iniziale suggerito è l’estremità inferiore visibile. Clicca sul vero perno oppure inserisci Pivot X/Y. Le coordinate si riferiscono ai pixel originali della PNG.
4. Facoltativamente importa un’ombra per ciascuna grafica. Imposta il suo pivot e lo spostamento rispetto alla lancetta. Il flag delle ombre del livello resta disponibile.
5. Premi **Salva set nel catalogo**. Il nome appare subito nei menu e rimane disponibile dopo il riavvio, anche nei nuovi progetti.
6. Torna su **Quadrante**, seleziona un livello Lancette e scegli il set nel menu Ore. Premi **Usa modello**: vengono applicate anche Minuti, Secondi e le ombre abbinate. Le scelte singole successive rimangono indipendenti. Nel livello Lancetta piccola, il menu offre anche le nuove grafiche piccole; scegli poi la sorgente del dato o del cronografo nelle proprietà come prima.

**Modifica** riapre un set esistente: nome, tipo, PNG, pivot e ombre sono modificabili. **Aggiorna set nel catalogo** conserva gli ID dei ruoli presenti. Per un secondo set usa **Nuovo set** e un nome diverso; i nomi duplicati vengono rifiutati. Le modifiche al catalogo non alterano automaticamente i livelli già creati: riapplica il modello quando vuoi aggiornarli.

**Elimina** rimuove il set dai menu personali. Le PNG già incorporate nei progetti rimangono disponibili e i quadranti esportati sono autonomi. Le risorse PNG del catalogo hanno nomi basati su SHA-256; vengono mantenute sul disco anche dopo l’eliminazione di un set e non vengono cancellate insieme ai progetti. Un nuovo set non salvato è una bozza della sessione: premi Salva prima di chiudere l’app o passare a un’altra bozza.

Nell’eseguibile il catalogo è in `%LOCALAPPDATA%/S5Studio/hand-sets/`, comune alle nuove versioni sullo stesso account Windows. Per trasferirlo copia l’intera cartella su un altro PC. In modalità sorgente è in `data/hand-sets/`. Il file EXE incorpora il catalogo originale, senza i set personali creati durante lo sviluppo. I progetti salvati incorporano comunque tutte le PNG applicate.

Il salvataggio del catalogo è atomico; sono controllati formato PNG, dimensioni, trasparenza totale, pivot, percorsi e hash. Le PNG vengono normalizzate a RGBA mantenendo dimensioni e allineamento, senza ritaglio o ridimensionamento. Le anteprime dei menu sono copie ridotte. Il progetto continua a utilizzare gli stessi componenti nativi e Lua di prima, senza nuove API sul firmware.

Verifiche automatiche e controlli del pannello da sorgente sono registrati in [validation-editor-1.6.json](validation-editor-1.6.json). Il test reale delle novità 1.5 e 1.6 sul dispositivo è ancora da eseguire. Non sono stati creati backup, quadranti dimostrativi o prove dell’eseguibile in ambiente isolato.
