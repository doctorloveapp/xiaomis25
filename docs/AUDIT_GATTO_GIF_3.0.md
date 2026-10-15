# Audit Gatto — GIF e regolarità dei secondi

Data: **15 ottobre 2026**. Applicazione: **S5 Studio 3.0**. Profilo dispositivo noto: **Xiaomi Watch S5 M2530W1 / firmware 3.221.024**.

## Esito

**Non è emerso un errore nell’abbinamento o nella frequenza esportata delle lancette. Non è dimostrato un limite hardware inevitabile.** La causa più plausibile dei salti riferiti dall’utente è la concorrenza tra caricamento/decodifica/disegno della GIF a pieno schermo e aggiornamento grafico dei secondi. È un’ipotesi motivata dai dati del pacchetto, non una misura di CPU, GPU, cache o RAM sull’orologio.

Esistono alternative software concrete, con compromessi misurabili. Nessuna può essere dichiarata risolutiva senza una prova sul dispositivo. Questo intervento è un **audit**: codice applicativo, runtime Lua, progetti ed eseguibile non sono stati modificati. Non è stata creata una nuova release.

## File esaminati

- Progetto esportato: `Quadranti Compilati/Gatto-865100840-20261015-145916/Gatto.s5faceproj`.
- Pacchetto installabile della stessa cartella: `Gatto.zip`, con relativo `build-report.json`.
- Bozza: `projects/Gattos5faceproj.s5faceproj`.
- Sorgenti: `gif_animation.py`, `studio_gif.lua`, generazione FPRJ, composizione binaria, binding delle lancette e validazione del pacchetto.

Gli hash degli input e dell’eseguibile sono nel [rapporto misurabile](gatto-performance-audit-3.0.json). L’hash del binario presente nello ZIP coincide con quello del rapporto di compilazione. I file originali sono rimasti intatti.

## Dati verificati

| Voce | Risultato |
| --- | --- |
| Fotogrammi nel progetto | 60 totali, **9 inclusi**, indici 9–17 |
| Velocità GIF | **50%** |
| Dimensioni del livello | 485 × 485, ritagliato a **480 × 480** |
| Dimensioni delle immagini GIF sorgente | 400 × 400, ingrandite durante l’esportazione |
| Risorse animate esportate | 9 PNG RGBA da 480 × 480, tutte completamente opache |
| Totale PNG animati | **4.461.486 byte** compressi, circa 4,46 MB |
| Percorso GIF | App Lua/LVGL separata; nessun SpriteGroup nel pacchetto attuale |
| Pianificazione | 30 posizioni da 40 ms, ciclo **1.200 ms** |
| Cambi immagine nominali | **7,5 al secondo**, con nove immagini distinte per ciclo |
| Movimento fluido | Disattivato per tutte le lancette |
| Lancette e ombre native normali | Sei descrittori; ore `0811`, minuti `1011`, secondi `1811`, tutti a **1.000 ms** |
| ZIP attuale | **19.641.135 byte** |
| Binario attuale | **6.940.892 byte** |

La cadenza da 40 ms è la risoluzione della pianificazione GIF e il target del callback di animazione; **non significa che vengono decodificate 25 immagini diverse al secondo**. Il runtime confronta il fotogramma con quello precedente e scrive la sorgente soltanto quando cambia.

Ridurre il numero di fotogrammi senza allungare il tempo di permanenza delle immagini accorcia il ciclo e riduce lo spazio occupato, ma può lasciare praticamente invariato il lavoro grafico al secondo. Nove immagini a pieno schermo ripetute rapidamente restano un carico diverso da nove immagini statiche.

## Cosa esclude l’analisi

Il pacchetto non contiene lancette dei secondi accidentalmente rimaste a 25 fps. Lancetta e ombra dei secondi usano il canale nativo corretto con periodo di 1.000 ms. Il valore generale `sweepFps: 25` nel report descrive il target disponibile; i periodi dei singoli puntatori dimostrano il comportamento effettivamente configurato.

`studio_gif.lua` non scrive l’ora, non cambia la sorgente `timeSecond`, non usa un proprio Timer Lua e applica già Write-on-Change. L’animazione e le lancette restano due componenti distinti. Non è stata trovata una formula che faccia avanzare o arretrare i secondi durante il cambio fotogramma.

