# S5 Studio 0.11

**Esito aggiornato:** dopo la prima prova positiva, un test più lungo ha mostrato minuti Crono fermi a zero oltre il primo minuto. Start/Stop/Reset, secondi e decimi funzionano; le ore non sono state provate per un’ora. La 1.0 corregge la sincronizzazione con una sola scena Lua. Vedere [EDITOR_1.0.md](EDITOR_1.0.md). Le conferme iniziali riportate sotto restano come storia della prova.

Apri `S5Studio-0.11.exe` o `Avvia_S5_Studio.cmd`. L’EXE personale contiene UI, librerie, template, compilatore e runtime Lua; non richiede cartelle accanto. I progetti 0.10 si aprono senza cambiare grafiche, pivot o valori salvati. Non sono stati modificati i progetti NASA dell’utente.

**Test reali sull’orologio Xiaomi Watch S5 M2530W1: tutti superati.** Il **7 ottobre 2026** l’utente ha confermato il funzionamento perfetto dei quadranti Crono e decimi, dell’applicazione e della compilazione, che ora termina in pochi secondi. Il movimento fluido era già stato confermato. Evidenza aggiornata: [hardware-test-0.11.json](hardware-test-0.11.json). I problemi della 0.10 descritti sotto sono la storia della diagnosi, risolta nella prova reale della 0.11.

## Risultati e diagnosi

Il 7 ottobre 2026 l’utente ha confermato sull’S5 il movimento fluido dei secondi della 0.10. I decimi rimanevano a zero; nel successivo test `NASA_S5_new_crono.s5faceproj` il tap non avviava le lancette Crono. Evidenza: [hardware-test-0.10.json](hardware-test-0.10.json). Il pacchetto conteneva effettivamente Lua, bitmap e manifest interattivo: un controllo strutturale riuscito non dimostra l’esecuzione sul firmware.

Nel codice 0.10 entrambe le funzioni si fermavano se `lvgl.tick_get` e `/proc/uptime` erano indisponibili. Questa è una causa plausibile dei sintomi, non una misura delle API presenti sull’orologio. Nel NASA dei decimi era rimasto anche l’intervallo 60. Nel NASA Crono le scale erano corrette, ma il centro del quadrante principale non apparteneva ad alcuna delle tre aree rettangolari di tap.

L’utente ha poi precisato di aver provato **sia il centro sia i sottoquadranti**. L’estensione dell’area di tap, da sola, non spiegava il fallimento della 0.10. Il successivo test reale della 0.11 ha confermato il funzionamento del cronografo; non è stata misurata quale sorgente di clock abbia scelto il firmware.

## Decimi indipendenti dal clock esportato

La 0.11 usa `root:Anim` con percorso lineare, durata 1000 ms e ripetizione infinita. La fase proviene dal motore LVGL; non dipende da `tick_get`, file procfs, CPU time o conteggio delle chiamate del timer. Una sola animazione aggiorna lancetta e ombra insieme. La scelta deriva dalle API mostrate negli esempi pubblici [ImageBarTest](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand9Pro/ImageBarTest/app/lua/main.lua) e [AnalogTimeAnimated](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand8Pro/AnalogTimeAnimated/app/lua/image.lua). Il funzionamento dei decimi è ora confermato dal test reale sull’S5 dell’utente.

Impostazioni consigliate: **valore iniziale 0, intervallo 10, rotazione totale 360°**. Mantieni il tuo angolo iniziale e pivot, che stabiliscono l’allineamento alla grafica. Il runtime percorre l’intervallo configurato in un secondo: anche i progetti con vecchio intervallo 60 compiono l’intera rotazione. Senza Movimento Fluido mostra dieci posizioni; con il flag usa valori intermedi, nei limiti del rendering del firmware. Anteprima PC e runtime applicano la stessa scala. Il ciclo parte all’avvio dell’animazione: non si dichiara sincronizzato alla frazione UTC del secondo dell’orologio.

## Cronografo e tap

Le aree Crono diventano a tutto quadrante: il centro del NASA può avviare il conteggio. Il callback `PRESSED` (con `CLICKED` se PRESSED è assente) esegue la sequenza **Avvia → Ferma → Azzera** e lo stato è condiviso tra i sottoquadranti nella stessa VM Lua. Un tap successivo all’azzeramento avvia una nuova misurazione. La logica non è collegata al cronometro di sistema. L’evento di pressione compare anche negli [esempi analogici pubblici](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand8Pro/AnalogTimeAnimated/app/lua/main.lua).

