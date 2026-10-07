# Analogico, varianti e complicazioni — 0.5

La limitazione precedente a due slot e alla grafica di Suit and tie era del nostro adattatore. Non era una limitazione dimostrata del S5. Il test 0.4 ha mostrato che quel trapianto era incompleto; non usare più quella build come risultato valido delle funzioni modificabili.

## Lancette

Ore/minuti/secondi sono DataItemPointer nativi con sorgenti 0811/1011/1811, intervallo ore 720° e minuti/secondi 360°. La UI modifica posizione e dimensione del gruppo, lunghezza, larghezza e tacche. Ogni lancetta accetta un PNG/SVG personale o uno dei 124 modelli estratti dai quadranti dell’utente. Il pivot originale viene letto dal payload nativo e verificato dentro l’immagine. La galleria include autore, quadrante, tema e hash dell’asset; immagini e pivot entrano nel progetto portabile. Le lancette che nei campioni funzionano solo su un tratto di giro sono escluse dai preset per un giro completo.

## Stili

Fino a cinque stili, ciascuno con nome distinto, accento, sfondo/immagine e override dei livelli, comprese bitmap/pivot delle lancette. Ogni stile normale ha un proprio payload e una vera anteprima nativa compilata; PNG e preview del selettore sono generati dal progetto. AOD è comune e viene abbinato a ogni stile, senza secondi e slot. Nessuna anteprima Suite viene utilizzata per rappresentare il progetto nuovo.

## Slot

Studio permette fino a 16 slot, con almeno cinque già inclusi nel progetto di test. Non è un massimo accertato del firmware. Ogni slot ha posizione e dimensioni proprie; può offrire tutte le 58 sorgenti osservate più Nessuna, oppure un sottoinsieme. Ogni scelta genera un gruppo completo: cornice, etichetta, unità, cifre native o icona meteo, miniatura e bordo editor. Nessuna mostra un gruppo trasparente vuoto.

Puoi modificare colori, cornice arrotondata/circolare/assente, font, etichetta, cifre, decimali e unità. Cifre/decimali 0/−1 attivano i default automatici. I numeri includono segno e punto decimale; temperatura e bussola usano i binding osservati. La precisione non converte automaticamente la sorgente in un’altra unità. Il nome/unità e il valore reale vanno confrontati sul dispositivo.

Il default del progetto stabilisce la prima scelta. Il menu Simula modifica solo l’anteprima nel PC. Le immagini mostrano dati di esempio; i numeri nel binario rimangono widget dinamici. Meteo richiede dati sincronizzati dal telefono; disponibilità e aggiornamento dei singoli canali dipendono dal firmware e dalle autorizzazioni.

“Sorgenti disponibili” significa i canali del framework dimostrati nei tuoi file, inclusi tempo/calendario, stato e progressi. Non significa poter interrogare qualsiasi sensore grezzo. `dateLunarStringMonth`, `dateLunarStringDay` e `weatherCurrentPressure` sono testo formattato non ancora generabile dinamicamente; calendario numerico e pressione `systemSensorAtmosphericPressure` sono disponibili.

## Metadati ed esportazione

I metadati modificabili devono descrivere il nostro binario. Description, manifest, uidmap ed editor vengono rigenerati, mentre capability e record protetti del template rimangono intatti. Il validator controlla le corrispondenze tra sorgenti, UID, layout, gruppi, scelte, nomi degli stili e immagini. `apply-template` sul FPRJ Studio riproduce il grafo completo dal `.s5faceproj` incorporato; rileva modifiche manuali dei sorgenti.

Il nuovo test deve verificare sul S5 cinque scelte indipendenti e cinque stili visibilmente diversi, oltre a preview e AOD. I test sul PC non certificano la gestione delle scelte nella mod o nel firmware.
