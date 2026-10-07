# Regione e prova locale — S5 Studio 0.2

EasyFace 4.23 è stato invocato direttamente. La CLI pubblicata dall'eseguibile è:

```text
Compiler -b {full path to .fprj} output {name of file.face} {id}
```

Non espone un parametro Regione. La configurazione locale non contiene una selezione CN/Global da cambiare. Il target del progetto è MiWatchS5, valore 562. Non è stata modificata la libreria del compilatore.

Il campione originale ha `deviceRegion=international` in description.xml e `CN` nella voce region di capability.json. Il confronto non stabilisce la semantica della voce né dimostra la causa del rifiuto. L'utente riferisce installazione e funzionamento con verifica delle capacità disattivata, Bluetooth e sincronizzazione attivi; preview non visibile. L'evidenza è registrata separatamente dalle verifiche automatiche.

La versione 0.2 genera un ZIP **sperimentale** con il proprio binario compilato, description.xml P62/480x480/international e preview PNG proprie, alla radice e sotto preview/. Non contiene capability.json, hashCode o uidmap.map copiati o inventati. Non è un pacchetto Xiaomi firmato o un quadrante già collaudato sul dispositivo. L'assenza delle capacità potrebbe essere rifiutata dalla mod anche con il controllo disattivato.

Per il test minimo usare S5_Test_Locale_TEST_LOCALE.zip senza estrarlo. Copiarlo nel telefono, aprire l'uploader con l'orologio connesso, usare la stessa impostazione Verify capability set disattivato del test originale, selezionare il ZIP e avviare l'installazione se accettato. Verificare ora e batteria; annotare l'eventuale errore esatto e la visibilità dell'anteprima. Questo test non include AOD.

Per chiudere il problema delle capacità serve la semantica del controllo della specifica mod e un pacchetto completo generato da una toolchain appropriata. Cambiare una stringa CN non è una soluzione verificata.
