# Disco lunare giornaliero — S5 Studio 2.5

> Nella **2.6**, il calendario del disco è condiviso con i nuovi campi Giorno/Mese/Anno di **Simula l'orologio**. Cambiare il giorno aggiorna insieme datario e disco lunare. Corretta anche l'interferenza nell'anteprima con Crono Pro attivo. Il runtime S5 resta quello della 2.5. [Guida aggiornata](EDITOR_2.6.md).

## Utilizzo con il tuo disco Longines

1. Avvia `S5Studio-2.5.exe` e apri **Dischi**.
2. Cerca **Longines Moonphase - 59-day disc** e premi **Aggiungi**. La PNG fornita è incorporata, 480 × 480, pivot centrale 240 / 240; ridimensionala e spostala come ogni disco.
3. Mantieni la sorgente **Fasi lunari · 59 posizioni (giornaliero)**. I valori corretti sono già impostati: iniziale 0, intervallo 59, angolo iniziale 0°, rotazione 360°, correzione 0 giorni.
4. Metti sopra al disco la grafica del quadrante con la finestra trasparente. Alla data di riferimento la posizione è 0: con la PNG Longines e angolo 0° una luna è rivolta verso l'alto, l'altra verso il basso. Allinea l'**Angolo iniziale** alla finestra effettiva; usa **Rotazione antioraria** se richiesto dalla grafica. L'angolo iniziale non cambia il calendario.
5. **Mostra riferimento** nell'anteprima permette di calibrare il disco in luna piena. La **Correzione giorni**, da −58 a 58, aggiunge o sottrae passi rispetto al riferimento. **Data attuale** ripristina la data del PC. Puoi provare date consecutive e verificare i passaggi di mese/anno; questa scelta di anteprima non viene esportata.
6. Salva e riesporta il tuo progetto. I livelli di ogni stile restano indipendenti; i vecchi progetti non vengono convertiti automaticamente a questa nuova sorgente.

