# S5 Studio 1.0

Avvia **S5Studio-1.0.exe** oppure **Avvia_S5_Studio.cmd**. La 1.0 apre i progetti precedenti e conserva immagini, pivot, colori, scale e posizioni salvati. L’EXE personale contiene UI, cataloghi, template e compilatore, come la 0.11.

## Correzione del cronografo

Dopo la prima conferma positiva della 0.11, un test più lungo sull’S5 ha mostrato che Start/Stop/Reset e i secondi funzionavano, ma i minuti restavano a zero dopo un giro completo dei secondi. Le ore non erano state provate per un’ora. Le sorgenti erano impostate su Ore Crono, Minuti Crono e Secondi Crono.

La 0.11 esportava un App/script per ogni lancetta. Il modulo comune presumeva che `_G` e la cache di `require` fossero condivisi fra gli App: questa ipotesi non è garantita dal formato. Tre VM separate riproducono nei test lo stesso sintomo: il tap raggiunge l’App superiore, avvia i secondi e lascia ore/minuti nello stato azzerato. Il calcolo dei minuti non era il problema. L’organizzazione effettiva delle VM sul firmware non è stata misurata; la correzione elimina la dipendenza da quella organizzazione.

La **1.0 genera un solo App/script per stile**, con tutte le lancette Lua registrate nella stessa scena. Un solo clock, un solo timer e un solo gestore del tap aggiornano lo stesso tempo trascorso. Ogni lancetta conserva grafica, ombra, pivot, posizione, colore e regolazioni individuali. I decimi conservano la loro animazione ciclica indipendente dal cronografo. Secondi e componenti Lua restano esclusi dall’AOD.

| Lancetta | Valore dopo 61 secondi | Valore dopo 1 ora | Scala consigliata |
| --- | ---: | ---: | --- |
| Secondi Crono | 1 | 0 | 0/60, rotazione 360° |
| Minuti Crono | 1 | 0 | 0/60, rotazione 360° |
| Ore Crono | 0 | 1 | 0/12, rotazione 360° per un sottoquadrante da 12 ore |

Il runtime calcola secondi, minuti e ore dallo stesso tempo trascorso, rispettivamente diviso per 1.000, 60.000 e 3.600.000 millisecondi. Il flag fluido abilita le frazioni dove il clock le fornisce; senza flag avanza alle unità intere. Il fallback `os.time` conserva precisione di un secondo. L’angolo iniziale resta quello regolato sulla tua grafica. La scala salvata determina l’angolo effettivo: non viene modificata automaticamente aprendo un vecchio progetto.

## Ordine dei livelli

Immagini, testi e forme fra le lancette Lua vengono inclusi nella scena nello stesso ordine, mantenendo sovrapposizioni e trasparenze. Le lancette principali e gli altri elementi nativi sopra/sotto il gruppo conservano il proprio ordine.

Se inserisci un elemento dinamico nativo, come una complicazione o una bussola, **tra** le lancette Lua, l’esportazione ti chiede di spostarlo sopra o sotto il gruppo: il compilatore evita di alterarne silenziosamente l’ordine o la sorgente. Il progetto NASA controllato ha le tre lancette Crono consecutive e le lancette principali sopra di esse; non richiede modifiche all’ordine.

## Validazione e prova

La release supera **95 test automatici**, **84 controlli dell’interfaccia da sorgente** e la verifica statica dei **707 file incorporati nell’EXE**. Il Lua incorporato coincide con il sorgente sottoposto ai test. I risultati e gli hash sono in [validation-editor-1.0.json](validation-editor-1.0.json) e [executable-build-1.0.json](executable-build-1.0.json).

Il validator verifica un solo entry point Lua per ogni stile che ne ha bisogno, tutte le lancette e sorgenti previste, un solo gestore del tap e l’assenza di Lua/secondi nell’AOD. `build-report.json` espone `interactive.luaArchitecture`, l’elenco degli ID per scena e `crossWidgetVmSharingRequired=false`. Gli ZIP precedenti restano verificabili con i loro rapporti originali.

I test Lua avanzano il clock a 59,999 s, 60 s, 61 s, 3.599,999 s, 3.600 s e oltre 12 ore, verificando anche Stop/Reset e il fallback a un secondo. Le compilazioni di verifica sono temporanee. Per richiesta dell’utente non si esegue l’EXE in un ambiente isolato: il controllo del bundle verifica file e hash senza avviarlo.

Per il test sull’orologio, apri il tuo progetto nella 1.0 ed **esporta un nuovo ZIP**. Installa il nuovo pacchetto e avvia Crono: dopo 65 secondi i minuti devono indicare 1 e i secondi circa 5. Stop deve fermare tutte le lancette; il tap successivo deve azzerarle insieme. Le ore sono verificate con clock simulato; il nuovo payload deve ancora essere confermato sul dispositivo.
