# S5 Studio 1.1 — Crono-Pro

Avvia **S5Studio-1.1.exe** o **Avvia_S5_Studio.cmd**. L’eseguibile personale rimane autonomo. Il Crono separato usa lo stesso `studio_core.lua` della 1.0, senza modifiche; il nuovo backend `studio_core_pro.lua` si attiva soltanto con **Crono Pro**.

## Configurazione

1. Apri il progetto e salva una copia con nome diverso, per esempio NASA_Pro. Conserva progetto e ZIP 1.0 funzionanti.
2. Seleziona il livello Lancette e attiva **Crono Pro** nelle proprietà della **Lancetta secondi**. Il flag abilita anche la lancetta grande dei secondi; non serve una nuova voce di abbinamento per quella lancetta. Dall’interfaccia il flag si applica a tutti gli stili.
3. Per le piccole scegli **Ore Crono**, **Minuti Crono** e **Decimi crono · Crono Pro**. Scale consigliate: ore 0/12, minuti 0/60, decimi 0/10, rotazione 360°. Mantieni pivot e angolo iniziale che identificano lo zero grafico.
4. **Movimento Fluido** rimane salvato, ma viene ignorato nel conteggio Pro. I rientri sono sempre fluidi anche con il flag disattivato. A riposo il flag della lancetta grande regola invece i secondi dell’ora.
5. Prova il ciclo con il pulsante centrale di simulazione, poi **Esporta ZIP** e installa il nuovo pacchetto.

Senza Pro resta **Avvia → Ferma → Azzera**, con i secondi Crono sulle piccole. **Decimi di secondo · un giro al secondo** conserva l’animazione continua indipendente, già collaudata. La nuova voce **Decimi crono** è distinta e richiede Pro.

## Sequenza Pro

| Stato | Lancetta grande secondi | Piccole Crono | Tap |
| --- | --- | --- | --- |
| Riposo | Ora corrente | Zero | Prepara: sweep allo zero |
| Posizionamento | Rientro fluido | Zero | Ignorato durante il rientro |
| Pronto | Zero | Zero | Avvia |
| In movimento | Secondi Crono interi | Decimi/minuti/ore interi | Stop lettura |
| Fermo | Tempo registrato | Tempo registrato | Reset del gruppo |
| Rientro | Sweep verso i secondi correnti dell’ora | Sweep allo zero | Ignorato durante il rientro |

Reset termina in Riposo; la misura successiva richiede di nuovo Prepara e Avvia. Non è il cronometro dell’app di sistema. Cambio quadrante, ricreazione della VM o cambio scena Pro azzerano il conteggio.

## Risparmio energetico selettivo

In Running un solo timer usa **100 ms** con Decimi crono, altrimenti **1.000 ms**. I valori sono quantizzati: dieci posizioni al secondo per i decimi, una al secondo per i secondi, unità intere per minuti/ore. Il runtime non riscrive un angolo identico. Lancetta e ombra ricevono lo stesso valore. Nessuna interpolazione del conteggio viene attivata dal flag fluido.

Preparazione e Reset condividono un’animazione da **320 ms**, con obiettivo di **25 aggiornamenti grafici al secondo**. Tutte le viste Crono, compresa la grande, seguono la stessa fase; una lancetta già a zero resta a zero. La destinazione della grande viene aggiornata durante il rientro per riagganciare l’ora corrente anche al passaggio 59/0. Gli angoli seguono il percorso breve e le ombre seguono le madri.

Questo riduce le scritture e le rotazioni rispetto al conteggio continuo a 25 fps. Il consumo del Pro sull’S5 non è ancora misurato: il target non certifica frame effettivamente mostrati o un consumo massimo.

## Scena, geometrie e clock

Il Pro usa un solo App/entry point per stile. Per rispettare livelli e ombre, **l’intero livello analogico Pro viene disegnato nella scena Lua**: ore/minuti principali ricevono l’ora via `dataman`, mentre i secondi hanno un solo controller che sceglie ora o crono. Non si cambia la sorgente di un puntatore nativo e non si sovrappongono due controller. Il percorso classico e gli altri elementi mantengono la compilazione prevista dalla 1.0.

