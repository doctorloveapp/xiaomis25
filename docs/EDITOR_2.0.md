# S5 Studio 2.0 — Crono Pro POST e archi calibrati

La 1.9 ha superato il test reale sullo Xiaomi Watch S5, come confermato dall'utente l'11 ottobre 2026. [Esito](hardware-test-1.9.json). La 2.0 aggiunge indicatori POST al Crono Pro e calibrazione degli archi; il precedente cronografo separato continua a usare il proprio runtime.

## Configurare sei lancette di misura

1. Nel gruppo Lancette attiva **Crono Pro** nella scheda Secondi. Le lancette grandi ore/minuti continuano a indicare l'ora; quella grande dei secondi passa al cronografo durante la misura.
2. Aggiungi le piccole con **Ore Crono**, **Minuti Crono** e **Decimi crono · Start/Stop/Reset**: queste tre e la grande dei secondi costituiscono le quattro lancette in movimento.
3. Aggiungi altre due piccole con **Centesimi (POST)** e **Millesimi (POST)**. Non hanno un flag Movimento Fluido: durante Running restano alla posizione iniziale. Allo Stop mostrano la lettura acquisita con l'animazione comune da **720 ms**, aggiornata al massimo a **25 fps**. Il Reset include tutte e sei le lancette di misura.
4. **Lettura POST** offre la frazione completa del secondo (00–99 / 000–999), predefinita come richiesto dall'utente, oppure la singola cifra (0–9). Per esempio, a 12,488 s: decimi = 4, centesimi completi = 48, millesimi completi = 488; scegliendo le singole cifre, centesimi = 8 e millesimi = 8. Non si tratta dei millisecondi totali trascorsi.
5. Per un giro completo usa intervallo 100 per i centesimi, 1000 per i millesimi, 10 per una singola cifra; rotazione 360° oppure −360°. L'ultima tacca 99/999/9 precede il ritorno allo zero.

La sequenza dei tap resta **Prepara → Avvia → Stop → Reset**. Dopo Stop, durante i 720 ms di posizionamento POST, gli altri puntatori sono già fermi; il tap successivo è accettato a posizionamento finito. Nell'editor la fase si chiama Lettura POST. Nessun nuovo tap o sorgente sensore è necessario.

## Creazione dei set piccoli con Centesimi e Millesimi

Nella sezione **Set lancette** seleziona **Tipo di set → Lancette piccole**. Sono disponibili cinque schede: Ore, Minuti, Secondi, **Centesimi** e **Millesimi**. Ogni scheda importa una PNG distinta, con il proprio pivot e la propria ombra facoltativa. **Genera ombre** include anche i due nuovi ruoli. Per un set piccolo basta almeno una grafica; puoi quindi creare anche un set con soltanto Centesimi/Millesimi. I set principali conservano esclusivamente Ore/Minuti/Secondi.

Salva il set, torna al quadrante, seleziona una lancetta piccola e scegli la nuova grafica dal suo catalogo. **Usa modello** riconosce il ruolo e abbina Centesimi (POST) o Millesimi (POST), richiedendo Crono Pro nello stesso stile e schermo normale. Per un nuovo abbinamento propone frazione completa e intervallo 100/1000 (99/999 in arco); se la lancetta usa già la stessa sorgente, conserva tutti gli estremi dell'arco e il tipo di lettura. I PNG, pivot e le ombre restano incorporati nel progetto. Puoi riaprire e modificare i set; sincronizzazione e packaging conservano i nuovi ruoli sui nuovi PC. La modifica non tocca i runtime Lua o il conteggio Crono.

Aggiornamento del catalogo personale: integrato **Bulova**, per otto set, 23 modelli aggiuntivi e **618 modelli totali**. Cataloghi sorgente intatti. Completamento verificato con **30 test mirati e 10 controlli UI**, inclusi importazione, modifica, ombre, abbinamento POST, conservazione della calibrazione e sincronizzazione per un nuovo PC. I runtime Lua coincidono con quelli della prima consegna 2.0. [Controlli editor](hand-set-post-editor-2.0.json).

## Arco di rotazione personalizzato

Il flag **Arco di rotazione personalizzato** è aggiuntivo: disattivandolo tornano Intervallo valori e Rotazione totale, con giro completo disponibile. È presente nelle proprietà delle lancette piccole, anche per sorgenti precedenti. Non è l'effetto Arco applicato a testo/dati.

Con il flag attivo imposta **Valore iniziale**, **Valore finale**, **Angolo iniziale**, **Angolo finale** e **Direzione dell'arco**. L'angolo 0° è verso le ore 12; 90° verso le ore 3; gli angoli sono riferiti alla grafica della lancetta orientata verticalmente. Il pivot resta configurabile come prima. Modificare un estremo iniziale conserva l'estremo finale. Sono supportati valori interi non negativi; 0.000 è numericamente 0.

Per la lettura completa dei millesimi imposta **0 / 999** per distribuire tutta la frazione su un arco; **0 / 99** per i centesimi. Le unità sono quelle della sorgente: se la tacca stampata «8» rappresenta 0,800 s, il Valore finale va impostato a **800**, non 8. Un Valore finale 8 nella lettura completa dei millesimi rappresenta invece **8 ms**, cioè 0,008 s. La calibrazione è libera e non interpreta automaticamente i numeri stampati nella grafica.

