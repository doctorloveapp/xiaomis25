# Version history and earlier operating notes

[Documentation index](README.md) · [Current README](../README.md) · [Italian README](../README.it.md)

This page preserves the release history and operating notes previously in the
README, in Italian. Each entry describes its own release: executable names,
test counts, pending tests and implementation details can be superseded by
later entries. Use the current README and guides for installation and behavior.
Referenced personal projects, demo packages and previous restore points are
historical records; they are not promised as public repository contents.

**2026-10-13:** the user confirmed successful operation of version 2.7 on the
Xiaomi Watch S5. See [the hardware confirmation](hardware-test-2.7.json).
The earlier “awaiting hardware test” statements below describe the delivery
status on 2026-10-12 and are retained as dated history.

## Novità 3.1 — limiti GIF e compatibilità secondi/cronografo

Massimo **10 fotogrammi inclusi per GIF visibile normale**, verificato in tutti gli stili: contatore, messaggio ed Esporta ZIP disabilitato oltre il limite. Bozze, importazione ed esclusi restano modificabili/salvabili. Scorrimento dei fotogrammi conservato.

In uno stile con GIF visibile vengono escluse lancetta grande secondi/ombra, piccole dei secondi/decimi e tutte le lancette Crono/POST; **Crono, Crono Pro, Only Crono e relativi tap sono disabilitati**. Avviso italiano/inglese/cinese e controlli bloccati. Le preferenze restano nel progetto e si ripristinano nascondendo/eliminando la GIF. Uno stile senza GIF conserva il cronografo. Anche una GIF con un solo fotogramma o preview PC ferma segue la regola conservativa. AOD indipendente, sempre modificabile/esportabile, con GIF esplicite statiche.

Anteprima e sorgenti EasyFace usano una copia separata con le esclusioni. `gifSafety` nei rapporti ZIP/esterno descrive ogni stile; il validator rifiuta secondi nativi o un controller Crono attivo nello stile GIF. Il progetto consegnato accanto al ZIP conserva le impostazioni originali. Tutti gli otto Lua invariati rispetto alla 3.0; nessuna modifica al clock. Il limite è una scelta applicativa, non un massimo firmware scoperto.

**96 test mirati, 9 controlli editor e 2 compilazioni/ZIP superati**, incluse varianti miste GIF/Pro, quattro viste con AOD, ripristino, confronto anteprima e rifiuto di un puntatore secondi reinserito. Set personali controllati: 13, nessun aggiornamento, 635 modelli/90 dischi conservati. Solo Bulova incorporato. EXE verificato staticamente; nessun avvio isolato, backup o ZIP dimostrativo. Le nuove limitazioni attendono la prova reale. [Guida](GIF_3.1.md) · [Verifiche](validation-editor-3.1.json).

### Audit Gatto 3.0 — riscontro hardware e prestazioni (2026-10-15)

L’utente conferma la riproduzione della GIF sull’orologio, ma segnala salti saltuari dei secondi con tutti i flag fluidi disattivati. Verificati progetto e ZIP effettivo: nove PNG RGBA opachi a pieno schermo, velocità 50%, 7,5 cambi immagine/s; sei puntatori e ombre nativi correttamente a 1.000 ms. Il runtime GIF applica già Write-on-Change e non scrive l’ora. Decodifica/disegno concorrente è la causa più plausibile, non misurata sul firmware; non è dimostrato un limite hardware inevitabile.

Tre compilazioni `.face` temporanee verificano la fattibilità di alternative native: nove immagini uniformi a 130 ms senza Lua, oppure 30 posizioni per conservare la pianificazione variabile. Quest’ultima porta il binario a 34,8 MB; il solo suffisso RGB non cambia il formato prodotto dal compiler target 562. Prove di compilazione, non benchmark hardware. Documentato il confronto diagnostico con velocità 25% (3,75 cambi/s).

**Solo audit: codice, runtime, eseguibile e progetti intatti**; nessun backup, avvio EXE o ZIP dimostrativo. Set personali controllati: 13, nessuna modifica. [Rapporto](AUDIT_GATTO_GIF_3.0.md) · [Dati](gatto-performance-audit-3.0.json) · [Riscontro utente](hardware-gif-3.0.json).

## Novità 3.0 — GIF animate e creazione da zero

Nuovo pulsante **＋ Gif** dopo Immagine. Tutti i fotogrammi vengono decodificati con trasparenze e disposal; si possono escludere, eliminare con Annulla e riprodurre in anteprima. Velocità 25–400%, massimo 25 fps. Immagini statiche e GIF mantengono il proprio ordine; scale, ritaglio, rotazione e arco vengono applicati ai fotogrammi.

Esportazione nativa SpriteGroup/ImageArray, con fallback LVGL per GIF dentro la scena Crono o sequenze lunghe. Metadati, binding, risorse, conteggi e report GIF sono validati nel ZIP. In AOD nessuna GIF normale è copiata; eventuali GIF aggiunte espressamente sono statiche e possono essere eliminate indipendentemente. Avvio vuoto e tacche disattivate sulle nuove lancette; scelte dei progetti precedenti conservate.

**Verifiche:** 162 test mirati, 10 controlli dell’editor e compilazione temporanea di due stili/due AOD con sfondo statico, tre percorsi GIF e Crono Pro. Sette moduli Lua preesistenti invariati; studio_gif.lua è indipendente dal conteggio. Nessun backup, avvio EXE o prova isolata; il test fisico delle GIF è ancora necessario. Integrato Lorenz Star Trek: 13 set personali e 635 modelli. Solo Bulova come esempio. [Guida](GIF_3.0.md) · [Test](validation-editor-3.0.json) · [Compilazione](export-validation-3.0.json).

### Correzioni 3.0 — AOD, limite GIF e compilazione Gatto (2026-10-15)

**AOD sempre accessibile**, anche con GIF e anche quando escluso dall’esportazione. Aggiungere o modificare un suo livello ne attiva automaticamente l’esportazione; resta disponibile il pulsante Includi AOD nello ZIP. Il pacchetto conserva la composizione AOD scelta, indipendente dal normale; una GIF esplicita in AOD è statica.

**Massimo 20 fotogrammi inclusi per GIF visibile normale**, in ogni stile: contatore, messaggio e ZIP disabilitato oltre il limite, con controllo backend prima della compilazione. Le bozze più grandi restano apribili/modificabili/salvabili. I flag dei fotogrammi si aggiornano sul posto, senza ricreare il pannello né spostare lo scroll.

Gatto aveva 60 fotogrammi, 44 inclusi e 73 bitmap native per rappresentare i tempi variabili; il precedente ZIP pesava 90,6 MB. Il log incompleto e l’intervallo di circa 93 secondi sono coerenti con il timeout del compilatore a 90 secondi, non con un massimo firmware di 44 fotogrammi. Il percorso LVGL riusa una sola bitmap per fotogramma incluso. Con 20 fotogrammi e AOD scelto: **9,76 secondi, ZIP 31,6 MB**, AOD statico verificato e preview identica al progetto. Il limite di 20 è una politica Studio; non è stata verificata la dimensione massima firmware.

**98 test mirati, 7 controlli editor e compilazione reale Gatto/AOD superati**; progetto originale intatto, output temporaneo eliminato. Tutti gli otto Lua invariati rispetto alla prima 3.0; pacchetti precedenti ancora validabili. Catalogo personale ricontrollato: 13 set, nessun aggiornamento. Nessun backup o avvio EXE; verifica statica del bundle. [Guida](GIF_3.0.md) · [Controlli](gif-hotfix-editor-3.0.json) · [Diagnosi](gatto-gif-diagnosis-3.0.json) · [Compilazione](gatto-export-hotfix-3.0.json).

## Novità 2.9 — header e cinese semplificato

Selettore lingua con icona globo, etichetta accessibile e altezza uniforme di 36 px con Apri, Salva ed Esporta ZIP. Verificato l’allineamento a 1120 e 1440 px nelle tre lingue. Aggiunto **简体中文**, con cataloghi JSON/Qt completi e font CJK di sistema; italiano ancora predefinito, preferenza conservata tra gli avvii. Nomi e contenuti dei progetti restano quelli dell’utente.

Integrato il nuovo set personale **Swatch Luce**: 12 set, 632 modelli complessivi e 90 dischi. Il solo esempio incorporato resta Bulova; altri progetti, recuperi, preferenze e cronologie personali esclusi. Sorgenti dei cataloghi e `.gitignore` conservati.

**Verifiche:** 59 test mirati, 16 controlli editor e 161 contesti renderizzati in cinese. Eseguibile 2.9 verificato staticamente; sette moduli Lua identici alla 2.8, senza modifiche a compilazione o Crono Pro. Nessun avvio dell’EXE, test isolato, backup o ZIP dimostrativo. [Guida](I18N_2.9.md) · [Test](validation-editor-2.9.json) · [Bundle](executable-build-2.9.json).

## Novità 2.8 — i18n

Italiano predefinito e inglese selezionabile dalla barra superiore, con preferenza applicativa persistente. Cataloghi Qt TS/QM e JSON frontend offline, estrazione automatizzata, dati utente protetti. 43 test mirati e 10 controlli editor superati; sette moduli Lua invariati. [Guida](I18N_2.8.md) · [Verifiche](validation-editor-2.8.json).

### Rifinitura 2.8 — release internazionale

Completate le etichette inglesi composte e i testi dinamici di cataloghi, tooltip, importazione, validazione, compilazione e cronografo. 54 test mirati, 11 controlli editor e 161 contesti di localizzazione superati. Italiano predefinito; nomi, percorsi e dati utente conservati.

**Solo Bulova** incluso come esempio, apribile da Progetto e AOD e salvabile come copia. Due stili e 14 risorse. Gli altri progetti, preferenze, recuperi e cronologie sono esclusi; i progetti esistenti restano apribili. Cataloghi lancette/dischi conservati. Il nuovo eseguibile 2.8 è verificato staticamente; la prova isolata precedente resta riferita al suo specifico hash. [Verifiche](validation-editor-2.8.json) · [Copertura](localization-coverage-2.8.json).

## Novità 2.7

**Ore 24 (giorno/notte):** corretto l'arrotondamento nel collegamento delle lancette normali inserite nella scena Lua. Il contatore Q8 viene troncato all'ora intera, come nel clock civile già collaudato: un valore 14,75 indica ancora le 14, non le 15. Lo stesso criterio vale per minuti e secondi. Nessuna correzione artificiale del fuso orario; scala 24, pivot e calibrazione del progetto rimangono quelli salvati. L'anteprima segue la stessa lettura. La riproduzione del difetto nei test usa valori frazionari; il dato grezzo del firmware non è stato acquisito.

**Secondi piccoli con Movimento Fluido:** l'animazione usa ora un oggetto trasparente dedicato, una singola esecuzione (`repeat_count=1`) e un arresto/riavvio esplicito a ogni secondo reale cambiato, seguendo la configurazione già impiegata nelle transizioni Crono Pro. Conserva aggiornamenti senza polling, ombre sincronizzate e sospensione immediata in AOD. Il conteggio Crono Pro, il disco lunare e gli altri sei moduli Lua restano invariati rispetto all'eseguibile 2.6 aggiornato. I secondi normali rimangono indipendenti da Start/Stop/Reset; l'utente ha confermato che questo comportamento funzionava già.

**Verifiche:** superati **114 test mirati**; esportazione temporanea del tuo Longines con **due stili e AOD** riuscita in **11,1 secondi**, provando il flag fluido attivo in uno stile e disattivo nell'altro. Validati binario, ZIP, manifest interattivo, binding e moduli Lua; progetto originale intatto. Cataloghi personali ricontrollati: **11 set, 629 modelli**, nessun aggiornamento da integrare. Nessun backup o avvio dell'EXE. **Le correzioni 2.7 attendono il test reale sull'S5.** [Dettagli tecnici](EDITOR_2.7.md) · [Test](validation-editor-2.7.json) · [Esportazione Longines](export-validation-2.7.json) · [Verifica EXE](executable-build-2.7.json).

**Eseguibile 2.7 creato e verificato staticamente:** 1.251 risorse, 43 moduli Python, entry point e sette moduli Lua corrispondono ai sorgenti testati; confermata l'identità dei sei moduli Lua preesistenti con la 2.6 aggiornata. Nessun avvio dell'EXE.

Per applicarle, salva e chiudi la vecchia versione, avvia **S5Studio-2.7.exe**, riapri il progetto, **riesporta lo ZIP e reinstallalo**. Non occorre ricreare le lancette o cambiare la calibrazione.

## Novità 2.6

