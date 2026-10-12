# Dischi lunari — calibrazione nella 2.4

> Documento storico della 2.4. La **2.5** aggiunge il contatore giornaliero indipendente da 59 posizioni, con impostazioni automatiche: consulta [la guida aggiornata](DISCHI_LUNARI_2.5.md). I limiti delle sorgenti native descritti qui restano validi.

## Cosa significano le 59 posizioni

Un disco lunare meccanico tradizionale ha due lune diametralmente opposte. Una ruota da 59 denti avanza di un dente al giorno: un giro completo richiede 59 giorni e ogni luna rappresenta un ciclo approssimato da 29,5 giorni. Il passo è `360° / 59 = 6,1016949°`. La [Fondation Haute Horlogerie](https://www.hautehorlogerie.org/en/watches-and-culture/watchmaking-knowledge/encyclopedia/moonphases-complications) descrive questo meccanismo e la sua approssimazione rispetto al ciclo astronomico reale. Non tutti i dischi con sole, luna o stelle seguono questa logica: alcuni indicano soltanto giorno e notte.

## Cosa forniscono le sorgenti di S5 Studio

Le sorgenti native ricostruite dai pacchetti hanno due significati diversi:

| Sorgente | Valori utilizzati | Comportamento |
| --- | --- | --- |
| Fasi lunari (`dateMoon`, `7012`) | 0–7 | Otto fasi; non cambia una volta al giorno |
| Giorno lunare (`dateLunarDay`, `3812`) | 1–29/30 | Avanza ogni giorno, poi riparte da 1 al nuovo mese lunare |
| Ore (`timeHour`, `0811`) | 0–23 | Un giro al giorno con intervallo 24 e rotazione 360°; indicazione giorno/notte |

Il default 24 / 360° dei dischi rotanti è generico. **Intervallo valori** è il denominatore della trasformazione, non un numero di giorni da attendere:

`angolo = angolo iniziale + (dato − valore iniziale) × rotazione totale / intervallo valori`

Cambiare l'intervallo non cambia la natura o la frequenza del dato di ingresso.

## Impostazioni utilizzabili ora

Per un indicatore circolare dei soli otto stati lunari: **Fasi lunari**, valore iniziale **0**, intervallo **8**, rotazione **360°**. Una PNG con due lune opposte rappresenta invece un ciclo in mezzo giro: **180°** su otto stati (22,5° per cambio di fase). Il verso può essere invertito con una rotazione negativa. Sono posizioni discrete per fase, non uno scatto al giorno. L'angolo iniziale dipende da dove le lune sono disegnate e dalla maschera sovrapposta.

Per una **approssimazione giornaliera** su una grafica a due lune: **Giorno lunare**, valore iniziale **1**, intervallo **59**, rotazione **360°** o **−360°**. Fra due giorni consecutivi il passo è circa 6,10°. Al nuovo mese il dato torna a 1: questo interrompe la progressione a 59 posizioni. La simmetria delle due lune può attenuare il salto visivo, ma non rende questa impostazione equivalente alla ruota meccanica. Non va presentata come una simulazione esatta.

Per **59 posizioni continue, una al giorno**, serve un dato derivato che conti giorni consecutivi da una data di riferimento e applichi il modulo 59, con calibrazione iniziale. Le due sorgenti lunari disponibili non forniscono questo contatore. Questa revisione non introduce una nuova logica Lua astronomica; non basta impostare 59 lasciando la sorgente Fasi lunari. Anche una ruota esatta da 59 giorni conserva l'approssimazione astronomica di 29,5 giorni e richiede nel tempo una correzione.

I modelli del catalogo in modalità **Immagini per valore** conservano le loro sequenze originali: il firmware seleziona una PNG per fase o giorno lunare. Per quelli non si calibra la rotazione di una PNG singola.

## Eliminazione dal catalogo

**Dischi → Elimina** è ora disponibile su tutti i modelli. Per i modelli incorporati l'eliminazione è una preferenza locale persistente; il contenuto originale dell'EXE e dei pacchetti sorgente rimane intatto. La sezione **Dischi incorporati eliminati** permette di ripristinare il modello originale. Le modifiche locali di quel modello vengono rimosse con l'eliminazione. Le PNG e i livelli già incorporati nei progetti non cambiano.
