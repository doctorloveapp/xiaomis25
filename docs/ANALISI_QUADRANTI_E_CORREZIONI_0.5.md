# Analisi dei quadranti e correzioni 0.5

## Corpus ed evidenze

La scansione copre tutte le 39 cartelle in `quadranti/`, inclusa una vuota, e tutti i 7.513 file anche fuori dalla sottocartella contenente il payload. Per ogni file registra percorso, dimensione e SHA-256; XML/JSON sono letti come dati, senza eseguire contenuti dei pacchetti. [Inventario](library-analysis/inventory.md), `library-analysis/catalog.json` e rapporti individuali contengono gerarchia e metadati. I conteggi “Slot dichiarati” comprendono temi diversi e slot condizionali: non indicano quanti slot l’utente può modificare contemporaneamente.

Sono state trovate 61 sorgenti XML. **58** hanno un binding nativo numeric/pointer/lista dimostrato e sono incluse nella libreria `data/watchface-library.json`. Le altre tre sono sorgenti di testo formattato: dateLunarStringMonth, dateLunarStringDay e weatherCurrentPressure. Questa versione non compila quel testo dinamico; offre le sorgenti numeriche osservate, compresa pressione atmosferica 5842. Non inventa codici per sensori assenti dai campioni.

LLATH (562700103, autore Aksiarin) ha 22 dichiarazioni Slot widget distribuite su due temi, cioè **11 simultanee per tema normale**. SkyHawk (562700050, HaloX78) ha sette slot condition, non sette menu di scelta. Il limite precedente di due era quindi dell’implementazione Studio. La 0.5 permette 16 slot nel progetto, senza dichiarare questo numero un limite hardware certificato.

La libreria raccoglie **124 lancette per giro completo**, deduplicate per bitmap e pivot, con autore, tema e hash. Il pivot viene letto dal binario a offset 20/22 nel descrittore pointer, evitando errori di arrotondamento dei pivot XML frazionari. Immagini originali intatte in `data/hand-presets/`; 18 icone meteo e mappa dei codici osservati in `data/weather-presets/`. La provenienza dei preset resta esplicita.

## Diagnosi del test fallito

L’utente riferisce che S5_Analogico_Varianti_TEMPLATE.zip mostra lancette principali funzionanti, anteprima Suit and tie, nessun effetto cambiando stili/complicazioni e grafica mancante. La foto `quadrante_orologio_test_analogico.jpg` mostra i piccoli puntatori delle complicazioni privi delle relative grafiche complete.

Nel vecchio output erano verificabili due difetti: i metadati mantenuti descrivevano ancora risorse/stili di Suit and tie; i gruppi importati dipendevano da grafica del quadrante originale non inclusa nella loro chiusura autonoma. Una miniatura corretta sul PC non ricostruiva quella grafica nel runtime. Sono motivi concreti per cui il vecchio approccio era incompleto. Non dimostrano da soli quale ramo del firmware o della mod causasse ogni sintomo. Collisioni dell’ID originale/cache e gestione degli UID molto distanti restano ipotesi, non diagnosi accertate.

La frase “la grafica interna resta quella di Suit and tie” significava che cornici, scale e numeri dei gruppi selezionabili venivano riutilizzati, mentre sfondo e lancette del progetto erano personali. Era una scorciatoia del nostro adattatore e non offriva la libertà richiesta. Questo trapianto è stato eliminato.

## Correzioni del formato

- Parser delle directory: EasyFace 88 byte; protocollo vendor 0x800 160 byte; 0x900/903 176 byte. Le palette possono aggiungere byte diversi per tema: il passo viene calcolato per ogni directory, non come media. LLATH e altri campioni dimostrano perché la media sbagliava gli offset.
- Slot widget: tipo nativo 2, scelte UID, lunghezza UTF-8 comprensiva del padding; nome numerico stabile per lo stesso slot fra stili.
- Gruppi: header 44 byte, figli da 12 byte e trailer editor; riferimenti a titolo, preview e bordo espliciti, senza scansione indiscriminata delle parole binarie.
- UID: assegnazione compatta per categoria, con ricollocazione dei riferimenti e chiusura delle dipendenze dei gruppi generati.
- Numeri: parametro 1000 osservato nei campioni S5; EasyFace target 562 lo lasciava a zero. Campo cifre/decimali, segno al glifo 10 e punto al glifo 11 coerenti con i campioni. Quantità e unità effettive richiedono il confronto hardware.
- Preview: PNG del progetto, preview native compilate per ciascun tema, risorse di miniatura e bordo per ciascuna opzione; nomi e riferimenti concordano fra binario, manifest ed editor.
- Nuovi progetti: ID personale distinto dal template e modificabile nella UI. I progetti già salvati conservano il loro ID; questa scelta riduce le collisioni possibili, senza provare la causa della cache precedente.

## Template e validator

La chirurgia mantiene gli attributi ZIP e i record compressi originali di **187 file protetti e otto directory**. Capability.json e hashCode sono conservati, senza tentativi di reinterpretare maschere o firma. Sono sostituiti resource.bin e 28 anteprime; description.xml, resources/manifest.xml, uidmap.map ed editor.config.json sono rigenerati perché devono descrivere le nuove risorse. Si aggiungono risorse Studio e un manifest locale con hash.

Il validator verifica CRC, record protetti, percorsi, ID, offset, sorgenti, UID, layout, scelte dei gruppi, nomi/tipi dei temi, preview native, editor e hash di PNG/metadati. Blocca una build incoerente; il vecchio analogico 0.4 viene rifiutato per metadati obsoleti. Questa firma strutturale locale non certifica autenticità Xiaomi o accettazione del capability test.

## Verifiche e limite dell’evidenza

37 test passati includono compilazione reale di tutte le 58 sorgenti, meteo con la mappa originale dei 18 codici, decimali nativi, cinque stili/cinque slot, bitmap/pivot personali e rifiuto di output corrotti. Una compilazione aggiuntiva offre tutte le 58 sorgenti più Nessuna in ciascuno dei cinque slot, su cinque stili: 22.524 voci ZIP validate, con limite di 100.000 voci / 128 MB per gestire la moltiplicazione degli asset. Rapporto `stress-all-sources-0.5.json`. La UI reale è provata con QtWebEngine/QWebChannel. Il nuovo pacchetto ha dieci temi normal/AOD e 25 istanze native di slot.

Il precedente digitale 0.3 è riuscito secondo l’utente, mentre l’analogico 0.4 è fallito: [registrazioni](../data/hardware-tests/). La nuova versione resta **non verificata sul S5** fino al test successivo. Le selezioni, i dati reali, l’aggiornamento dei canali e la gestione preview della mod possono essere certificati solo con quella prova.