**Esportazione Longine — aggiornamento nella stessa 2.6:** eliminato il blocco su «Dato Giorno». Il disco lunare si trovava sotto lo sfondo, mentre le lancette Crono Pro erano sopra giorno e mese: la scena Lua comprendeva tutto questo intervallo, ma non accettava i datari testuali né le lancette normali intermedie. Ora conserva l'ordine originale e aggiorna i giorni/mesi e i puntatori a sorgente nativa con notifiche reali `dataman`. Giorno e mese rimangono sotto le lancette; il disco rimane sotto la maschera dello sfondo. I motori Lua del cronografo, del clock civile e del disco lunare sono invariati; il nuovo modulo `studio_scene_data.lua` gestisce soltanto i dati inseriti nella scena. Inclusi anche i nuovi set **Longines** e **Longines_Lancette piccole**: 11 set personali, 629 modelli complessivi.

**Verifiche della correzione:** superati **90 test mirati** dei sorgenti su ordine, aggiornamento dei dati, ombre, secondi normali fluidi, varianti e sospensione/AOD; esportazione reale temporanea del progetto Longine superata in **10,1 secondi**, con validazione di ZIP, binario e manifest. Il file progetto originale è rimasto intatto. Salva e chiudi la vecchia applicazione, apri **S5Studio-2.6-aggiornato.exe**, riapri il progetto e riesporta senza spostare i livelli. [Analisi tecnica e limiti](LONGINE_LIVELLI_2.6.md) · [Rapporto Longine](validation-longine-scene-2.6.json). L'eseguibile aggiornato è stato verificato staticamente: **1.251 risorse, 43 moduli Python e sette moduli Lua**, tutti corrispondenti ai sorgenti. Questa nuova composizione attende il test sul dispositivo.

**Simula l'orologio:** nuovi campi **Giorno del mese (1–31)**, **Mese (1–12)** e **Anno (1900–2399)**. Cambiare il giorno aggiorna insieme il dato live del giorno, l'oggetto Data, la lancetta datario e il **disco lunare a 59 posizioni**. Mese e anno permettono una simulazione lunare coerente, compresi anni bisestili e passaggi di mese. Lo scenario Normale parte dal 15 ottobre 2026, con il giorno a due cifre già usato per verificare l'ingombro del datario.

Il calendario è condiviso anche con **Verifica calendario** nelle proprietà del disco: Mostra riferimento e Data attuale aggiornano i campi generali. Cambiare mese/anno adatta il giorno se necessario (31 ottobre → febbraio diventa 28, oppure 29 negli anni bisestili); un giorno esplicitamente inesistente viene rifiutato senza cambiare la data precedente. I valori simulati non modificano il progetto, la calibrazione o il calendario reale dell'orologio.

Corretta un'interferenza del simulatore **Crono Pro** che poteva sovrascrivere la posizione del disco lunare con un valore fisso. Il disco ora segue esclusivamente la data simulata anche con Crono Pro attivo. Questa correzione riguarda l'editor; i sei moduli Lua del quadrante restano invariati rispetto alla 2.5.