La **Data di riferimento** predefinita è **2026-09-26**, giorno della luna piena del 26 settembre 2026 alle 16:49 UTC secondo [US Naval Observatory](https://aa.usno.navy.mil/calculated/moon/phases?date=2026-09-01&nump=8). Il software usa la data civile locale, senza calcolare l'ora astronomica esatta. Se scegli un altro riferimento, scegli un giorno di luna piena e verifica l'allineamento nella finestra.

## Meccanismo e precisione

La posizione è `(giorno attuale − giorno di riferimento + correzione) modulo 59`, con valori interi 0–58. Un passo giornaliero misura `360 / 59 = 6,1016949°`; il giro completo dura 59 giorni. Due lune opposte producono due cicli da circa 29,5 giorni. La [Fondation Haute Horlogerie](https://www.hautehorlogerie.org/en/watches-and-culture/watchmaking-knowledge/encyclopedia/moonphases-complications) descrive questo meccanismo tradizionale e la sua approssimazione astronomica: nel tempo serve correggere la fase. Non è un'epemeride e non garantisce la precisione o il meccanismo esatto di uno specifico calibro Longines.

La posizione viene ricalcolata dalla data, non incrementata in memoria: l'AOD, i giorni di inattività e una nuova installazione non fanno perdere scatti. Un cambio della data locale modifica coerentemente la posizione. Non è necessario mantenere un timer attivo tutto il giorno.

| Voce del menu dischi | Significato |
| --- | --- |
| Fasi lunari · 59 posizioni (giornaliero) | Contatore civile indipendente, continuo attraverso mesi e anni |
| Fasi lunari native · 8 stati | Sorgente firmware `dateMoon`, otto fasi discrete; su un disco con due lune propone 0 / 8 / −90° / 180° |
| Giorno lunare | Sorgente firmware che riparte a 1 al mese lunare; non equivale al contatore continuo da 59 posizioni |

**Dato live → Fasi lunari** mantiene la sorgente nativa a otto stati. I dischi **Immagini per valore** mantengono le proprie sequenze; la nuova sorgente giornaliera si usa con **Disco rotante**.

## Runtime e prestazioni

`studio_moon_disk.lua` è separato dai moduli Crono/Crono Pro: non usa il loro elapsed, tap, timer o animazione a 25 fps. Ogni disco si collega ai canali `dateYear`, `dateMonth`, `dateDay` in formato Q8 e ricava il giorno gregoriano, compresi anni bisestili e secoli. Il calendario nativo prevale su `os.date`, evitando conflitti di fuso orario; `os.date('*t')` viene usato soltanto come fallback quando il calendario nativo è incompleto e la funzione è disponibile sul firmware.

Poiché anno, mese e giorno arrivano separatamente, un timer da **200 ms** raggruppa le notifiche. Attende una revisione stabile, applica la posizione e si sospende; non esegue polling continuo né rotazioni animate. Anche riattivazione e ripresa attendono un calendario coerente. Scritture identiche sono eliminate durante le notifiche ordinarie; alla riattivazione la posa viene reinviata una volta per riallineare il renderer. Disco e ombra ricevono lo stesso valore. Non viene introdotto alcun codice sensore fittizio.

Il modulo gestisce `ScreenStateChangedCB`, pausa, ripresa e distruzione conservando i callback già presenti. In AOD il disco eventualmente inserito è una posa statica: aggiornamento all'attivazione, nessun timer periodico. Una variazione della data durante la stessa permanenza in AOD viene mostrata alla successiva attivazione. I secondi e il cronografo restano esclusi dall'AOD come prima.

L'architettura limita il lavoro alla data e a poche scritture; questo non costituisce una misura strumentale di consumo o FPS. Il nuovo modulo deve ancora essere verificato sul dispositivo reale.

## Esportazione e verifiche

Le scene Lua conservano ordine dei livelli, PNG, pivot, ombre e impostazioni separate per stile. I dati nativi dentro una scena Lua seguono i vincoli di ordinamento già applicati dal validatore dell'editor. Lo ZIP mantiene la chirurgia sul template, include il modulo, imposta `interactive=true` e registra `interactive.moonDisc` nel `build-report.json`.

Il validatore confronta i byte del modulo, i binding di ogni disco e stile, data di riferimento, correzione, scala e angoli. Verifica anche che il disco non sia registrato fra le lancette del cronografo. Il controllo semantico ricostruisce correttamente il flag AOD dal progetto incorporato.

I test coprono tutte le 59 posizioni, date precedenti al riferimento, offset, riporti mensili/annuali, bisestili, ordine delle notifiche, scritture ripetute, pausa/ripresa, AOD, indipendenza da tutti i tap e callback del Pro, alterazioni del modulo e della calibrazione. Due compilazioni EasyFace temporanee verificano Pro con più stili e AOD, e una scena con il solo modulo lunare in AOD. L'editor viene provato dai sorgenti; l'eseguibile viene ispezionato staticamente senza avviarlo. [Rapporto completo](validation-editor-2.5.json).

## Lancetta datario

Per il sottoquadrante del tempo solare, scegli **Ore (24h · giorno/notte)** sulla lancetta delle ore e **Minuti giorno (0–59)** sulla lancetta dei minuti. Quest'ultima usa la sorgente nativa `timeMinute`, con valore iniziale 0, intervallo 60 e giro di 360° per ora; alle 14:37 indica 37. Non segue Start, Stop o Reset del cronografo. Il nome precedente Minuti completi è sostituito soltanto nel menu delle lancette piccole; i progetti salvati mantengono lo stesso dato.

In **Set lancette → Lancette piccole → Datario** puoi importare una PNG con pivot e ombra, anche generata automaticamente. Il modello viene proposto nel catalogo delle lancette piccole. **Usa modello** imposta `dateDay`, valore iniziale 1, intervallo 31, angolo 0° e giro 360°; la tacca 1 corrisponde all'angolo iniziale, la tacca 31 precede il ritorno alla tacca 1. Puoi ricalibrare verso e angolo. Applicare nuovamente un modello datario mantiene la calibrazione già presente su `dateDay`.

Per un arco, imposta le estremità 1 e 31: l'intervallo è 30 perché indica la distanza fra i due estremi. Il primo abbinamento su un elemento già configurato ad arco conserva gli angoli dell'arco. Il calendario del firmware gestisce i mesi da 28, 29, 30 e 31 giorni; non serve un timer Lua o Crono Pro. Il ruolo Datario è riservato ai set piccoli; i tre ruoli dei set principali restano ore/minuti/secondi.