Esempio angolare: **30° / 140°** in verso orario percorre 110°; in verso antiorario percorre 250°, perché deve raggiungere lo stesso angolo finale nel verso opposto. Per un arco antiorario breve di 110° imposta invece **140° / 30°**. Gli estremi coincidono con le tacche scelte, indipendentemente dal verso. I valori fuori scala si fermano agli estremi: con scala 0–800, una lettura 900 arriva alla tacca 800. La modalità facoltativa Singola cifra permette anche una scala letterale 0–8; in quel caso il 9 si ferma a 8 e non è distinguibile.

**Mostra inizio** e **Mostra fine** permettono di calibrare visivamente la lancetta sopra qualunque immagine caricata, anche prima di avviare il cronografo. Modifica gli angoli/pivot finché combaciano con le tacche. **Dato reale** ripristina la simulazione; anche Prepara/Avvia Crono elimina la posa di calibrazione. La posa è soltanto dell'editor e non viene salvata nel progetto o esportata sul dispositivo.

Negli archi POST i valori sono interpolati entro gli estremi durante Stop e Reset. Il ritorno ripercorre l'arco al contrario per non attraversare la zona senza scala. È una scelta esplicita per gli archi calibrati; i rientri delle lancette a giro completo mantengono la direzione fisica oraria già collaudata. La durata/easing comuni restano invariati. Gli angoli sono interi e la rotazione di un arco deve essere tra 1° e 359°; per 360° disattiva il flag.

## Clock, precisione e carico

Tutte le lancette leggono un unico `elapsed` congelato dal tap Stop. Il tempo deriva dallo stesso clock già usato dal Crono Pro: priorità a `lvgl.tick_get`, poi `/proc/uptime`, con fallback alla fase dell'animazione LVGL. Per i POST il runtime calcola `floor((elapsed % 1000) / 10)` e `floor(elapsed % 1000)`, applicando `% 10` se si richiede una cifra singola. Non conta callback per inventare millisecondi e non estrapola una frazione dopo Stop.

**Tre cifre visualizzabili non certificano una precisione di 1 ms.** `tick_get` è letto al tap quando disponibile; la precisione effettiva dipende comunque dal clock e dalla consegna dell'evento. `/proc/uptime` può avere risoluzione più grossolana. Nel fallback Anim si legge l'ultima fase pubblicata dal motore, quindi la lettura è campionata ai fotogrammi. Durante sospensioni la correzione tramite `os.time` ha precisione di un secondo; se la pagina Lua viene ricreata, il conteggio si azzera come prima. Il valore non viene presentato come misura certificata al millisecondo.

I due POST non aggiungono timer rapidi né animazioni continue durante Running. Il timer già presente resta a 100 ms con decimi crono, a 1000 ms senza. Le scritture Pointer sono memorizzate e ripetute soltanto quando cambia il valore. Durante Stop si animano soltanto i due POST; durante Reset l'animazione comune coordina le sei lancette. Memoria/disegno aumentano per le due immagini aggiunte e le eventuali ombre; consumo e fluidità con sei lancette restano da misurare sul dispositivo.

Il nuovo stato `reading` termina in `stopped`. In AOD/OFF il renderer Pro viene nascosto e l'animazione interrotta immediatamente; la lettura congelata viene conservata, quindi sul ritorno ON appare nella posizione finale, senza riprendere un'animazione nascosta. L'AOD usa la propria scena precedente, con secondi e tutti i POST esclusi. Una pausa temporanea durante il tocco sospende e riprende l'animazione senza perdere la misura.

## Esportazione e verifiche

Una sola scena Lua per stile registra tutti i puntatori nella stessa VM. `studio_core_pro.lua`, runtime classico di supporto, campionamento civile, immagini e dipendenze sono incorporati sia nel binario sia nella struttura finale prevista dal template. Il manifest finale mantiene `interactive="true"`. Il validatore controlla sorgenti, ID, modalità POST, calibrazione e presenza del runtime POST.

`build-report.json` contiene `interactive.chronoPro.postReadout`: indicatori per stile, tipo di lettura, estremi valori/angoli, assenza di nuovi timer Running, durata/frequenza delle animazioni, timestamp comune e `millisecondAccuracyGuaranteed=false`.

Verifiche: **99 test mirati**, **14 controlli UI** dai sorgenti, sintassi JavaScript, compilazione EasyFace temporanea e confronto del grafo finale/manifest/file Lua in memoria. Inclusi sei puntatori, intervalli a cavallo di secondi/ore, wrap del tick, fallback senza tick, stop/reset, AOD e pausa durante il tocco, archi orari/antiorari, uguaglianza tra anteprima e Lua. Nessun ZIP dimostrativo, backup o avvio dell'eseguibile.

Catalogo personale aggiornato: integrati **Longine** e **Bulova**, otto set, 23 modelli aggiuntivi, 41 PNG e **618 modelli totali**, preservando i cataloghi sorgente e il `.gitignore`. Avvia **S5Studio-2.0-aggiornato.exe**, apri il progetto e riesporta lo ZIP. Il nuovo funzionamento POST 2.0 richiede il tuo test reale sull'S5.

Eseguibile 2.0 creato e verificato staticamente: 754 risorse incorporate, 20 moduli Python corrispondenti ai sorgenti testati e file Lua identici. Non è stato avviato.

[Test](validation-editor-2.0.json) · [Editor](chrono-post-editor-2.0.json) · [Bundle](executable-build-2.0.json) · [Catalogo](hand-set-integration-2.0.json).