La prima build 2.6 aveva superato **87 test mirati e 20 controlli dell'editor**, compreso il confronto delle immagini al cambio del giorno, e la verifica statica di 1.238 risorse, 42 moduli Python e sei moduli Lua identici a quelli dell'EXE 2.5. L'aggiornamento Longine aggiunge un modulo Python e un modulo Lua per la composizione dinamica della scena; i sei moduli Lua precedenti restano invariati. Nessun avvio dell'eseguibile, backup o quadrante ZIP dimostrativo. [Guida al calendario simulato](EDITOR_2.6.md) · [Verifiche aggiornate](validation-editor-2.6.json) · [Rapporto dell'eseguibile aggiornato](executable-build-2.6.json).

## Novità 2.5

**Minuti giorno — aggiornamento nella stessa 2.5:** in **Lancetta piccola → Dato che guida la lancetta** trovi **Minuti giorno (0–59)**. Segue i minuti normali dell'orologio, indipendentemente dal cronografo; la selezione propone valore iniziale **0**, intervallo **60** e rotazione **360°** per un giro ogni ora. Puoi affiancarlo a **Ore (24h · giorno/notte)** nel sottoquadrante Longines. È la sorgente nativa `timeMinute`, prima indicata come Minuti completi, senza duplicazioni o modifiche al conteggio. Gli archi e gli angoli già calibrati mantengono il comportamento precedente.

**Disco lunare a 59 posizioni:** scegli **Fasi lunari · 59 posizioni (giornaliero)**. La selezione imposta automaticamente valore iniziale **0**, intervallo **59**, angolo iniziale **0°**, rotazione **360°**, correzione **0 giorni** e riferimento **26 settembre 2026**. Il disco avanza di una posizione per giorno civile, circa **6,10°**, e ricomincia dopo 59 giorni. Il conteggio deriva dalla data corrente: recupera anche i giorni trascorsi durante sospensioni o spegnimenti, senza salvare uno stato progressivo. Per un disco con due lune opposte ogni luna rappresenta un ciclo approssimato di 29,5 giorni.

**Longines pronto nel catalogo:** il tuo `DiscoLunare_Longines.png` è incorporato come **Longines Moonphase - 59-day disc**, con pivot **240 / 240** e impostazioni giornaliere già applicate. **Dischi → Aggiungi**, poi calibra angolo iniziale e verso rispetto alla finestra del tuo quadrante. La data di riferimento corrisponde a una luna piena secondo [USNO](https://aa.usno.navy.mil/calculated/moon/phases?date=2026-09-01&nump=8); il modello resta una simulazione meccanica da 59 giorni, non un calcolo astronomico preciso. Catalogo: **90 dischi e 516 immagini**.

**Calibrazione e anteprima:** puoi modificare riferimento, correzione in giorni, angolo iniziale e verso orario/antiorario. La verifica calendario nell'anteprima permette di provare una data senza cambiarla nel progetto esportato. **Mostra riferimento** verifica l'allineamento iniziale; **Data attuale** ripristina il calendario reale. Le vecchie sorgenti native a otto fasi e giorno lunare restano disponibili e i progetti precedenti conservano le loro impostazioni.

**Carico contenuto e AOD:** un nuovo modulo Lua indipendente dal Crono Pro riceve le notifiche del calendario e scrive solo le posizioni cambiate. Non usa un timer di animazione né polling continuo. Un breve timer da **200 ms**, normalmente sospeso, raggruppa le notifiche separate di anno/mese/giorno; evita posizioni intermedie ai cambi di mese e anno. In AOD il disco è statico fra le attivazioni, senza timer. Il calendario nativo ha precedenza; `os.date` è un fallback se disponibile. Lancette e clock del cronografo conservano il loro runtime.

**Lancetta datario:** in **Set lancette → Lancette piccole** trovi **Datario**, con PNG, pivot e ombra propri. **Usa modello** abbina automaticamente il giorno del mese, valore iniziale **1**, intervallo **31** e giro completo; se già abbinato al datario conserva la calibrazione. Per un arco impostato in precedenza propone l'intervallo 30 fra i valori 1 e 31. Non richiede Crono Pro e segue il calendario del firmware.

**219 test sulla 2.5 e 16 controlli dell'editor aggiornato superati**, comprese compilazioni native temporanee con più stili, disco lunare, AOD e datario. Per il successivo aggiornamento del nome/aiuto **Minuti giorno** sono stati ripetuti i soli 16 controlli dell'editor e la verifica JavaScript; nessuna nuova compilazione di quadranti. Dettagli nel [rapporto 2.5](validation-editor-2.5.json). **Il nuovo contatore giornaliero attende il test reale sull'S5**; non sono stati misurati consumo o frame rate. Nessun backup, avvio dell'EXE o quadrante ZIP dimostrativo. Cataloghi personali controllati: 9 set e 623 modelli, nessun aggiornamento da integrare; sorgenti preservati. [Guida alla calibrazione](DISCHI_LUNARI_2.5.md) · [Inventario](library-analysis/discs-2.5.json) · [Verifica dell'eseguibile](executable-build-2.5.json).

**Eseguibile 2.5 creato e verificato staticamente:** 1.238 risorse incorporate, 42 moduli Python, entry point e sei moduli Lua corrispondenti ai sorgenti testati. Catalogo Longines, interfaccia e ruolo Datario inclusi; nessun avvio dell'EXE.

## Novità 2.4

**Dischi:** nuova scheda accanto a Set lancette, con **89 modelli e 515 immagini** recuperati dai 39 pacchetti: sole/luna/stelle, bussole, rotore meccanico, quadranti e ghiere. Puoi importare nuove PNG, modificare anche i modelli incorporati, impostare il pivot con un clic e generare ombre con opacità, sfocatura e spostamento. I dischi rotanti usano i puntatori nativi; le sequenze lunari conservano le immagini e il collegamento al calendario originale. Ogni disco è un livello indipendente e il suo pivot iniziale è al centro. **Dischi → Aggiungi**, oppure **Quadrante → Disco → Usa modello**.

**Dato live:** il flag **Mese abbreviato** sceglie JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC; senza flag rimangono i nomi completi inglesi. **Fasi lunari** mostra gli otto nomi inglesi dalla sorgente nativa; per le immagini di luna, sole e stelle usa Dischi.

**Eliminazione dischi — aggiornamento 2.4:** il pulsante **Elimina** è disponibile per tutti i modelli, anche incorporati e modificati. La scelta persiste tra gli avvii e rimuove il modello dai menu; i livelli e le PNG già salvati nei progetti restano intatti. I modelli incorporati eliminati si recuperano dalla sezione **Dischi incorporati eliminati → Ripristina**. Le proprietà spiegano la distinzione fra **8 fasi lunari**, **giorni lunari 1–29/30** e una vera ruota da **59 posizioni**: l'intervallo numerico non crea un contatore giornaliero. [Calibrazione e limiti dei dischi lunari](DISCHI_LUNARI_2.4.md).

Questo aggiornamento conserva la versione **2.4**. Ricontrollati i **10 test sui dischi** (due nuovi, su eliminazione persistente e conservazione dei progetti) e **10 controlli dell'editor**. Nessuna modifica al runtime Lua o alla compilazione dei quadranti.

**Lancette piccole:** nuova voce **Ore (24h · giorno/notte)**, indipendente dal cronografo, già calibrata su 24 valori e un giro di 360° al giorno. La precedente scala oraria a 12 ore resta disponibile.

**Only Crono:** nuovo flag nei secondi grandi. Attiva Crono Pro e mantiene la lancetta ferma a zero a riposo; durante la misura conta i secondi crono e al Reset rientra a zero con l'animazione fluida oraria esistente. Ore e minuti grandi continuano a segnare l'ora. Senza flag resta il comportamento collaudato della 2.3. Secondi sempre esclusi dall'AOD.

**Verifiche:** 154 test mirati sui sorgenti e 8 controlli dell'editor superati; esportazione temporanea con due stili, dischi/ombre, calendario, Only Crono e AOD verificata. Catalogo personale ricontrollato: 9 set, nessun aggiornamento. Nessun backup o avvio dell'EXE in ambiente isolato. **Le nuove funzioni 2.4 attendono il tuo test reale sull'S5.** [Guida e dettagli tecnici](EDITOR_2.4.md) · [Inventario dischi](library-analysis/discs-2.4.json) · [Verifiche](validation-editor-2.4.json).

**Eseguibile 2.4 creato e verificato staticamente:** 1.236 risorse incorporate, tutti i 41 moduli Python del pacchetto, entry point e cinque moduli Lua corrispondenti ai sorgenti testati. Catalogo dischi e interfaccia inclusi. Nessun avvio dell'EXE. [Rapporto del bundle](executable-build-2.4.json).

## Novità 2.3

**Decimi Crono Pro fluidi, opzionali:** seleziona la lancetta piccola abbinata a **Decimi crono** e attiva **Movimento Fluido** nella sua scheda. Durante Running segue la frazione del tempo trascorso con target **25 fps**; disattivando il flag mantiene **dieci scatti al secondo**. La lancetta grande dei secondi del cronografo resta sempre a scatti da un secondo; ore/minuti crono restano a scatti. I progetti conservano i flag salvati: se quello dei decimi era già attivo, nella 2.3 diventa operativo. L'anteprima applica la stessa scelta.

**Lettura dei decimi:** nella scheda delle lancette piccole con sorgente **Decimi crono · Start/Stop/Reset** o **Decimi continui** puoi scegliere **Singola cifra** oppure **Frazione completa**. Per i decimi le due letture coincidono sulla scala 0–9 (0,0–0,9 secondi); a 0,456 s la cifra dei decimi è 4 in entrambi i casi. La scelta viene salvata nel progetto, indipendentemente per stile, e conserva scala, calibrazione e flag Movimento Fluido. Con il movimento fluido la lancetta continua a passare fra le tacche: questo selettore non la rende a scatti. Centesimi/Millesimi mantengono le rispettive letture complete o a singola cifra. Il solo aggiornamento del selettore, nella stessa **versione 2.3**, conserva il runtime Lua; le successive protezioni della ripresa sono descritte sotto.

**Aggiornamenti sincronizzati:** il callback dell'animazione aggiorna il clock e subito le lancette, eliminando il timer separato da 100 ms che poteva leggere una fase vecchia. Con un clock monotono disponibile, il callback legge quel clock senza cambiarne l'origine. Il runtime evita aggiornamenti ripetuti dello stesso intervallo e conserva la cache **write-on-change** per lancette e ombre. Non viene inventato un evento firmware `elapsedMs`: si usa `Anim.exec_cb`, già impiegato dal progetto e collaudato sull'S5.

**Tacche nascoste escluse:** quando **Mostra tacche** è disattivato, non si genera né si compila la PNG trasparente `_ticks.png` e non si crea il suo oggetto grafico. Vale per analogico nativo e Crono Pro. Le tacche abilitate, anche in uno stile o nella schermata AOD, rimangono presenti.

**Stop, POST e AOD:** tutte le letture usano lo stesso tempo congelato. I decimi fluidi possono fermarsi fra due tacche; la lettura numerica dei decimi mostra la cifra intera, mentre centesimi/millesimi mostrano le rispettive frazioni complete. Rientri coordinati da **720 ms**, archi calibrati e transizioni orarie conservano il funzionamento precedente. L'AOD interrompe gli aggiornamenti rapidi e mantiene la schermata nativa senza secondi né lancette crono.

**Ore Crono e ripresa AOD — aggiornamento 2.3 del 12 ottobre:** le ore contano le ore intere (scala 0–12: 1 dopo 60 minuti, 2 dopo 120). Nel test precedente sul Bulova l'utente segnalava ore ferme anche dopo un giro completo dei minuti. Il calcolo e i binding del binario risultano corretti; scegliere lo stesso modello del catalogo per ore/minuti crea comunque due oggetti indipendenti. Corretti due punti della ripresa: notifiche di pausa ripetute conservano il primo istante di sospensione; al risveglio le posizioni vengono reinviate una volta anche se il valore è invariato. La seconda protezione copre un eventuale disallineamento del renderer, simulato nei test ma non osservato direttamente sul firmware. **Nuovo test reale superato il 12 ottobre 2026: la lancetta ore Crono funziona correttamente.** La conferma riguarda il funzionamento ottenuto; la causa interna del firmware non è stata misurata. [Analisi Bulova](VERIFICA_BULOVA_ORE_CRONO.md).

**137 test mirati superati**, incluse 22 nuove prove su sospensione, ripresa, cache grafica e modello condiviso per ore/minuti. Conservati i 12 controlli dell'editor del selettore dei decimi. Le prove comprendono compilazioni binarie temporanee, clock diretto/fallback, ombre, riporti, POST, AOD e cambio scena. Catalogo controllato: **9 set personali, 623 modelli**, nessun aggiornamento da integrare. Nessun backup, ZIP dimostrativo o avvio dell'EXE in ambiente isolato. I nuovi rapporti di compilazione indicano la versione effettiva dell'applicazione, correggendo la vecchia etichetta fissa 2.1.

**Versione 2.3 stabile e completa, confermata dall’utente sullo Xiaomi Watch S5 il 12 ottobre 2026.** Il nuovo test reale supera anche la verifica della lancetta ore Crono Pro: tutto funziona correttamente e non sono segnalati errori. Restano confermati decimi fluidi e assenza dei lag precedentemente osservati nei secondi grandi. [Conferme dei test reali](hardware-test-2.3.json). Fps e consumo non sono stati misurati. Questa registrazione aggiorna soltanto i documenti; codice ed eseguibile rimangono quelli testati.

Apri il progetto nella **2.3**, scegli il flag dei decimi, **riesporta lo ZIP** e reinstallalo. [Guida tecnica](EDITOR_2.3.md) · [Test](validation-editor-2.3.json) · [Editor](editor-2.3.json) · [Verifica EXE](executable-build-2.3.json).

**Eseguibile 2.3 creato e verificato staticamente:** 760 risorse, tutti i 40 moduli Python del pacchetto incorporati, entry point e cinque moduli Lua corrispondenti ai sorgenti. Nessun avvio dell'EXE.

## Novità 2.1

**Lancetta piccola · Decimi** è disponibile nella creazione/modifica dei set piccoli, accanto a Ore, Minuti, Secondi, Centesimi e Millesimi. Puoi importare PNG, impostare il pivot e importare o generare l'ombra. Il modello salvato compare nel catalogo delle lancette piccole. **Usa modello** conserva la sorgente e la calibrazione se hai già scelto Decimi continui o Decimi crono; al primo abbinamento propone Decimi continui (0/10, 360°). Per il conteggio Start/Stop/Reset scegli **Decimi crono** e attiva il flag generale Crono Pro. I set principali restano a tre ruoli.

**Cartelle ricordate:** Apri progetto, Salva progetto/Salva con nome, immagini/sfondi, PNG lancette singole, bussole, font, PNG set, ombre set, compilatore, esportazione ZIP e anteprima mantengono ciascuno l'ultima cartella scelta. Le preferenze persistono tra gli avvii in `%LOCALAPPDATA%/S5Studio/dialog-paths.json` (da sorgente: `data/dialog-paths.json`). Annullare non modifica la cartella; se non è più disponibile si usa il percorso predefinito. Salva progetto continua a chiedere il nome a ogni utilizzo.

**Lettura numerica allo Stop:** a destra di **Crono fermo** compare, per esempio, `01:02:03 · Decimi 4 · Centesimi 48 · Millesimi 488`. Ore:minuti:secondi sono il tempo trascorso; le frazioni complete rappresentano tutte lo stesso secondo, in questo caso 0,488 s. Il dato deriva dall'istante congelato che guida le lancette e resta fermo anche con l'anteprima animata attiva. Con i POST appare al termine del loro posizionamento; il Reset lo nasconde. Disponibile per Crono e Crono Pro. Questo è un controllo dell'anteprima del PC, non una nuova garanzia di precisione del clock dell'S5.

Integrato anche **Bulova_lancette_piccole**: **9 set personali, 623 modelli complessivi**. Verificati **56 test mirati e 12 controlli dell'editor**. [Guida 2.1](EDITOR_2.1.md) · [Controlli](validation-editor-2.1.json) · [Verifica EXE](executable-build-2.1.json).

**Eseguibile 2.1 creato e verificato staticamente:** 760 risorse incorporate, 22 moduli Python e file Lua corrispondenti ai sorgenti. Nessun avvio dell'EXE in ambiente isolato.

## Novità 2.0 — Centesimi/Millesimi POST e archi calibrati

**Centesimi (POST)** e **Millesimi (POST)** sono nuove sorgenti delle lancette piccole e richiedono il flag generale **Crono Pro**. Restano alla posizione iniziale durante Running e, allo Stop, raggiungono la lettura acquisita con l'animazione comune da **720 ms a 25 fps**. Puoi usare sei lancette di misura: grande secondi, piccole decimi/minuti/ore e due POST. Il Reset le comprende tutte; l'AOD le esclude. Il flag Movimento Fluido è assente per i POST.

**Creazione set piccoli:** scegli Set lancette → Tipo di set → Lancette piccole. Oltre a Ore, Minuti e Secondi trovi **Centesimi** e **Millesimi**, ciascuna con PNG, pivot e ombra propri, anche generata automaticamente. Salva il set e scegli la grafica dal catalogo della lancetta piccola: **Usa modello** abbina la relativa sorgente POST e richiede Crono Pro nello stesso stile. Se la sorgente è già quella corretta, mantiene la calibrazione; al primo abbinamento propone la frazione completa. I set principali mantengono i tre ruoli precedenti. Integrato anche il nuovo set personale **Bulova**: otto set e 618 modelli totali. Completamento verificato con **30 test mirati e 10 controlli UI**; runtime Lua invariato. [Controlli editor dei set POST](hand-set-post-editor-2.0.json).

**Lettura POST:** frazione completa del secondo (00–99 / 000–999) oppure singola cifra (0–9). Esempio a 12,488 s: 48 e 488 nella lettura completa, 8 e 8 nelle singole cifre. Tutte leggono lo stesso istante di Stop. Nessun nuovo timer rapido durante Running. **La visualizzazione dei millesimi non garantisce precisione di 1 ms:** sul fallback Anim l'istante è campionato ai fotogrammi; durante sospensioni il clock civile ha precisione di un secondo.

**Arco di rotazione personalizzato:** valori iniziale/finale, angoli iniziale/finale e verso orario/antiorario indipendenti. Per tutta la frazione imposta 0 / 99 o 0 / 999. Se la tacca «8» significa 0,800 s, imposta Valore finale 800; il valore 8 nei millesimi completi significa 0,008 s. 30° → 140° percorre 110° in senso orario oppure 250° in senso antiorario; per 110° antiorari usa 140° → 30°. Valori fuori scala fermi agli estremi; Stop e Reset restano entro l'arco. **Mostra inizio**, **Mostra fine** e **Dato reale** facilitano la calibrazione sul canvas, senza cambiare la misura o il progetto. Il giro completo resta disponibile disattivando il flag Arco.

**99 test mirati e 14 controlli UI superati**, incluse esecuzione Lua, compilazione EasyFace temporanea, verifica del grafo finale/manifest interattivo e sei lancette, AOD, tick wrap, pause durante il tocco e due versi dell'arco. Catalogo personale aggiornato con **Longine** e **Bulova**: otto set e 618 modelli. Cataloghi sorgente e `.gitignore` conservati. Nessun backup, ZIP dimostrativo o avvio dell'EXE. Le nuove funzioni POST richiedono il test reale sull'S5.

**Eseguibile 2.0 creato:** 754 risorse incorporate, 20 moduli Python e runtime Lua corrispondenti ai sorgenti testati, verificati staticamente senza avviarlo.

Avvia **S5Studio-2.0-aggiornato.exe**, apri il progetto e riesporta lo ZIP. [Guida tecnica e calibrazione](EDITOR_2.0.md) · [Test](validation-editor-2.0.json) · [Editor](chrono-post-editor-2.0.json) · [Verifica EXE](executable-build-2.0.json).

## Novità 1.9 — Cornici, ellissi e ombre dei livelli

**Forma:** scegli Rettangolare oppure Circolare / Ellittica. Il flag **Riempimento** mostra o nasconde l'interno; **Colore riempimento** e **Colore cornice** sono indipendenti. **Spessore cornice (px)** imposta il bordo; 0 lo elimina. Se togli il riempimento senza aver ancora impostato un bordo, Studio propone una cornice da 2 px, regolabile. Per ottenere un'ellisse imposta larghezza e altezza diverse: i due campi e il ridimensionamento sul canvas sono indipendenti. Cambiare tipo conserva posizione e dimensioni.

**Ombre per Testo, Dato live e Forma:** attiva **Mostra ombra** e scegli colore, opacità 0–100%, spostamento X/Y, sfocatura ed espansione. Sono proprietà del livello: seguono i suoi spostamenti e il suo ordine, si salvano nel progetto e restano indipendenti tra gli stili. Rotazione e arco continuano a funzionare. Anche i nuovi selettori di colore offrono **Nessun colore**.

Le ombre di testo/forme vengono incorporate nelle PNG. Quelle dei numeri live usano immagini dei glifi preparate durante l'esportazione e notifiche reali `dataman`: il valore non viene congelato nell'anteprima. Tutte le ombre restano sotto tutte le cifre, senza nuovi timer o filtri eseguiti sull'S5. Giorni della settimana e mesi mantengono le sorgenti native del calendario. La grafica finale viene ritagliata ai 480 px del quadrante.

**93 test mirati e 15 controlli dell'editor superati**, incluse compilazioni binarie temporanee, confronto tra PNG esportate e anteprima, sensori live con ombre, calendario, AOD e ordine dei glifi. Il runtime Crono/Crono Pro e la sincronizzazione 1.8.1, già collaudata sull'orologio, sono invariati. **Test reale della 1.9 superato**, come certificato dall'utente l'11 ottobre 2026: tutte le implementazioni funzionano benissimo. [Esito reale](hardware-test-1.9.json). Catalogo personale controllato alla consegna: sei set, 612 modelli; nessun aggiornamento. Nessun backup, ZIP dimostrativo o avvio dell'EXE in ambiente isolato.

**Eseguibile 1.9 creato:** 742 risorse incorporate e 19 moduli Python corrispondenti ai sorgenti testati, verificati staticamente senza avviarlo.

Apri il progetto nella 1.9 e riesporta lo ZIP per applicare le nuove proprietà al quadrante. [Guida tecnica](EDITOR_1.9.md) · [Test](validation-editor-1.9.json) · [Editor](layer-effects-editor-1.9.json) · [Verifica EXE](executable-build-1.9.json).

## Correzione 1.8.1 — Sincronizzazione al cambio minuto e ora

Eliminato il salto temporaneo in avanti della lancetta minuti al passaggio dei secondi da 59 a 0. Le notifiche `dataman` di ore, minuti e secondi arrivano separatamente: prima potevano combinare il minuto nuovo con i vecchi 59 secondi. Il nuovo modulo `studio_civil_clock.lua` pubblica un campione coerente; al cambio dell'ora attende anche il nuovo valore delle ore. Vale per le lancette fluide normali e per l'ora civile del Crono Pro, senza aggiungere timer o animazioni.

Il test reale della 1.8 ha confermato l'avanzamento progressivo piacevole dei minuti e ha individuato questo scatto al confine. **Test reale della correzione 1.8.1 superato sullo Xiaomi Watch S5**, come confermato dall'utente il 10 ottobre 2026: il funzionamento è ora perfetto. [Esito riferito dall'utente](hardware-test-1.8.1.json). AOD, conteggio Crono, rientri da 720 ms e flag indipendenti conservano il comportamento precedente.

**Per applicare la correzione:** apri il progetto esistente nella 1.8.1, esporta nuovamente lo ZIP e reinstallalo sull'S5. Non occorre ricreare il progetto o cambiare le impostazioni delle lancette.

**86 test mirati superati. Eseguibile 1.8.1 creato:** 742 risorse incorporate e 16 moduli Python corrispondenti ai sorgenti testati, verificati staticamente senza avviarlo. Set personali controllati: nessun aggiornamento.

[Dettagli e verifiche](EDITOR_1.8.1.md) · [Test](validation-editor-1.8.1.json) · [Verifica EXE](executable-build-1.8.1.json).

## Novità 1.8 — Fluidità separata e schede stabili

Apri il livello **Lancette**, poi la scheda **Lancetta ore**, **Lancetta minuti** o **Lancetta secondi**: ciascuna contiene il proprio flag **Movimento Fluido**. Il selettore comune è stato rimosso. Puoi attivare qualsiasi combinazione. I progetti precedenti conservano la scelta dei secondi; i nuovi flag di ore/minuti partono disattivati.

**Ore e minuti fluidi:** la posizione include i secondi reali, eliminando il salto di un minuto intero. I minuti avanzano di **0,1° al secondo** e le ore di circa **0,0083° al secondo**. La posizione viene calcolata con domini interi precisi dai dati `dataman`, senza aggiungere timer o animazioni a 25 fps. **Secondi fluidi:** resta lo sweep a **25 fps** già collaudato. Ogni ombra segue la propria lancetta con identica geometria.

Il lavoro aggiuntivo previsto è contenuto: ore/minuti sono mossi dalle notifiche dei secondi e non da cicli di ridisegno continuo. Il test reale ha confermato l'avanzamento progressivo dei minuti, ma ha rilevato lo scatto al cambio minuto corretto nella 1.8.1. Il consumo non è stato misurato. La risoluzione angolare del Pointer limita quanto sia visibile un singolo incremento, soprattutto per le ore.

**Crono Pro:** ore/minuti dell’ora seguono i propri flag; i puntatori che misurano il cronografo mantengono il conteggio a scatti e i rientri coordinati già collaudati. **AOD:** i tre controlli sono disabilitati; ore/minuti usano il percorso nativo senza la nuova logica Lua e i secondi restano esclusi. I valori salvati dei flag non vengono cancellati.

**Corretto il ritorno alla scheda Ore dopo Invio o una modifica:** il pannello conserva sia le schede aperte sia quelle chiuse dello stesso livello, oltre alla posizione di scorrimento. Anche Annulla mantiene la scheda corrente.

Superati **70 test mirati e 11 controlli dell’editor**, inclusi esecuzione Lua, indipendenza dei flag, salvataggio/stili, ombre, confronto geometrico, Crono Pro, AOD e compilazione di un binario temporaneo con tre stili misti. Nessun quadrante ZIP dimostrativo o avvio dell’eseguibile. Controllati i set personali: sei set incorporati, **612 modelli**, nessun nuovo aggiornamento.

**Eseguibile 1.8 creato: 741 risorse incorporate e 16 moduli Python corrispondenti ai sorgenti testati**, verificati staticamente senza avviarlo.

[Guida tecnica e limiti](EDITOR_1.8.md) · [Test](validation-editor-1.8.json) · [Verifica EXE](executable-build-1.8.json).

## Correzione 1.7.7 — Secondi dell’ora nell’anteprima

La lancetta piccola impostata su **Secondi completi (0–59)** avanza ora anche con **Movimento Fluido disattivato**, quando è attivo **Simula movimento**: un aggiornamento al secondo. Il difetto era nella sola anteprima, che applicava il tempo trascorso soltanto con il flag fluido attivo. Se cambi manualmente il campo **Secondi** o lo scenario durante la simulazione, il conteggio riparte dal nuovo valore, senza sommare la fase precedente.

**La posizione iniziale era corretta**, come confermato dall’utente: la lancetta indica i secondi scelti nell’anteprima, **30** nello scenario Normale, e non lo zero del cronografo. Per verificare lo zero scegli **Secondi = 0** nella barra della simulazione. La scala completa consigliata resta **Valore iniziale 0 / Intervallo 60 / Angolo iniziale 0° / Rotazione totale 360°**. Il parametro Valore iniziale definisce l’origine della scala, non l’istante di avvio della simulazione.

Pivot, grafica, sorgente nativa `timeSecond`, compilazione delle lancette e runtime Crono/Crono Pro restano invariati. La sorgente esportata continua a seguire i secondi reali dell’orologio; resta esclusa dall’AOD. Nessun valore del progetto personale è stato riscritto. Integrati i nuovi set **Omega moon** e **Omega moon piccole**: sei set personali incorporati e **612 modelli totali**.

**17 test mirati e 15 controlli dell’editor superati**, compresa una compilazione binaria temporanea che verifica sorgente, aggiornamento a 1 Hz, scala, pivot, due stili Crono Pro e assenza dei secondi in AOD. Nessun ZIP dimostrativo, backup o avvio dell’EXE. La segnalazione della posizione è stata chiarita in anteprima; non è stato dichiarato un nuovo test hardware.

**Eseguibile 1.7.7 creato: 740 risorse incorporate e 15 moduli Python corrispondenti ai sorgenti testati**, verificati staticamente senza avviarlo.

[Dettagli](EDITOR_1.7.7.md) · [Test](validation-editor-1.7.7.json) · [Verifica EXE](executable-build-1.7.7.json).

## Novità 1.7.6 — Dato live e selettore colore universale

Seleziona un livello **Dato live** e usa **Orientamento e arco → Rotazione (°) / Arco (°)**: ora puoi inclinare il dato e adattarlo al bordo del quadrante. Anteprima, selezione, salvataggio, stili e immagini di esportazione usano la stessa geometria. Il valore continua ad aggiornarsi dal sensore sull’orologio: non viene trasformato in una scritta fissa. Giorni della settimana e mesi conservano le rispettive etichette inglesi dinamiche. **Raddrizza livello** riporta entrambi i valori a zero.

La casella **Nessun colore** è ora disponibile in **tutte le finestre colore**, incluse lancette generali, testo, forme, Dato live, complicazioni, sfondo e accento degli stili. Nel colore generale delle lancette nasconde **soltanto il tappo centrale**; nelle PNG mantiene i colori originali; nei colori di testo/forme/sfondo rende il riempimento trasparente. Le singole lancette restano configurabili separatamente. Annulla, Ripeti e salvataggio conservano la scelta.

Verificati **81 test mirati e 20 controlli dell’interfaccia**, inclusi aggiornamenti sensore eseguiti in Lua, confronto pixel con l’anteprima, decimali/allineamento, compilazioni binarie temporanee di due stili Crono Pro e di un progetto senza crono, AOD, grafo finale e manifest. Nessun ZIP dimostrativo e nessun avvio dell’eseguibile. Il nuovo rendering numerico Lua trasformato richiede ancora il test reale sul S5; i runtime già collaudati di Crono e Crono Pro restano invariati. Controllati i set personali: quattro set incorporati, nessun nuovo aggiornamento, 607 modelli totali.

**Eseguibile 1.7.6 creato: 730 risorse incorporate e 10 moduli Python corrispondenti ai sorgenti testati**, verificati senza avviarlo.

[Guida e dettagli tecnici](EDITOR_1.7.6.md) · [Test](validation-editor-1.7.6.json) · [Verifica EXE](executable-build-1.7.6.json).

## Novità 1.7.5 — Nessun colore

Nella finestra **Select Color** delle grafiche importate è disponibile la casella **Nessun colore — mantieni i colori originali**. Selezionala e premi **OK** per togliere la ricolorazione da una singola lancetta principale/piccola, da un’immagine o dalla bussola. La grafica mantiene la propria trasparenza e resta visibile con i colori della PNG. Nel pannello compare **Colore originale** quando la tinta è disattivata.

Scegliere un colore nella finestra disattiva automaticamente la casella e applica la nuova tinta. **Annulla** lascia invariati il progetto e la cronologia; il cambio colore supporta Annulla/Ripeti ed è conservato al salvataggio. L’opzione è disponibile sulle grafiche importate; testo e forme continuano a usare il normale colore del componente.

Il controllo dei cataloghi personali ha trovato e integrato **Hamilton Lancette**, con tutte e tre le lancette e le rispettive ombre. La release include ora **quattro set personali**, **12 modelli aggiuntivi**, **19 PNG distinte** e **607 modelli totali**. [Integrazione](hand-set-integration-1.7.5.json).

**Eseguibile 1.7.5 creato; 729 risorse incorporate verificate staticamente**, senza avviarlo. [Verifica EXE](executable-build-1.7.5.json).

**21 test mirati e 10 controlli dell’interfaccia superati**, compresa la vera finestra colore Qt, ripristino dei pixel/trasparenza, salvataggio, esportazione PNG nativa, annullamento e disponibilità di Hamilton su un catalogo utente vuoto. [Verifica](validation-editor-1.7.5.json). Runtime Lua e risorse originali invariati; nessun backup, quadrante dimostrativo o avvio dell’EXE isolato.

## Novità 1.7.4 — Tutti i set modificabili

**Integrati nell’eseguibile:** **Seiko 5 ombra**, **Swatch Orange ombra** e **Swatch orange piccole**. Le nove lancette e le tredici PNG distinte, incluse le ombre, mantengono pivot, spostamenti e impostazioni di generazione. Sono disponibili anche copiando il solo EXE su un nuovo PC. Il catalogo comprende ora **604 modelli**, rispetto ai 595 originali.

Apri **Set lancette**, cerca il nome e premi **Modifica**: ora puoi modificare anche **ogni set del catalogo originale**, incluse le lancette piccole e AOD. Puoi cambiare nome, PNG, pivot, ombre e generazione automatica. Gli stili e le varianti originali sono distinguibili nel nome; i filtri separano principali, piccole, personali/integrati e catalogo originale. I set originali privi dei secondi mantengono i loro ruoli esistenti. **Ripristina** recupera la versione incorporata di un set modificato.

Le modifiche sono persistenti in `%LOCALAPPDATA%/S5Studio/hand-sets/` e hanno precedenza sui valori incorporati, senza duplicare i set. I file originali restano intatti. I quadranti già creati conservano le proprie PNG: per applicare un set aggiornato a un livello esistente scegli nuovamente **Usa modello**. Il comando **Elimina** sui set personali/integrati agisce sul catalogo locale e non sui progetti.

**Controllo automatico a ogni release:** `scripts/package.ps1` esegue, tramite `prepare_runtime.py`, la sincronizzazione dei cataloghi in `data/hand-sets/` e `%LOCALAPPDATA%/S5Studio/hand-sets/` dentro `resources/hand-sets/`. Include sia nuovi set sia aggiornamenti, verifica hash/PNG/pivot e interrompe il packaging se una risorsa è danneggiata. Il catalogo dell’app Windows ha precedenza in caso dello stesso ID; la sincronizzazione non scrive nei cataloghi sorgente. Il controllo è richiamabile anche con `python -X utf8 scripts/sync_hand_sets.py` ed è richiesto dalle istruzioni del progetto a ogni nuova modifica. [Guida](EDITOR_1.7.4.md), [integrazione](hand-set-integration-1.7.4.json).

**Eseguibile 1.7.4 creato e 723 risorse incorporate verificate staticamente**, senza avviarlo. [Verifica EXE](executable-build-1.7.4.json).

**41 test mirati e 38 controlli dell’interfaccia superati**, comprese modifica di tutte le 595 grafiche originali, pivot esterni, abbinamenti, ombre, persistenza, ripristino, disponibilità dei set integrati senza dati utente e integrità delle PNG. Runtime Lua e risorse originali invariati. [Rapporto](validation-editor-1.7.4.json). Nessun nuovo backup, quadrante ZIP dimostrativo o avvio dell’EXE in ambiente isolato.

## Correzioni 1.7.3 — Calendario inglese e allineamento

**Dato live → Giorno settimana:** mostra **MON, TUE, WED, THU, FRI, SAT, SUN**, sempre tre lettere maiuscole. L’anteprima iniziale è **MON**. **Dato live → Mese:** mostra i nomi completi inglesi, da **January** a **December**, come richiesto dall’utente. Font importato, dimensione, grassetto memorizzato, colore, opacità e allineamento si applicano a tutti i nomi. Cifre, decimali e zeri iniziali sono nascosti quando la sorgente è un calendario testuale; restano disponibili per gli altri dati numerici.

Le parole sono rasterizzate sul PC con il font scelto e compilate in un **DataItemImageValues nativo**, collegato a `dateWeek` o `dateMonth`. Il dispositivo seleziona quindi la scritta del giorno/mese effettivo, senza Lua e senza dipendere dalla lingua del telefono. La codifica dei quadranti forniti è `dateWeek: 0=SUN, 1=MON, …, 6=SAT`; i mesi usano valori espliciti `1…12`. [Evidenza del formato](calendar-native-mapping-1.7.3.json). Le anteprime complete e degli stili usano lo stesso testo dell’esportazione. Il normale oggetto **Data DD/MM** conserva il mese numerico; anche le sorgenti che guidano le lancette rimangono numeriche.

Alla selezione di una sorgente calendario il campo viene allargato, solo se necessario, per ospitare tutti i nomi con il font corrente, mantenendolo sul canvas. Le geometrie già salvate non vengono riscritte all’apertura: se un campo esistente è troppo piccolo per il nome più lungo, aumenta la larghezza o riduci il font. La validazione controlla l’intero elenco, non soltanto il nome mostrato nell’anteprima.

**Dato live → Giorno del mese, allineamento Destra:** un giorno come **6** occupa la posizione delle unità di **16**, sul lato destro del campo. Era errata sia l’anteprima, che aggiungeva spazi a destra, sia l’esportazione, che forzava sempre l’allineamento sinistro. Ora Sinistra/Centro/Destra allineano il valore visibile; gli zeri iniziali continuano a produrre **06** quando richiesti. I metadati e il validator verificano anche l’allineamento effettivo del binario.

**22 test mirati e 9 controlli dell’editor superati**, incluse compilazioni binarie temporanee di calendario e allineamenti, associazioni giorno/mese, AOD, font, colore/opacità, anteprime, giorno singolo e conservazione del DD/MM numerico. [Rapporto](validation-editor-1.7.3.json). Nessun quadrante ZIP dimostrativo, nuovo backup o avvio dell’EXE in ambiente isolato. Runtime Crono/Pro e catalogo originale invariati. Le ombre della 1.7.2 sono confermate corrette dall’utente; l’utente ha successivamente confermato che il lavoro della 1.7.3 è ben fatto.

## Correzione 1.7.2 — Ombre tra le lancette

Le lancette principali rispettano ora questo ordine, dal basso verso l’alto:
**ombra ore → ore → ombra minuti → minuti → ombra secondi → secondi → copriperno centrale**.
L’ombra dei minuti può quindi cadere sulla lancetta delle ore; quella dei secondi può cadere sulle lancette di ore e minuti. Prima tutte le ombre venivano disegnate sotto tutte le lancette: si vedevano sul quadrante, ma erano coperte dalle lancette stesse.

La correzione si applica ad **anteprima, miniature degli stili, esportazione nativa e Crono Pro**, sia con ombre originali sia con quelle generate dal software. Nel percorso nativo le singole lancette sono emesse come puntatori separati, con la propria ombra immediatamente sotto: restano gli stessi sei puntatori quando sono presenti tre lancette e tre ombre. La scena Lua crea le immagini nello stesso ordine e conserva gli abbinamenti ombra/lancetta del controller. Pivot, dimensioni, colori, spostamenti, conteggio e animazioni non sono modificati. Il flag **Mostra ombre** continua a nasconderle tutte.

**58 test mirati superati**: verifica dei pixel delle ombre su lancette sovrapposte, miniature, ordine dei figli nella scena Lua realmente eseguita, ombre disattivate, geometria e generazione dei set. Una sola compilazione binaria temporanea verifica ordine, sorgenti, centri e periodi nel formato nativo, incluso AOD senza secondi; nessun quadrante ZIP dimostrativo. Il movimento fluido ordinario riguarda ancora soltanto i secondi; ore/minuti rimangono a 1.000 ms. I due runtime Lua restano invariati. [Rapporto](validation-editor-1.7.2.json). Nessun nuovo backup e nessun avvio dell’EXE in ambiente isolato.

**Il test della correzione 1.7.1 è confermato dall’utente**, che riferisce «il problema è stato risolto». L’utente conferma successivamente «perfetto adesso le ombre sono perfette»: [esito](user-test-1.7.2.json).

## Correzione 1.7.1 — Decimi e visibilità Crono Pro

Il flag **Crono Pro** della lancetta grande dei secondi rimane l’unico selettore del sistema integrato, per ogni stile. Il menu della lancetta piccola sceglie il dato da mostrare:

| Sorgente | Comportamento |
| --- | --- |
| **Decimi di secondo · continui** | Un giro al secondo, indipendente dal cronografo. Continua anche a cronografo fermo e non segue Avvio, Stop o Reset. Non richiede Crono Pro. |
| **Decimi crono · Start/Stop/Reset** | Decimi del tempo misurato dal Crono Pro: zero a riposo, dieci scatti al secondo durante la misura, fermi alla lettura su Stop, azzerati con il rientro fluido al Reset. Richiede il flag generale nello stesso stile. |

Per un cronografo usa **Decimi crono · Start/Stop/Reset**; la voce non introduce una seconda modalità Pro. Entrambe le sorgenti restano escluse dall’AOD. I progetti mantengono le sorgenti salvate, senza conversioni automatiche.

**Corretto il falso messaggio bloccante quando si nascondeva il livello delle lancette grandi.** Il controllo verificava contemporaneamente il flag e la visibilità del livello: occultare la grafica veniva interpretato come disattivare Crono Pro. Ora la modalità dipende dalla configurazione, mentre anteprima ed esportazione omettono la grafica dei livelli nascosti. Le piccole visibili continuano a usare il controller Pro; nascondere/mostrare, anche con Annulla/Ripeti, non azzera il conteggio nell’editor. L’avviso resta corretto se il flag manca davvero nello stile corrente o si tenta di disattivarlo lasciando visibili i decimi crono.

**47 test mirati e 10 controlli dell’editor superati**, inclusi esecuzione della scena Lua con gruppo grande nascosto, conteggio di ore/minuti/decimi, Stop/Reset, persistenza e indipendenza degli stili. I due file runtime Lua sono identici alla 1.7. Nessuna compilazione di quadranti di prova, nessun nuovo backup e nessun avvio dell’EXE in ambiente isolato. [Verifica](validation-editor-1.7.1.json). **L’utente conferma che la 1.7 ha funzionato bene sul proprio dispositivo**; l’utente conferma successivamente che la correzione 1.7.1 ha risolto il problema: [esito](hardware-test-1.7.1.json).

## Novità 1.7 — Genera ombre

Apri **Set lancette**, crea un nuovo set oppure premi **Modifica** su uno dei tuoi set esistenti. Attiva **Genera ombre**: Studio crea subito le PNG mancanti ricavando la sagoma dalla trasparenza delle lancette. Funziona sia per i set principali sia per quelli piccoli. Le ombre importate manualmente vengono conservate; il flag completa soltanto quelle mancanti.

Default: ombra nera, **opacità 45%**, **sfocatura 1,5 px**, **spostamento X +2 / Y +3 px** nelle coordinate della PNG. Puoi regolare opacità (1–100%), sfocatura (0–4 px) e spostamento (−20…20 px). Il pivot automatico segue quello della lancetta, con margini trasparenti quando disponibili, entro 480×480 px. Cambiando PNG, pivot o impostazioni, si aggiorna solo l’ombra automatica. Per una forma fedele usa PNG con sfondo trasparente.

Premi **Salva/Aggiorna set nel catalogo**, poi torna sul livello del quadrante e premi **Usa modello** per applicare anche le ombre. Il flag **Mostra ombre** del livello le rende visibili o nascoste. Disattivare **Genera ombre** rimuove dalla bozza soltanto quelle automatiche; salva e riapplica il modello per aggiornare i livelli già creati. Puoi importare una tua PNG al posto di un’ombra automatica: diventa manuale e non viene più rigenerata. Le PNG originali delle lancette restano intatte e i progetti incorporano le ombre applicate.

**37 test mirati e 32 controlli dell’editor superati**, inclusi set piccoli, pivot, aggiornamento, ombre importate, salvataggio e confronto delle PNG native/Lua. La generazione avviene sul PC e utilizza i componenti ombra esistenti, senza aggiungere timer o nuove API al firmware. Nessun backup, quadrante dimostrativo o test isolato dell’EXE. [Guida](EDITOR_1.7.md), [verifica](validation-editor-1.7.json). **Il test reale 1.6.1 è pienamente superato**, come confermato dall’utente il 9 ottobre 2026; l’utente conferma successivamente che la 1.7 ha funzionato bene: [esito](hardware-test-1.7.json).

## Correzioni 1.6.1

**Nuovi livelli Lancette e Lancetta piccola:** Lunghezza **50%** e Spessore **15 px**. I progetti già salvati conservano i propri valori. Quando premi **Usa modello**, sia nel catalogo originale sia nei set personali, vengono attivate immediatamente entrambe le regolazioni per ogni lancetta applicata, comprese minuti/secondi abbinati e ombre. Il modello usa i valori visibili nei controlli fin dal primo render; non serve modificarli per aggiornare l’anteprima. Anche Crono Pro usa la medesima geometria. Riapplica il modello per attivare questo comportamento su un livello esistente; i suoi valori numerici non vengono azzerati.

Il pulsante attende la decodifica della nuova immagine e i vecchi fotogrammi dell’anteprima animata vengono scartati, evitando che coprano una modifica recente. Il problema era nei flag di regolazione lasciati disattivati dopo l’applicazione del modello: una modifica manuale li attivava soltanto in seguito.

**Dato → Giorno del mese:** lo scenario iniziale **Normale** mostra **15**, per valutare subito l’ingombro di due cifre. Gli scenari limite mantengono i loro dati e lo ZIP continua a usare la data reale del S5.

**26 test mirati e 24 controlli dell’editor superati**, compresi confronto fra primo render e modifica a valori invariati, PNG native/Lua, modelli principali/piccoli, set personali e compatibilità Crono Pro. [Rapporto](validation-editor-1.6.1.json). Nessun nuovo backup, nessun quadrante dimostrativo e nessun avvio dell’EXE in ambiente isolato. **Test reale della 1.6.1 pienamente superato**, confermato dall’utente: [esito](hardware-test-1.6.1.json); i runtime Crono e Crono Pro rimangono invariati.

## Novità 1.6

Nuova sezione **Set lancette** nella barra laterale. Assegna un **nome**, scegli **Lancette principali** oppure **Lancette piccole**, poi importa le PNG nei ruoli Ore, Minuti e Secondi. Per un set principale servono tutte e tre; per le piccole basta una grafica. Ogni PNG deve essere statica, da 1 a 480 pixel per lato, preferibilmente trasparente e rivolta verso le ore 12. Clicca sull’immagine per impostare il pivot, oppure usa le coordinate in pixel. Puoi importare anche le ombre, con pivot e spostamento indipendenti.

Premi **Salva set nel catalogo**. Torna su **Quadrante**, seleziona il livello Lancette e scegli il nuovo nome nel menu delle ore: **Usa modello** abbina automaticamente anche minuti, secondi e ombre. Resti libero di sostituire ogni lancetta separatamente. Per le lancette piccole scegli la grafica dal loro menu; il pivot salvato viene rispettato, mentre la sorgente del dato resta quella scelta nel livello. Puoi modificare, rinominare o eliminare i set dal pannello dedicato.

Il catalogo personale è persistente in **`%LOCALAPPDATA%/S5Studio/hand-sets/`** nell’eseguibile, oppure `data/hand-sets/` avviando i sorgenti. Dalla 1.7.4 i set presenti sul PC di sviluppo vengono integrati automaticamente nelle nuove release; la cartella continua a contenere le modifiche locali. Per trasferire modifiche non ancora incluse in una release puoi copiarla su un altro PC. **Le PNG applicate sono incorporate nei progetti e nell’esportazione:** modificare o eliminare un set non altera i quadranti già salvati. L’importazione singola PNG/SVG rimane disponibile nelle proprietà delle lancette.

**30 test mirati e 18 controlli del nuovo pannello superati**, compresi importazione, pivot, ombre, persistenza e applicazione del set. La 1.6 conserva tutte le funzioni della 1.5, poi incluse nella 1.6.1 collaudata dall’utente. Nessuna modifica al runtime Crono/Pro sul S5. [Guida set lancette](EDITOR_1.6.md), [verifica della release](validation-editor-1.6.json).

## Novità 1.5

Seleziona un livello **Testo, Immagine o Forma** e apri **Orientamento e arco** nelle proprietà. **Rotazione (°)** gira il livello attorno al suo centro: positivo in senso orario, negativo in senso antiorario. **Arco (°)** adatta la grafica al bordo rotondo: 0 mantiene il livello diritto, valori positivi creano un arco superiore e negativi uno inferiore. **Raddrizza livello** azzera entrambi. Il riquadro di selezione segue l’ingombro trasformato; puoi continuare a trascinare, ridimensionare e usare le frecce.

La trasformazione è identica nell’anteprima, negli stili e nello ZIP: viene incorporata nelle PNG, ritagliando la parte oltre i 480×480 px. Anche immagini ingrandite fino a 4.096 px restano supportate. Le immagini a scelta dinamica, come le icone meteo, mantengono la sorgente nativa; ciascuna immagine riceve la stessa trasformazione. Non viene aggiunta logica Lua per queste operazioni. Lancette, bussola, numeri live, Ora/Data e complicazioni numeriche conservano i loro componenti nativi e non espongono questi controlli. Riduci l’arco o l’altezza se il software segnala che la grafica si ripiegherebbe su sé stessa.

**Forma:** scegli **Rettangolare** o **Circolare** nelle proprietà. Il passaggio al cerchio mantiene il centro e usa dimensioni uguali; puoi poi ridimensionarlo. La scelta è indipendente per stile e supporta Annulla/Ripristina.

**Catalogo lancette:** gli otto nomi cinesi presenti sono tradotti in inglese, compresi cinque nomi di stile e due nomi autore. Grafiche, ID, pivot, ombre e abbinamenti sono conservati; i nomi originali restano disponibili nei dati di provenienza. [Rapporto traduzioni](catalog-english-1.5.json).

**22 test mirati superati**, inclusa una compilazione temporanea con due stili, AOD, Crono Pro, sensori nativi e icone meteo trasformate. Controllo visivo di rotazione e dei due versi dell’arco superato. Nessun quadrante dimostrativo, nessun nuovo backup e nessun avvio EXE in ambiente isolato. [Guida](EDITOR_1.5.md), [verifica](validation-editor-1.5.json). Il test reale della **1.4.1 è confermato dall’utente il 9 ottobre 2026**; le trasformazioni sono poi incluse nella release 1.6.1, il cui test reale è stato confermato dall’utente.

## Correzione 1.4.1

**L’anteprima Crono Pro mostra subito le dimensioni impostate**, anche aprendo un progetto senza modificare i controlli. Nel primo NASA analizzato, Lunghezza minuti 10% generava correttamente una grafica di 5×46 px. L’anteprima usava invece la geometria analogica originale di 40×480 px finché non venivano modificati i controlli, dando un’idea sbagliata della misura esportata.

Il renderer dell’anteprima usa ora le stesse viste `pro_views` dell’esportazione Lua, inclusi pivot, colori e ombre. **La geometria nello ZIP resta invariata:** tutte le 12 PNG delle lancette/ombre e le due scene Lua rigenerate dal nuovo progetto NASA sono byte per byte identiche al pacchetto creato dall’utente dopo la regolazione. La prova riproduce anche i controlli iniziali minuti 10% e spessore 5 senza regolazioni attivate. Le anteprime complete e degli stili usano lo stesso renderer.

**Movimento Fluido durante l’ora normale:** il flag del gruppo analogico riguarda soltanto la grande dei secondi; non abilita il movimento fluido sulle grandi di ore e minuti. Il Crono Pro mantiene il conteggio a scatti e i rientri coordinati sempre fluidi da 720 ms, indipendenti dal flag. Il runtime resta invariato.

**30 test mirati superati**, inclusi anteprima al primo render e dopo una modifica, quattro combinazioni di regolazione, compilazioni temporanee, varianti e AOD. Il binario nativo verifica secondi a 25 fps e ore/minuti al periodo normale di 1.000 ms. [Analisi del NASA](nasa-geometry-analysis-1.4.1.json), [verifica](validation-editor-1.4.1.json). Nessun nuovo backup, nessuna prova EXE isolata e nessun quadrante dimostrativo.

Apri il progetto con **S5Studio-1.4.1.exe**: vedrai subito la dimensione esportata. Modifica Lunghezza/Spessore per ottenere la misura desiderata, poi genera lo ZIP. Non serve toccare un controllo per risvegliare l’anteprima.

## Novità 1.4

**Crono Pro più lento:** preparazione e Reset passano da **480 a 720 ms**, riducendo la velocità di un altro terzo rispetto alla 1.3. Il tempo resta comune e deterministico, con rientri orari, simultanei, target 25 fps e annullamento immediato in AOD. Anche la simulazione usa 720 ms. A parità di durata, una lancetta che percorre più gradi ruota più velocemente: questa differenza rimane per conservare il completamento simultaneo del gruppo; la 1.4 rallenta tutti i percorsi di un terzo.

**Anteprime della mod:** il confronto del materiale NASA recuperato con tutte le **39 cartelle** del corpus trova **33 configurazioni disponibili e 133 temi**, tutti con anteprime nella cartella `_preview/`. Le PNG NASA della 1.3 contengono già tutte le lancette; la mod le estrae senza modificarle. Nel binario cambia soltanto l’ID, che diventa `L00000000001`. Le configurazioni online esaminate non contengono oggetti `App`, mentre le nostre lancette Pro sono gestite da una scena Lua `App`: il comportamento del renderer della mod resta da confermare.

La 1.4 usa PNG complete in `resources/_preview/`, riferimenti statici nel manifest e in `editor.config.json`, mappa `formats` e risorse `Image` conformi agli esempi. Il riferimento `previewAni` ai WebP con un solo fotogramma viene rimosso. Un validator controlla questi riferimenti prima dell’esportazione. Le capacità, il template e i livelli del quadrante operativo non vengono alterati da questa correzione dei metadati.

**La correzione della preview nella mod richiede il prossimo test reale:** la cartella non include il database del catalogo locale né il codice dell’app. Non consente di dimostrare che la mod usi le PNG statiche anziché ricostruire una preview ignorando Lua. Nome locale e controllo capabilities dipendono ancora dal percorso di importazione della mod. Analisi: [ANALISI_UPLOADER_1.4.md](ANALISI_UPLOADER_1.4.md), [rapporto tecnico](local-uploader-analysis-1.4.json). Guida: [EDITOR_1.4.md](EDITOR_1.4.md).

**25 verifiche mirate superate**, comprese una compilazione temporanea, integrità delle anteprime e rifiuto dei riferimenti incoerenti. Nessun nuovo backup e nessun avvio EXE in ambiente isolato. [Rapporto di verifica](validation-editor-1.4.json).

Per il test: apri il progetto nella 1.4, esporta un nuovo ZIP e importalo sul telefono. Usa il nuovo pacchetto e verifica le anteprime dello stile normale e dello Stile 2; aggiornare soltanto l’EXE non modifica il pacchetto già installato.

## Novità 1.3

La 1.3 aveva portato i rientri da 320 a 480 ms e rasterizzato tutte le lancette prima della codifica delle anteprime native. Il test reale conferma il funzionamento del Crono Pro, ma la mod mostra ancora una preview con il solo sfondo. [Esito reale](hardware-test-1.3.json). La 1.4 allinea i metadati delle anteprime al catalogo online e rallenta ulteriormente le transizioni.

## Novità 1.2

**Rientri Crono Pro sempre in senso orario**: preparazione allo zero e Reset del gruppo usano il percorso orario, anche quando è più lungo. Restano sincronizzati, fluidi per 320 ms con target 25 fps; conteggio a scatti e annullamento immediato in AOD. La simulazione usa lo stesso criterio. Sono gestite anche scale parziali o con rotazione inversa: il rientro fisico resta orario.

**Ogni stile possiede i propri livelli.** Nel pannello **Livelli e proprietà → Stile in modifica** scegli la variante. Duplica uno stile, poi aggiungi, cancella, nascondi, trascina, riordina e modifica le sue immagini, lancette, sorgenti o complicazioni: gli altri stili non vengono alterati. Non serve più il flag “Modifica soltanto questo stile”. “Sfondo da immagine” sostituisce lo sfondo dello stile selezionato, senza lasciare l’immagine coperta dal quadrante principale.

I progetti precedenti vengono convertiti in memoria conservando l’aspetto di ogni stile. Il salvataggio usa lo **schema 3**, con risorse di tutti gli stili; salva una copia per conservarne una apribile nelle versioni precedenti. L’AOD rimane una schermata comune abbinata agli stili. Il compiler genera risorse, anteprime reali e complicazioni da ciascuna lista indipendente. Guida: [EDITOR_1.2.md](EDITOR_1.2.md).

Il **primo test reale Crono Pro 1.1 è superato**, con fluidità confermata dall’utente. Sorgenti, risorse ed EXE 1.1 sono conservati nel [backup verificato](stable-baseline-1.1.json); il crono separato mantiene il core 1.0. Il test reale della 1.2 è pienamente superato: [conferma dell’utente](hardware-test-1.2.json). Verifica PC: **127 test automatici e 100 controlli dell’editor superati**. Rapporti: [validation-editor-1.2.json](validation-editor-1.2.json), [executable-build-1.2.json](executable-build-1.2.json). Nessuna prova EXE in ambiente isolato; viene consegnato solo l’eseguibile.

## Novità 1.1 — Crono-Pro

Nuovo flag **Crono Pro** nelle proprietà della lancetta grande dei secondi, disattivato per default. Attivo: Riposo → Prepara allo zero → Avvia → Stop → Reset fluido e ritorno all’ora corrente. Le piccole possono usare **Decimi crono**, Minuti Crono e Ore Crono. Durante il conteggio il flag Movimento Fluido viene ignorato: secondi e decimi avanzano a scatti; nei rientri tutto il gruppo usa obbligatoriamente un’animazione comune da 320 ms, target 25 fps. Il runtime aggiorna soltanto gli angoli cambiati e usa 100 ms con i decimi, 1.000 ms negli altri casi. In AOD interrompe i rientri, nasconde la scena e usa l’AOD del progetto, sempre senza secondi o Lua.

Il **Crono separato 1.0 rimane distinto e conserva il runtime collaudato**. I decimi continui già funzionanti mantengono la propria voce; Decimi crono è la nuova voce legata allo stato Pro. Per rispettare i livelli, l’analogico Pro viene disegnato nella scena Lua, ricevendo l’ora tramite dataman; i secondi hanno un solo controller. Guida: [EDITOR_1.1.md](EDITOR_1.1.md).

Verifica PC: **112 test automatici superati**, compilazioni temporanee con varianti/AOD e **91 controlli nell’editor da sorgente**. **Primo test reale Pro 1.1 superato**, con rientro fluido confermato dall’utente; consumo non misurato. [Evidenza riferita dall’utente](hardware-test-1.1.json). L’EXE 1.0 e il backup verificato restano conservati. Nessun quadrante dimostrativo prodotto e nessuna prova EXE in ambiente isolato.

## Novità 1.0

Il test prolungato della 0.11 ha mostrato minuti Crono fermi dopo il primo giro dei secondi, pur con sorgenti corrette. La 1.0 sostituisce gli App separati con **un’unica scena Lua per stile**: ore, minuti e secondi condividono lo stesso conteggio, timer e tap. La sincronizzazione non dipende più dalla condivisione della VM tra widget separati. **Test reale 1.0 pienamente superato**, confermato dall’utente l’**8 ottobre 2026**: il crono funziona su tutte le lancette piccole. I test automatici coprono anche il passaggio del minuto e dell’ora, Stop/Reset e il giro oltre 12 ore. Verifica PC: **95 test passati** e **84 controlli dell’editor**, compresa la compilazione reale con due stili e AOD. Guida: [EDITOR_1.0.md](EDITOR_1.0.md); evidenza fisica riferita dall’utente: [hardware-test-1.0.json](hardware-test-1.0.json).

## Crono

La **1.0 è il riferimento stabile collaudato sull’Xiaomi Watch S5 M2530W1**. Il cronografo è locale al quadrante: non controlla l’app Cronometro del sistema. Le sorgenti `studioChronoSecond`, `studioChronoMinute` e `studioChronoHour` sono abbinamenti del nostro runtime Lua, non nuovi identificatori di sensori Xiaomi.

### Come abbiamo ottenuto il funzionamento completo

1. **Packaging Lua reale.** `s5studio/native.py` genera un App EasyFace tramite **Shape 34**. `s5studio/lua_runtime.py::write_scene` scrive un solo entry point `app/lua/studio_vN_scene.lua` per stile normale, insieme a `studio_core.lua`, PNG delle lancette e ombre. EasyFace compila queste risorse nel binario; non basta aggiungere uno script esterno allo ZIP.
2. **Un solo stato per tutte le lancette.** Nella 0.11 ogni lancetta era un App separato. `_G` e la cache di `require` non garantivano uno stato comune fra questi App: nei test con VM isolate, il tap avviava soltanto l’App dei secondi. La 1.0 registra tutte le viste tramite `core:add` nello stesso entry point; ore, minuti e secondi condividono certamente il medesimo runtime. La separazione effettiva delle VM del firmware non è stata misurata, ma non è più necessaria per il funzionamento.
3. **Tempo trascorso, non conteggio dei callback.** Il runtime seleziona una sola sorgente temporale: `lvgl.tick_get`, altrimenti `/proc/uptime`, altrimenti `os.time`. Memorizza l’istante di partenza e calcola il tempo trascorso dal clock; un callback in ritardo non perde secondi. La sorgente non viene cambiata durante una misura, per evitare di mescolare origini temporali diverse. `os.time` ha precisione di un secondo e può risentire delle correzioni dell’ora; il test positivo non identifica quale clock sia disponibile sul singolo firmware.
4. **Un timer e un calcolo comune.** Un `lvgl.Timer` da **40 ms**, cioè un obiettivo di 25 aggiornamenti al secondo, aggiorna tutte le lancette Crono. Dallo stesso `elapsedMs` ricava secondi `/ 1.000`, minuti `/ 60.000` e ore `/ 3.600.000`. Senza Movimento Fluido applica la parte intera; poi applica il modulo 60, 60 o 12, rispettivamente. `Pointer:set {value=...}` trasforma il valore nell’angolo definito da intervallo, rotazione e pivot del progetto. Una sola lista aggiorna grafica e ombra insieme.
5. **Un solo tap per il quadrante.** Una superficie trasparente 480×480 usa `lvgl.EVENT.PRESSED`, con `CLICKED` come fallback. La sequenza è **Azzera → Avvia → Ferma → Azzera**. Stop memorizza il tempo e ferma tutte le viste; Reset azzera insieme ore, minuti e secondi. Le lancette non devono gestire tap o timer indipendenti.
6. **Pause senza scomparsa delle lancette.** `pageOnPause` sospende gli aggiornamenti senza nascondere le immagini durante una pausa temporanea legata al tocco. Se necessario, un tap viene conservato fino a `pageOnResume`. Lo schermo spento/AOD sospende il disegno e ignora i tap; al ritorno, se il crono è in movimento e il clock è disponibile, il tempo trascorso viene ricalcolato. Ricreare la VM o cambiare quadrante azzera lo stato: non è prevista persistenza del cronometro.
7. **Coerenza di esportazione.** Manifest interattivo, script, PNG e binario sono verificati insieme. `build-report.json` registra hash, entry point e `crossWidgetVmSharingRequired=false`; il validator controlla tutte le viste e un solo gestore del tap per stile. Secondi e App Lua sono esclusi dall’AOD. Il packaging conserva capability e record protetti del template. `hardwareVerified:false` nei rapporti automatici significa che il validator non esegue prove fisiche: la conferma manuale della 1.0 è documentata separatamente.

Per un sottoquadrante da 60 secondi/minuti usa valore iniziale 0, intervallo 60 e rotazione 360°. Per le ore su scala 12 usa 0/12 e 360°. L’angolo iniziale dipende dalla grafica, dal pivot e dallo zero del sottoquadrante; un vecchio progetto conserva le sue impostazioni.

**Decimi attuali, già funzionanti e collaudati sull’S5:** `studioDecisecond` usa `root:Anim`, con durata 1.000 ms e ripetizione continua. Il callback ricava la fase del giro e aggiorna lancetta/ombra; il flag fluido abilita i valori intermedi. L’utente ha confermato nuovamente il funzionamento l’8 ottobre 2026. Questa funzione è indipendente da Start/Stop/Reset. La futura voce **Decimi crono** estende il comportamento già disponibile, collegandolo ad Avvio/Ferma/Azzera e allo stesso tempo trascorso delle altre lancette; non sostituisce i decimi continui dei progetti esistenti.

Gli esempi primari mostrano [Pointer con timeSecond](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand9Pro/PointerTest/app/lua/main.lua) e [rotazione animata di immagini](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand8Pro/AnalogTimeAnimated/app/lua/image.lua). La prova dell’utente sull’S5 conferma il nostro runtime 1.0; gli esempi pubblici su altri modelli non certificano da soli ogni nuova funzione.

L’evoluzione proposta, con lancetta grande condivisa fra ora e crono, è descritta nel [piano di fattibilità](PIANO_CRONO_INTEGRATO.md). Il codice 1.0 rimane invariato in questa fase; il [punto di ripristino](stable-baseline-1.0.json) conserva sorgenti e risorse con hash verificabili.

## Novità 0.11

**Prima prova reale 0.11 positiva**, confermata dall’utente il **7 ottobre 2026**: decimi, tap Crono e secondi funzionanti, compilazione in pochi secondi. Un test successivo più lungo ha rilevato minuti Crono fermi; le ore non sono state provate per un’ora. La correzione è nella 1.0. Evidenza aggiornata: [hardware-test-0.11.json](hardware-test-0.11.json).

- Esportazione: notifica collegata alla reale fine del worker, pulsante riabilitato anche dopo errori, aggiornamento finale senza render di tutte le anteprime. L’animazione della UI è sospesa durante la build e usa intervalli dopo il render. Il report esterno registra tempi delle fasi, pubblicazione, pulizia e ritardo della notifica UI.
- Decimi: animazione LVGL ciclica da 1000 ms, indipendente da `tick_get` e `/proc/uptime`. Anche un vecchio intervallo 60 copre la rotazione configurata in un secondo; scala consigliata 0/10 e rotazione 360°.
- Cronografo: tap esteso al quadrante e fallback `os.time` se i clock monotoni non sono disponibili. Questo fallback ha precisione di un secondo e risente della sincronizzazione dell’ora. Tap e secondi Crono sono confermati sull’S5; la sincronizzazione dei minuti viene corretta nella 1.0.

**Esito iniziale delle correzioni 0.11:** risolti nel test reale i decimi fermi e il cronografo non avviato della 0.10. L’utente conferma inoltre la compilazione in pochi secondi. Restano conservati i rapporti storici della 0.10; il successivo difetto dei minuti è documentato nella 1.0. Dettagli: [EDITOR_0.11.md](EDITOR_0.11.md).

Verifica PC: 90 test della suite completa e 14 test mirati dopo l’ultimo feedback sul tap (91 test distinti); 84 controlli nell’editor, senza prova EXE isolata. [Rapporto](validation-editor-0.11.json). Il runtime gestisce anche un tap durante una pausa temporanea, senza nascondere esplicitamente le lancette; i tocchi in AOD vengono ignorati.

## Novità 0.10

- **Movimento Fluido** per secondi: 25 fps / periodo nativo 40 ms, applicato anche alle ombre. Secondi, decimi e componenti Lua sono sempre esclusi in AOD, in tutti gli stili.
- Lancette piccole: **Decimi di secondo** (un giro al secondo), **Ore Crono**, **Minuti Crono**, **Secondi Crono**. Framework Lua con tap sul sottoquadrante: Avvia → Ferma → Azzera. Pulsante di simulazione nell’editor.
- **Ctrl + clic** sul canvas o nei livelli per selezione multipla; drag e frecce muovono il gruppo. Sei allineamenti al quadrante, distanze relative conservate, un solo Annulla.
- ZIP con `build-report.json`: hash degli script incorporati nel binario, interattività verificata, frequenze native e controllo AOD. `interactive=true` solo con componenti Lua.
- EXE personale autonomo, con runtime Lua incorporato. Nessun nuovo quadrante dimostrativo consegnato.

**Cronografo e decimi 0.10: verificati sul PC, ma il successivo test firmware è fallito. Vedere le correzioni 0.11 sopra.** Sono richiesti un clock monotono accessibile e una VM condivisa fra i sottoquadranti. Senza clock il cronografo resta azzerato. Durante AOD il disegno e il timer sono sospesi, mentre il tempo trascorso continua. Cambio quadrante o nuova VM azzerano il conteggio. Non è collegato all’app cronometro dell’orologio.

Verifica finale 0.10: **85 test passati**, **81 controlli UI nell’EXE**, **707 risorse incorporate verificate** e compilazione isolata senza tool esterni; il binario Lua con due stili e AOD coincide con quello prodotto dai sorgenti. Rapporti: [validation-editor-0.10.json](validation-editor-0.10.json), [executable-build-0.10.json](executable-build-0.10.json).

Guida e fattibilità: [EDITOR_0.10.md](EDITOR_0.10.md). Rapporti: [validation-editor-0.10.json](validation-editor-0.10.json), [executable-build-0.10.json](executable-build-0.10.json).

## Novità 0.9

- Clicca nella preview **Pivot · clicca sulla grafica applicata** per impostare X/Y nel file originale. La croce mostra il perno attuale; per le lancette piccole il clic disattiva il perno automatico. Preview valida anche per PNG/SVG personalizzati e ombre abbinate.
- Lunghezza e spessore funzionano sulle lancette importate: trasformazione condivisa da anteprima, bitmap FPRJ e binario. I progetti precedenti mantengono la propria geometria finché modifichi un controllo; le immagini originali rimangono intatte. Lunghezza 1–100% del lato più corto del livello, spessore 1–100 px della parte visibile più larga.
- Menu delle sorgenti senza alias duplicati, con spiegazioni in hover. **Ora completa** è distinta da **Cifra delle ore · unità / decine**: alle 14, rispettivamente 14, 4 e 1.
- Nuovo livello **Bussola analogica**, con 10 modelli: otto grafiche osservate e due rose complete composte. Pivot al centro, sensore `systemSensorCompass`, intervallo 360°, rotazione −360°. Puoi importare un PNG/SVG, ricolorarlo, ridimensionarlo e usarlo nelle varianti. Il campo **Bussola °** modifica solo la simulazione.
- Zoom anteprima 50–400%, Ctrl + rotella e centratura della selezione. Spazio + trascina o tasto centrale per la panoramica. Zoom e scorrimento non modificano le coordinate o i 480×480 px esportati.
- Eseguibile personale completo, verificato in una cartella contenente soltanto l’EXE. Nessun nuovo quadrante dimostrativo prodotto per questa versione.

Verifica finale: **77 test automatici passati**, **66 controlli UI nell’eseguibile reale**, 705 risorse incorporate controllate e compilazione senza toolchain/template esterni. Il binario della fixture temporanea coincide con quello dei sorgenti, anche con due stili e AOD. Rapporti: [validation-editor-0.9.json](validation-editor-0.9.json) e [executable-build-0.9.json](executable-build-0.9.json).

Il **test reale NASA della 0.8 è superato**, come confermato dall’utente. Il progetto `projects/NasaS5.s5faceproj` resta intatto e la sua anteprima 0.9 è identica a quella della 0.8. Il successivo test reale della 0.9 è stato dichiarato completamente positivo dall’utente, inclusa la bussola analogica; evidenza in docs/hardware-test-0.9.json. Guida: [EDITOR_0.9.md](EDITOR_0.9.md).

### Perché data/ è nel .gitignore?

`.gitignore` decide cosa viene salvato nel repository, non cosa entra nell’eseguibile. La **0.8 da sola non era completa**: richiedeva data, template e compilatore accanto al file. La **0.9 preparata per questo progetto** include tutte queste risorse tramite `scripts/prepare_runtime.py` e `scripts/package.ps1`; esclude progetti, recuperi automatici, corpus originale e ADB. Non cambiamo le regole personali del gitignore.

Un clone dei soli sorgenti non contiene automaticamente il corpus personale né il compilatore: per ricostruire l’EXE completo servono `data/watchface-library.json`, i relativi asset (rigenerabili dai 39 quadranti con `scripts/create_watchface_library.py`), il template collaudato e EasyFace 4.23 verificato. Lo script interrompe il packaging se qualcosa manca. Questa copia incorpora risorse dell’utente per uso personale; provenienza e avvisi sono in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Novità 0.8

- Avvio in finestra massimizzata; label **Version 0.8**.
- **Salva progetto chiede sempre il nome**, anche dopo il primo salvataggio. Annullare conserva percorso e modifiche; il recupero automatico resta senza dialoghi.
- Voce in hover evidenziata nei menu, anteprima delle lancette senza applicare la scelta.
- Catalogo completo dei 39 quadranti: **595 modelli**, 526 bitmap madri distinte, **108 modelli piccoli** e 407 abbinamenti con ombre. Comprende risorse nei gruppi/slot, AOD e rotazioni segmentate; tutti i 1.310 puntatori del corpus sono inventariati.
- Scegli il modello **ore** e premi **Usa modello**: abbina minuti e secondi disponibili dello stesso set. Minuti e secondi possono poi essere cambiati separatamente. Le ombre corrispondenti si importano automaticamente; il flag **Mostra le ombre abbinate** ne controlla la visibilità. Un set privo di secondi li disattiva; puoi riattivarli e scegliere la grafica.
- Le lancette piccole ruotano dall’estremità visibile e scalano rispetto alla lunghezza effettiva della grafica. Il perno è identico nella preview e nel binario; puoi usare anche un pivot manuale.
- `.gitignore` ampliato conservando byte per byte tutte le righe precedenti.

Guida: [EDITOR_0.8.md](EDITOR_0.8.md). Esempio: `projects/S5_Studio_Lancette_0.8.s5faceproj`; ZIP: `S5_Studio_Lancette_0.8_TEMPLATE.zip`. Verifica: **66 test passati**, compilazioni EasyFace reali e prove DOM. Il successivo test reale NASA della 0.8 è stato superato dall’utente.

## Novità 0.7

- Hover sui modelli: anteprima grafica, senza applicare la scelta. Il riquadro vuoto non carica immagini mancanti.
- Immagini fino a 4096 px per lato, coordinate negative, scala percentuale e centratura. Anteprima ed esportazione conservano solo la finestra 480×480.
- Frecce: 1 px; Maiusc + frecce: 10 px, per qualsiasi livello selezionato. Sono rispettati campi di testo, menu, blocco, stili, AOD e annulla.

Guida: [EDITOR_0.7.md](EDITOR_0.7.md). Esempio: `projects/S5_Studio_Ritaglio_0.7.s5faceproj`; ZIP: `S5_Studio_Ritaglio_0.7_TEMPLATE.zip`. Verifica: 58 test passati e prove DOM nell’eseguibile reale.

## Funzioni dell’editor

- Elimina un livello con × sulla riga, con Elimina nelle proprietà o con Canc; Annulla ripristina anche cancellazione e ordine.
- Trascina una riga del pannello livelli sopra/sotto un’altra: le righe in cima sono davanti. Anche le complicazioni seguono questo ordine nell’anteprima e nel binario.
- Colore per livello, tinta facoltativa sulle immagini e colori distinti di ore, minuti e secondi, anche su modelli PNG/SVG.
- Ridimensiona le immagini con le maniglie agli angoli, larghezza/altezza o Riempi quadrante / Adatta al bordo. Il mantenimento delle proporzioni è disattivabile.
- Opacità da **0 a 100**, a passi di 1: 0 invisibile, 100 completamente visibile. Le immagini originali sono conservate nel progetto.
- Le nuove complicazioni sono livelli con **solo il valore**, senza cornice, etichetta o icona preimpostata. Spostale sul canvas e scegli le informazioni nella scheda Complicazioni; le decorazioni restano facoltative. I progetti precedenti conservano la propria grafica.
- Lancetta piccola indipendente: posizione, dimensioni, grafica, pivot, colore, sorgente dati, intervallo e angoli. Puoi duplicarla per più sottoquadranti. Secondi/minuti dell’ora, batteria o altri dati del quadrante guidano la rotazione; dalla 0.10 le voci Crono usano il framework Lua interattivo descritto sopra.
- Menu a tendina con scelta confermata tramite clic o Invio; passaggio del mouse e frecce non cambiano il valore salvato.

Avvio e istruzioni: [EDITOR_0.6.md](EDITOR_0.6.md). Esempio: `projects/S5_Studio_Crono_0.6.s5faceproj`; ZIP: `S5_Studio_Crono_0.6_TEMPLATE.zip`.

## Creare un quadrante

1. Scegli Analogico, Digitale o Salute. Importa uno sfondo PNG/JPEG/WebP/BMP/SVG e posiziona i livelli sul canvas.
2. Seleziona Lancette. Regola dimensioni, lunghezza, spessore, tacche e secondi. Per ogni lancetta scegli un modello dalla galleria o importa PNG/SVG; pivot e bitmap vengono incorporati nel progetto. Sono disponibili **595 modelli** dai tuoi quadranti, con autore, provenienza, ombre abbinate e set, comprese lancette piccole e indicatori. Le immagini personalizzate devono puntare alle ore 12.
3. Apri Varianti grafiche e duplica lo stile, fino a cinque. Cambia colore, sfondo, immagine o proprietà del livello. “Modifica soltanto questo stile” consente anche lancette diverse per variante.
4. Apri Complicazioni e aggiungi cinque o più slot: **fino a 16 nel progetto Studio**, un limite applicativo, non il massimo certificato del firmware. Ogni slot nuovo mostra solo il valore; posizione, dimensioni, colore e ordine sono modificabili come per gli altri livelli. Cornice, etichetta e unità sono facoltative. Seleziona le informazioni offerte all’utente e quella iniziale. La simulazione cambia soltanto la preview, senza cambiare il default del progetto.
5. Le **58 sorgenti dati** osservate comprendono pulsazioni, passi, SpO₂, sonno, movimento, meteo con icone, temperature, umidità, vento, bussola, quota, pressione, batteria e calendario. Sono canali del framework dei quadranti, non accesso arbitrario ai sensori grezzi. Tre sorgenti di testo formattato presenti nei campioni non sono ancora esportabili come testo dinamico; vedi il rapporto.
6. Configura AOD: è comune agli stili, senza secondi e senza slot. Salva `.s5faceproj`, poi Esporta ZIP e scegli la cartella. Apri esportazione mostra il pacchetto pronto.

I progetti incorporano immagini e font, leggono schema 1/2 e salvano schema 2. Riordino, drag, duplicazione, annulla/ripristina e recupero automatico sono disponibili. Nome e ID sono modificabili in Progetto; i nuovi progetti ricevono un ID personale per ridurre collisioni con Suit and tie.

## Prova pronta

- Eseguibile attuale: **S5Studio-2.1.exe** (autonomo).
- Esempio storico 0.8 conservato: **S5_Studio_Lancette_0.8_TEMPLATE.zip** e **projects/S5_Studio_Lancette_0.8.s5faceproj**.
- ZIP: **S5_Analogico_Libero_0.5_TEMPLATE.zip**.
- Progetto: **projects/S5_Analogico_Libero_0.5.s5faceproj**.
- Istruzioni: [PROVA_S5_0.5.md](PROVA_S5_0.5.md).

Il test ha cinque colori e cinque slot indipendenti, inizialmente Passi, Pulsazioni, Temperatura, Bussola e Meteo; ogni slot offre quindici scelte. Le anteprime sono render del progetto con valori simulati. Il binario usa sorgenti native aggiornabili. Lo ZIP 0.5 è stato testato con successo dall’utente e rimane conservato. La 0.9 non aggiunge altri pacchetti dimostrativi: crea e salva il tuo progetto dall’applicazione.

L’originale Suit and tie fallisce anch’esso capabilities nel percorso locale della mod, mentre il catalogo e Modifica funzionano. La lista locale può quindi continuare a mostrare un nome generico o nessuna immagine. Non è stata dimostrata una soluzione tramite Regione.

## Packaging e verifica

Ogni build produce ZIP, `resource.bin`, `.face` identico, anteprime, progetto, FPRJ con bitmap, log e rapporto. Il packaging usa il template verificato: **187 file protetti e 8 directory conservano i record ZIP originali**, incluse capability e hashCode. Sostituisce binario e 28 anteprime; rigenera description, manifest, uidmap ed editor insieme alle risorse nuove. Preservare questi ultimi metadati invariati descriverebbe ancora Suit and tie, rendendo incompleto un quadrante modificabile.

È stata compilata e validata anche una configurazione con cinque slot, cinque stili e tutte le 58 sorgenti più Nessuna in ciascuno slot (22.524 voci ZIP); rapporto in `docs/stress-all-sources-0.5.json`. Il validator confronta CRC, file protetti, ID, offset, temi, UID, layout, sorgenti, opzioni, gruppi e anteprime. Rifiuta incoerenze prima dell’esportazione. La firma strutturale locale non è una firma crittografica Xiaomi e non certifica la verifica capabilities della mod.

L’analisi di `quadranti/` copre **39 cartelle e 7.513 file**, senza eseguire contenuti ricevuti. Inventari, hash e metadati: [catalogo](library-analysis/inventory.md). Ferrari è attribuito a HaloX78, come confermato dall’utente, e non trattato come OEM Xiaomi.

Dettagli: [analisi e correzioni 0.5](ANALISI_QUADRANTI_E_CORREZIONI_0.5.md), [analogico e slot](ANALOGICO_VARIANTI_COMPLICAZIONI.md), [stato](STATO_IMPLEMENTAZIONE.md), [analisi iniziale del template](RAPPORTO_TEMPLATE_FUNZIONANTE.md).

## Sviluppo e CLI

```powershell
python -m pip install -r requirements-dev.txt
python main.py
python -m pytest -q
python main.py ui-smoke --screenshot docs/screenshots/ui-test.png
python main.py build projects/S5_Analogico_Libero_0.5.s5faceproj --compiler tools/easyface-4.23/Compiler.exe --output build/prove
python main.py apply-template progetto.s5faceproj quadrante_funzionante.zip output-template
python main.py apply-template progetto.fprj quadrante_funzionante.zip output-template
python main.py validate-template quadrante_funzionante.zip S5_Analogico_Libero_0.5_TEMPLATE.zip
```

`apply-template` riconosce i FPRJ esportati da Studio e ricostruisce anche stili/slot dal progetto incorporato, controllando gli hash dei sorgenti. Per FPRJ esterni supporta immagini, cifre, liste di immagini e lancette; altri widget sono rifiutati quando non è possibile rigenerare metadati coerenti.

CSS: `npm ci` e `npm run build` in `frontend/`. Desktop personale autonomo: `scripts/package.ps1`, con preflight dei 708 file tramite `scripts/prepare_runtime.py`. Controllo rapido degli hash del bundle: `scripts/verify_bundle.py`. Su richiesta dell’utente, dalla 0.11 non si esegue più la prova dell’EXE in una cartella isolata. L’app non richiede Node. Gli archivi storici fino alla 0.8 in `deliverables/` escludono compilatore e template; per la 1.5 viene prodotto soltanto l’EXE completo richiesto. Vedere [provenienza e licenze](../THIRD_PARTY_NOTICES.md).

## Workflow delle prossime release

Su richiesta dell’utente dell’8 ottobre 2026, **non creare nuovi backup di regressione**. Aggiornare README, guida della versione e rapporti con modifiche e risultati effettivi dei test. Eseguire le verifiche pertinenti alle parti modificate, ampliandole soltanto quando necessario; creare soltanto l’eseguibile richiesto. Verificare staticamente risorse e codice incorporati, senza avviare l’EXE in ambiente isolato. Non creare quadranti dimostrativi salvo stretta necessità. I backup già esistenti restano documentati.
