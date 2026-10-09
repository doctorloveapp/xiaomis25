# S5 Studio 1.7 — Ombre automatiche

1. Apri **Set lancette**. Crea un set o usa **Modifica** su quello già salvato, principale o piccolo.
2. Importa le PNG e scegli i pivot delle lancette. Attiva **Genera ombre**: compariranno automaticamente le anteprime delle ombre mancanti.
3. Se vuoi, regola **Opacità**, **Sfocatura** e **Spostamento X/Y**. I default sono 45%, 1,5 px e +2/+3 px. Il pivot dell’ombra automatica segue quello della lancetta; i suoi campi individuali sono in sola lettura. Se cambi il pivot della lancetta si aggiorna anche l’ombra.
4. Premi **Salva/Aggiorna set nel catalogo**. Sul livello del quadrante scegli nuovamente il set e premi **Usa modello**. Per il gruppo principale la scelta delle ore abbina minuti, secondi e ombre; per una piccola scegli il suo modello nel relativo menu. Attiva **Mostra ombre** nelle proprietà se erano nascoste.
5. Esporta normalmente lo ZIP. Le ombre vengono incorporate come PNG, usando gli stessi componenti nativi e Lua già disponibili.

Le ombre manuali già presenti vengono conservate, compresi pivot e spostamenti. Il flag completa solo quelle mancanti. Puoi importare una PNG sopra un’ombra automatica per sostituirla con una manuale. Le successive regolazioni globali non altereranno quell’ombra.

Disattivando **Genera ombre** vengono rimosse dalla bozza soltanto le ombre generate. Salva e riapplica il modello al quadrante se vuoi propagare la modifica. Eliminando una PNG manuale mentre il flag è attivo, il software genera un’ombra al suo posto. I progetti già salvati rimangono indipendenti dal catalogo.

La forma è ricavata dal canale alpha della PNG della lancetta. Con uno sfondo opaco viene proiettata la sagoma rettangolare della PNG: usa immagini con trasparenza. Studio crea un’immagine nera, sfoca il canale alpha e ne regola l’opacità. Aggiunge, quando possibile, margini trasparenti fino a tre volte il raggio di sfocatura senza superare 480 pixel per lato; il pivot viene traslato dello stesso margine. Se una PNG occupa già 480 pixel non viene aggiunto margine su quell’asse. Lo spostamento X/Y è misurato nei pixel della grafica sorgente e segue il ridimensionamento del modello insieme alla sua ombra.

Le PNG originali restano immutate. Le ombre hanno hash SHA-256 e metadati di provenienza (`generated`, `generatedFrom`) nel catalogo personale, con salvataggio atomico. Cambiare la lancetta, il pivot o le impostazioni rigenera solo le ombre automatiche. I set precedenti vengono aperti con Genera ombre disattivato, conservando l’aspetto originale. La funzione riguarda i set personali del pannello Set lancette; il catalogo incorporato rimane integro.

Il catalogo rimane in `%LOCALAPPDATA%/S5Studio/hand-sets/` nell’eseguibile, oppure `data/hand-sets/` dai sorgenti. Per usare una lancetta singola con ombra automatica puoi inserirla in un set piccolo con una sola PNG. Le ombre originali dei modelli del catalogo incorporato rimangono disponibili come prima.

**Test reale della 1.6.1 superato**, confermato dall’utente il 9 ottobre 2026: [evidenza](hardware-test-1.6.1.json). La 1.7 mantiene default 50%/15 px, refresh immediato, giorno simulato 15 e runtime Crono/Pro. Verifiche della nuova funzione: [validation-editor-1.7.json](validation-editor-1.7.json). L’utente conferma successivamente che la 1.7 ha funzionato bene: [esito](hardware-test-1.7.json). La patch [1.7.1](../README.md) corregge un falso blocco dell’editor quando il livello Crono Pro viene nascosto. Nessun nuovo backup, quadrante dimostrativo o test dell’eseguibile in ambiente isolato.
