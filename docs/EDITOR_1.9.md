# S5 Studio 1.9 — Cornici, ellissi e ombre

## Forme

Il livello Forma può essere rettangolare oppure circolare/ellittico. `fill_enabled` abilita il riempimento, il cui colore continua a essere `color`. `border_color` e `border_width` definiscono la cornice indipendente: spessore 0–100 px, con 0 per eliminarla. Il bordo viene disegnato all'interno della geometria della forma. Disabilitare il riempimento nell'editor propone 2 px di bordo se lo spessore era zero. Colori e spessori restano modificabili; l'assenza di colore rende trasparente soltanto il colore scelto.

La forma ellittica usa direttamente larghezza e altezza: nessun vincolo di proporzione nei campi o nel trascinamento. Il cambio rettangolo/ellisse conserva posizione e dimensioni. Il cerchio è il caso in cui larghezza e altezza coincidono.

## Ombre

Testo, Dato live e Forma espongono `shadow_enabled`, `shadow_color`, `shadow_opacity` (0–255, mostrata come 0–100%), `shadow_offset_x/y` (−480…480 px), `shadow_blur` (0–40 px) e `shadow_spread` (−32…32 px). Espansione positiva dilata l'ombra, negativa la restringe. La maschera deriva dai pixel visibili del contenuto, inclusa la cornice. L'opacità del livello attenua anche l'ombra.

L'ombra viene applicata dopo rotazione e arco; gli offset seguono gli assi dello schermo. L'area intermedia conserva l'alone prima del ritaglio al canvas, evitando tagli sul riquadro del livello. Le PNG esportate restano entro 480×480. Ombra e contenuto costituiscono un solo livello rispetto agli altri oggetti. Salvataggio, duplicazione, Annulla/Ripeti e stili indipendenti conservano le nuove proprietà. I progetti precedenti mantengono riempimento attivo, bordo assente e ombra disattivata.

Testi e forme usano PNG già composte, incluse quelle inserite nelle scene Crono. Giorni e mesi conservano le liste native dei valori del calendario, con un'immagine completa di effetti per ogni voce.

I numeri live con ombra usano lo stesso renderer Lua già disponibile per rotazione/arco. `live_data.py` prepara i glifi e le rispettive ombre; `studio_live_data.lua` crea prima tutte le immagini d'ombra e poi tutte quelle delle cifre. Le notifiche Q8 del sensore aggiornano entrambi i gruppi, compresa la sparizione delle cifre inutilizzate quando cambia la lunghezza. Il valore simulato non viene incorporato come valore fisso. Sfocatura/espansione vengono calcolate sul PC, senza nuovi Timer o Anim sull'orologio; vengono aggiornate soltanto le immagini quando cambia il testo del valore. Le ombre live aggiungono al massimo un'immagine per cifra. Consumo e memoria effettivi sul dispositivo non sono stati misurati.

L'AOD conserva i percorsi esistenti: effetti statici e glifi aggiornati da eventi, senza nuove animazioni. Secondi e scene Crono restano esclusi dall'AOD. I runtime Crono classico, Crono Pro e campionamento civile 1.8.1 non sono stati modificati.

## Verifiche e consegna

93 test mirati e 15 controlli UI dai sorgenti superati. Copertura: bordo/riempimento, ellissi, alpha/colore, ritaglio, arco/rotazione, uguaglianza delle PNG native con l'anteprima, aggiornamenti reali simulati dei sensori, tutte le ombre sotto tutte le cifre, calendario nativo, AOD, salvataggio/stili, Annulla e ridimensionamento via mouse. Compilazioni binarie temporanee con scene Pro e AOD, oltre alla verifica del grafo finale in memoria. Un test d'integrazione che produce un pacchetto ZIP è stato escluso. Le correzioni 1.8.1 sono state nuovamente verificate nei test di rollover; il loro precedente test hardware rimane documentato separatamente.

Set personali controllati: sei set, 17 modelli aggiuntivi, 29 PNG, 612 modelli totali; nessun aggiornamento e cataloghi sorgente intatti. `.gitignore` conservato. Nessun backup, ZIP dimostrativo o avvio dell'eseguibile in ambiente isolato.

Avvia **S5Studio-1.9.exe**, carica il progetto esistente e imposta gli effetti nelle proprietà del livello. Esporta nuovamente lo ZIP per provarli sull'S5. La release incorpora le risorse e il compilatore nel singolo EXE. **Test reale superato**, come certificato dall'utente l'11 ottobre 2026: tutte le implementazioni funzionano benissimo. [Esito riferito dall'utente](hardware-test-1.9.json).

Rapporti: [test](validation-editor-1.9.json), [editor](layer-effects-editor-1.9.json), [bundle](executable-build-1.9.json), [catalogo](hand-set-integration-1.9.json).