L’utente ha inoltre osservato che nella 0.10 tutte le lancette piccole sparivano durante il tocco e ricomparivano al rilascio. Il vecchio codice nascondeva i root a ogni `pageOnPause` e ignorava i tap durante la pausa: il sintomo è compatibile con questa sequenza, ma l’ordine degli eventi sul S5 non è stato misurato. Nella 0.11 la pausa temporanea ferma gli aggiornamenti senza nascondere esplicitamente la grafica. Un tap ricevuto mentre la pagina è in pausa, ma lo schermo è acceso, viene conservato e applicato una sola volta alla ripresa. L’AOD/schermo spento nasconde i root e cancella ogni tap pendente. Il test Lua copre entrambe le sequenze; il successivo test reale ha confermato il funzionamento perfetto della versione Crono.

Il clock viene scelto una sola volta, nell’ordine `lvgl.tick_get`, `/proc/uptime`, `os.time`. L’ultima API compare nell’esempio pubblico [TempControl](https://github.com/m0tral/MiWatchLuaWatchfaces/blob/master/MiBand9/TempControl/app/lua/main.lua). Il fallback `os.time` ha **precisione di un secondo**; il flag fluido non può ricavare frazioni mancanti. Una correzione dell’ora può alterare il conteggio: i salti indietro non fanno diminuire il tempo già misurato, ma i salti avanti rimangono una limitazione. Senza alcun clock supportato il cronografo resta azzerato.

Il funzionamento dei quadranti Lua, dei tap e delle lancette Crono è confermato sull’S5 dall’utente. Le tre lancette native delle ore/minuti/secondi non dipendono da questo framework. Decimi e componenti Crono sono esclusi dall’AOD in tutti i temi. La pausa temporanea ferma gli aggiornamenti senza nascondere esplicitamente la grafica; AOD e schermo spento nascondono i root. Al ritorno il cronografo in movimento legge nuovamente il clock. Cambio quadrante o nuova VM azzerano lo stato.

## Fine esportazione e tempi

Una copia del NASA usato nel test è stata compilata sul PC in circa **7,2 s**, con pubblicazione di circa **0,065 s** e pulizia di **0,03 s**. Rapporti storici: [export-diagnostic-0.10.json](export-diagnostic-0.10.json), [export-qt-diagnostic-0.10.json](export-qt-diagnostic-0.10.json). Dopo le correzioni 0.11, l’utente ha confermato che anche la compilazione dall’applicazione termina in **pochi secondi**: il ritardo osservato nella 0.10 risulta risolto nella sua prova.

La cartella finale viene pubblicata dopo la validazione; la pulizia dei file temporanei segue la pubblicazione. L’editor 0.11 attende `QThread.finished` per uscire dallo stato occupato e invia una notifica leggera, senza rifare tutte le anteprime. Anche gli errori riabilitano Esporta ZIP. Risposte vecchie non possono ripristinare “Compilazione…”. L’anteprima animata usa un intervallo successivo al render ed è sospesa durante la build; riprende automaticamente se era attiva. Le frequenze delle lancette esportate non cambiano.

Il **build-report.json esterno**, nella cartella compilata, aggiunge `exportTiming`: tempi delle fasi, `fileReadySeconds`, `totalReadySeconds`, `publishSeconds`, `cleanupSeconds`. Se esporti dall’editor, include `guiNotificationDelaySeconds`. Il report dentro lo ZIP conserva le verifiche su Lua, manifest, hash e AOD; non include tempi che si conoscono soltanto dopo aver chiuso e pubblicato l’archivio.

## Procedura di installazione verificata

1. Avvia la 0.11 e apri il progetto NASA dei decimi o `NASA_S5_new_crono.s5faceproj`.
2. Per i decimi scegli la sorgente Decimi, scala 0/10 e 360°; per Crono conserva 12/60/60 e 360°. Mantieni pivot e angoli già regolati.
3. Esporta un nuovo ZIP e installalo sull’S5. Un vecchio ZIP contiene ancora il runtime 0.10. Se l’uploader riutilizza un quadrante precedente, assegna un ID nuovo dalla scheda Progetto.
4. Verifica il giro dei decimi in un secondo. Per Crono tocca il centro o un sottoquadrante: Avvia, attendi almeno cinque secondi, Ferma, poi Azzera. Prova anche il ritorno dall’AOD.

Per questa versione viene consegnato soltanto l’EXE. Le compilazioni di verifica sono fixture temporanee, non nuovi quadranti dimostrativi.

Verifica PC: suite completa di **90 test passati**, seguita da **14 test mirati passati** dopo l’ultimo feedback sul tap (91 test distinti complessivi); **84 controlli nell’editor QtWebEngine** e **707 risorse incorporate controllate**. Per richiesta esplicita dell’utente l’EXE 0.11 non è stato eseguito in un ambiente isolato: `scripts/verify_bundle.py` controlla soltanto il contenuto e gli hash. Rapporti: [validation-editor-0.11.json](validation-editor-0.11.json), [executable-build-0.11.json](executable-build-0.11.json).
