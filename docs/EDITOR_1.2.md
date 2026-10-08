# S5 Studio 1.2

Avvia **S5Studio-1.2.exe** oppure **Avvia_S5_Studio.cmd**. L’eseguibile incorpora il runtime personale completo e resta autonomo. Il primo test reale del **Crono Pro 1.1** è superato, con fluidità confermata dall’utente; la 1.2 aggiunge rientri orari e livelli indipendenti per ogni stile.

## Creare una variante indipendente

1. Apri il progetto e salva una copia con un nuovo nome.
2. In **Varianti grafiche**, seleziona lo stile da cui partire e premi **Duplica stile**. La copia conserva immagini, lancette, pivot, complicazioni e ordine dei livelli.
3. Scegli la copia con **Stile in modifica** nel pannello **Livelli e proprietà**, oppure dalla sua scheda in Varianti grafiche.
4. Modifica la copia: ogni aggiunta, cancellazione, visibilità, colore, geometria, sorgente, selezione multipla e riordino appartiene a quello stile. Non serve attivare un flag per limitare le modifiche.
5. Per cambiare il quadrante di sfondo premi **Sfondo da immagine**: sostituisce il livello di sfondo della copia. Puoi anche cancellare o importare immagini direttamente dai suoi livelli. Torna allo stile originale per verificarne l’aspetto.
6. Salva ed **Esporta ZIP**. Il selettore dell’orologio riceve fino a cinque stili, ciascuno con risorse, complicazioni e anteprime reali generate dal proprio progetto.

**Apri livelli di questo stile** riporta dalla scheda Varianti all’editor. Cambiare stile svuota la selezione singola e multipla, così un drag o una freccia non agisce sulla selezione precedente. L’annullamento ripristina l’operazione registrata senza riscrivere i livelli degli altri stili. Puoi duplicare, eliminare e rinominare gli stili; eliminando il primo viene promosso il successivo con i suoi livelli.

Le complicazioni possono differire per numero, posizione, grafica e informazioni selezionabili. Il binario contiene il numero effettivo di slot per ciascuno stile; i gruppi delle scelte hanno identità distinte. L’AOD resta una schermata comune, editabile nella propria scheda e abbinata a tutte le varianti; esclude secondi e App Lua.

## Migrazione e salvataggio

I progetti con schema 1/2 vengono letti come prima e convertiti dall’editor in memoria. Prima si risolvono tutte le differenze salvate: poi ogni variante riceve una copia completa dell’aspetto risultante. Nessun file dell’utente viene sovrascritto all’apertura.

Il primo stile conserva i livelli principali del progetto; gli altri possiedono `VariantDesign`, con `elements`, `complications`, `layer_order` e `background`. `variant_project()` produce la schermata risolta per preview e compilazione; le transazioni dell’editor modificano soltanto il design selezionato. Asset identici possono condividere i medesimi byte, ma i livelli non sono collegati.

Il salvataggio usa **schemaVersion 3** e include anche immagini/font usati esclusivamente dalle varianti. Le versioni precedenti non aprono lo schema 3: conserva la copia del vecchio progetto insieme al vecchio ZIP. La validazione controlla risorse, geometrie, ID, ordine e sorgenti di ogni design, oltre ai metadati del pacchetto compilato.

## Crono Pro: rientro orario

Configurazione e ciclo restano **Prepara → Avvia → Stop → Reset**. Nel conteggio secondi e decimi procedono a scatti, ignorando Movimento Fluido. Preparazione e reset usano l’animazione comune da **320 ms**, target **25 fps**, indipendentemente dal flag; la grande torna ai secondi correnti dell’ora al termine del Reset.

Il rientro sceglie il **percorso orario**, senza privilegiare quello più breve. Una lancetta già a destinazione rimane ferma. La destinazione dei secondi civili continua a essere aggiornata; attraversamenti 59/0 e correzioni del dato non invertono il percorso. Le ombre ricevono lo stesso aggiornamento delle madri. La simulazione dell’editor usa il medesimo criterio.

Per le scale parziali il Pointer usa temporaneamente un dominio angolare completo durante il rientro, poi recupera l’intervallo configurato. Anche le scale con segno negativo rientrano fisicamente in senso orario. Il conteggio conserva l’angolo e la scala impostati dall’utente. In AOD l’animazione è annullata immediatamente; le pause temporanee da tocco la sospendono e riprendono dalla posa raggiunta.

Il flag Crono Pro è locale allo stile, come le altre proprietà. Le scene classiche e Pro sospendono il controller precedente anche quando l’host condivide la VM. Il file `studio_core.lua` del crono separato conserva gli stessi byte della 1.0; il Pro usa `studio_core_pro.lua`. Tutti gli script necessari e il manifest interattivo sono inclusi e confrontati con il binario.

## Verifiche e ripristino

**127 test della suite completa, 11 verifiche finali sulle varianti e 100 controlli dell’editor superati.** Rapporti: [validation-editor-1.2.json](validation-editor-1.2.json), [executable-build-1.2.json](executable-build-1.2.json). I controlli comprendono rientri orari su scale complete/parziali/inverse, AOD e pause, migrazione, asset presenti solo in una variante, modifiche locali, selezione multipla, eliminazione del primo stile e compilazione reale temporanea con sfondi, sorgenti e conteggi di complicazioni differenti.

Il consumo e la precisione subsecondo non sono misurati. Il test fisico 1.1 è [registrato](hardware-test-1.1.json); rientri orari e varianti indipendenti della 1.2 attendono la nuova prova sul dispositivo. Non viene avviato l’EXE in ambiente isolato e non viene consegnato un quadrante dimostrativo.

Il [backup 1.1](stable-baseline-1.1.json) conserva sorgenti, 708 risorse ed eseguibile esatti, verificati tramite SHA-256 e CRC. Per tornare alla versione precedente estrai il backup in una cartella nuova e usa progetto/ZIP precedenti. Il vecchio EXE 1.1 rimane nella root.

Per le release successive, su richiesta dell’utente, non vengono creati ulteriori backup di regressione. Documenti e rapporti restano aggiornati; test mirati e verifica statica del bundle accompagnano l’eseguibile.