Resta possibile un ritardo nel presentare sul display la posizione aggiornata del puntatore. La documentazione LVGL spiega che la decodifica ripetuta di PNG può essere onerosa e che il caching riduce il lavoro consumando memoria. **La configurazione della cache del firmware S5 non è nota**: non si assume che corrisponda al default della libreria. [LVGL: immagini e cache](https://docs.lvgl.io/8.3/overview/image.html).

## Prove di fattibilità con il compilatore

Sono state compilate tre varianti temporanee `.face`, senza produrre ZIP dimostrativi e senza avviare S5 Studio. I file temporanei sono stati eliminati. Sono stati verificati header, limiti, riferimenti, presenza AOD e conservazione di sorgenti/periodi di tutte le lancette.

Le dimensioni delle prove sono quelle dei binari intermedi prodotti direttamente da EasyFace: non sono ZIP finali né risultati della successiva composizione sul template. Il confronto dimostra soprattutto la crescita dell’ImageArray; il pacchetto installabile avrebbe anche metadati e anteprime.

| Prova | Risultato verificato | Compromesso |
| --- | --- | --- |
| Nativa a cadenza uniforme, 9 immagini, 130 ms | Nessuna App Lua; ciclo 1.170 ms; binario **11.375.360 byte** | Sostituisce i tempi variabili con tempi uniformi; ciclo 2,5% più breve rispetto alla pianificazione attuale |
| Stessa prova con suffisso RGBA | Stesso formato e dimensione della precedente | Nessun risparmio ottenuto cambiando il solo suffisso |
| Nativa con pianificazione attuale esatta | 30 immagini codificate, 40 ms, ciclo 1.200 ms; nessuna App Lua; binario **34.809.136 byte** | Duplica le bitmap per i tempi di permanenza, facendo crescere molto il pacchetto |

Il suffisso RGB è documentato da EasyFace, ma **nelle prove di animazione con Compiler 4.23 / target 562 il solo cambio di nome non ha prodotto RGB565**: il byte di formato dell’ImageArray è rimasto 4 e i payload RGB/RGBA erano identici. Non è quindi corretto promettere un dimezzamento della memoria attraverso quel parametro. [EasyFace: animazioni](https://github.com/m0tral/EasyFace/wiki/Animations), [formati delle immagini](https://github.com/m0tral/EasyFace/wiki/ImageFormatEN).

L’ImageArray osservato contiene lunghezze e bitmap consecutive, non riferimenti riutilizzabili fra posizioni. Non è stata introdotta una struttura inventata per riutilizzare le immagini: richiederebbe una prova ulteriore di compatibilità del firmware.

**Una compilazione valida dimostra che l’alternativa è costruibile, non che elimini i salti sul S5.** Il backend nativo evita il cambio di sorgente PNG eseguito da Lua, ma conserva costi di decodifica nativa e disegno; potrebbe comunque risentire del carico grafico.

Il profilo del template conserva inoltre `imageArrayRamMethod: whole`. Non è stata misurata l’applicazione concreta di questa proprietà da parte del firmware: un’ImageArray grande può avere costi di memoria differenti dalle immagini PNG caricate separatamente. Anche questa ragione sconsiglia di sostituire automaticamente il backend attuale senza prova reale.

## Interventi consigliati

1. **Prova senza cambiare il software:** mantenere i nove fotogrammi e impostare Velocità a **25%**. Il ciclo nominale diventa 2.400 ms e i cambi immagine scendono a **3,75/s**. La posizione dei secondi continua a provenire dall’ora dell’orologio. Se i salti diminuiscono, aumenta l’evidenza di un problema legato al carico grafico. È una prova diagnostica, non una promessa di soluzione.
2. **Ottimizzazione software più interessante:** offrire una modalità facoltativa di cadenza uniforme nativa per GIF fuori dalla scena Lua condivisa, mostrando il tempo/ciclo realmente esportato. Conservare il percorso attuale per chi vuole la pianificazione variabile. La prova a 130 ms dimostra la fattibilità tecnica e il costo in spazio; resta da verificare il beneficio sul dispositivo.
3. **Alleggerimento senza toccare l’orologio:** verificare la rimozione lossless del canale alfa per i PNG completamente opachi e mantenere l’alfa quando serve. Riduce i dati sorgente da trattare, ma il decoder firmware può comunque convertirli internamente allo stesso formato: beneficio prestazionale da misurare.
4. **Per composizioni più esigenti:** usare uno sfondo statico e una GIF limitata alla zona realmente animata. Dimezzare larghezza e altezza riduce a un quarto i pixel dell’elemento; non equivale a limitare soltanto il numero totale di fotogrammi.

Non consiglio di caricare preventivamente tutti i fotogrammi in RAM, forzare una cache globale non documentata, alterare il clock dei secondi o introdurre un timer alternativo per le lancette. La dimensione della RAM e le API firmware disponibili non sono state accertate.

## Giudizio finale

**C’è margine di miglioramento dal software; non ci sono elementi sufficienti per dire che stai chiedendo troppo all’hardware del Watch S5.** Il progetto è configurato correttamente. Il percorso PNG a pieno schermo è il primo candidato da alleggerire, con una modalità nativa facoltativa e controlli che preservino AOD, trasparenza, ordine dei livelli e comportamento del cronografo. La causa definitiva e l’efficacia sul dispositivo richiedono il confronto reale fra le due modalità o misure del firmware.

[Evidenza tecnica](gatto-performance-audit-3.0.json) · [Riscontro hardware dell’utente](hardware-gif-3.0.json) · [Guida GIF/AOD](GIF_3.0.md)