PNG, colori, lunghezza/spessore, pivot e offset vengono conservati. Tutte le ombre principali precedono le loro grafiche madri. Immagini, testi e forme statiche interposte mantengono il proprio ordine nella scena; un elemento dinamico nativo interposto deve essere spostato sopra o sotto il gruppo, come indicato dall’errore di esportazione.

I puntatori Pro usano valori interi con una scala interna fino a 1.000, entro il dominio 0–65.535. Così anche il rientro da un solo minuto o da una sola ora ha posizioni intermedie, senza richiedere al firmware di accettare valori frazionari. Questa scala è interna: gli intervalli impostati nell’editor rimangono 12/60/10.

Il clock preferito è `lvgl.tick_get`, poi `/proc/uptime`; il tick LVGL a 32 bit viene esteso al wrap. Se non disponibili, il Pro usa la **fase millisecondi di un’animazione LVGL**, della stessa famiglia di API che muove già i decimi. Non incrementa il tempo in base al numero di callback e non inventa un sensore. Sampler, rientro e filtro tap hanno root distinti per evitare conflitti fra animazioni.

Nel fallback, `os.time` integra il tempo a schermo spento con **precisione di un secondo** e sensibilità alle correzioni dell’ora. La precisione subsecondo attraverso una sospensione non è certificata. Senza clock civile lo spegnimento ferma la misura, evitando tempi inventati. Il fallback include un sampler di fase aggiuntivo, oltre al timer del conteggio. Clock e precisione effettivi richiedono conferma sul firmware; il runtime stampa il clock selezionato all’inizializzazione.

## AOD e ciclo di vita

`ScreenStateChangedCB` interrompe le animazioni, sospende i timer e nasconde **l’intera scena**, incluse immagini statiche e lancette. Preparazione interrotta diventa Pronto; Reset interrotto diventa Riposo. Callback successivi non completano rientri nascosti e i tap AOD vengono ignorati. Al ritorno si disegna la posa coerente e, se in movimento, si ricalcola il tempo disponibile.

L’AOD del progetto è compilato separatamente e conserva la propria grafica. **Tutti i secondi e tutti gli App Lua sono esclusi dall’AOD**, anche nelle varianti. Una pausa temporanea da tocco non nasconde la scena; conserva al massimo un tap, salvo quelli avvenuti durante le transizioni. Un rientro sospeso da un tocco riparte dalla posa raggiunta, senza saltare alla destinazione; l’ingresso in AOD lo annulla invece subito. Cambio scena ferma vecchi timer/animazioni; i vecchi callback non controllano la nuova scena.

## Validazione e prova

`build-report.json` registra `interactive.chronoPro`: runtime/stati, quantizzazione obbligatoria, periodi 100/1.000 ms, rientri 320 ms/25 fps, scritture soltanto su variazioni e cancellazione AOD. Il validator confronta entry point, ID/sorgenti, script/PNG realmente incorporati, manifest e rapporto; rifiuta rapporti alterati. Capability e record protetti rimangono quelli del template.

**112 test automatici superati**: compilazioni temporanee reali con due stili/AOD, decimo/minuto/ora, Stop/Reset, valori interi dei puntatori, pause da tocco durante i rientri, fallback, wrap, cambio scena e geometrie importate. I **91 controlli dell’editor da sorgente** includono flag, nuova sorgente, ciclo e cancellazione AOD. Rapporti: [validation-editor-1.1.json](validation-editor-1.1.json), [executable-build-1.1.json](executable-build-1.1.json).

**Crono separato 1.0 e decimi continui già collaudati sull’S5; primo test Pro 1.1 superato, con fluidità confermata dall’utente.** Rientri orari e livelli indipendenti sono aggiornati nella [1.2](EDITOR_1.2.md). Verificare Prepara/Avvio, lettura dopo 65 secondi, Stop, Reset simultaneo e AOD durante entrambi i rientri. Nessun test dell’EXE in ambiente isolato e nessun quadrante dimostrativo consegnato: le compilazioni di verifica sono temporanee.

Il [backup 1.0](stable-baseline-1.0.json) e il vecchio EXE restano conservati. I progetti classici omettono il nuovo flag falso nel salvataggio; una copia con Pro e Decimi crono richiede 1.1. Per tornare a 1.0 usare progetto/ZIP precedenti conservati.
