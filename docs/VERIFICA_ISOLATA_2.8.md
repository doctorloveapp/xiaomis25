# S5 Studio 2.8 — verifica dell'eseguibile in ambiente separato

**Data:** 2026-10-13. **Esito:** verifiche funzionali eseguite superate; rilevate imperfezioni nella traduzione inglese da rifinire prima di presentare l'interfaccia come completamente tradotta.

Questa prova è stata autorizzata espressamente dall'utente **solo per la versione 2.8**. Non cambia la preferenza abituale del progetto: nelle prossime modifiche restano previsti test sui sorgenti e controllo statico del bundle, senza avviare l'EXE in ambienti isolati salvo nuova richiesta.

## Tipo di isolamento e limiti

Windows Sandbox non era disponibile. La verifica è stata svolta sul Windows del PC ospitante, usando una cartella temporanea inizialmente contenente **soltanto `S5Studio-2.8.exe`**, una directory di lavoro separata e percorsi temporanei per `LOCALAPPDATA`, `APPDATA`, `USERPROFILE`, `TEMP` e `TMP`. Il PATH del processo conteneva soltanto la directory di sistema Windows; Python, Node e le risorse del repository non erano nel PATH.

È una prova di autonomia del bundle e separazione delle preferenze, **non una macchina virtuale né una barriera di sicurezza del filesystem**. Non certifica l'installazione su un Windows completamente pulito o privo dei prerequisiti .NET. I dialoghi nativi possono mostrare controlli nella lingua di Windows: i titoli impostati da S5 Studio sono invece tradotti.

## Risultati

| Controllo | Risultato |
| --- | --- |
| Identità del file copiato rispetto all'EXE consegnato | SHA-256 invariato |
| `runtime-info` nell'EXE | Superato: esecuzione frozen, 1.257 risorse verificate |
| `self-test` nell'EXE | Superato: tre modelli e relativo rendering |
| `template-info` nell'EXE | Superato: template e default incorporati accessibili |
| Primo avvio grafico con preferenze assenti | Italiano, Version 2.8, finestra massimizzata, anteprima visibile |
| Cambio lingua dalla UI | Passaggio all'inglese riuscito; `language: en` salvato nel profilo temporaneo |
| Catalogo lancette | Pagina e anteprime caricate; 310 set elencati, risorse incorporate disponibili |
| Catalogo dischi | Pagina e controlli caricati; inventario incorporato verificato dal controllo runtime |
| Dialoghi di progetto | Titoli `Save project` e `Open project`, filtro `S5 projects` |
| Salvataggio e riapertura | Progetto temporaneo salvato e riaperto correttamente; quattro livelli e anteprima conservati |
| Riavvio dell'EXE | Inglese riletto dalle preferenze salvate; finestra massimizzata |
| Chiusura | Entrambe le sessioni chiuse normalmente |
| Configurazione personale | Hash invariati per le preferenze, la cronologia dialoghi, il recupero e i cataloghi controllati, sia EXE sia sorgenti |

Non sono stati generati quadranti ZIP, eseguite prove sul dispositivo, installati programmi o modificati codice applicativo e binario. La compilazione EasyFace non è stata rieseguita: questa prova riguarda l'autonomia del bundle e l'interfaccia 2.8; le evidenze di esportazione e firmware restano quelle documentate separatamente.

## Osservazioni sulla localizzazione

Nella modalità inglese sono rimaste visibili alcune etichette italiane o miste, fra cui:

- `Salva sets in the catalog` e `Salva disc in the catalog`;
- `Importa PNG disco`;
- `310 set visualizzati`;
- `Dato che guida il valore` nelle proprietà di un dato live.

Sono difetti di presentazione osservati nell'eseguibile, senza errori di avvio, lettura risorse o salvataggio nei controlli eseguiti. Non vanno confusi con i nomi personalizzati di progetti, livelli, stili e modelli, che devono mantenere il testo dell'utente.

Il codice esaminato compone alcuni messaggi inserendo verbi italiani nei parametri delle traduzioni, ad esempio `{v7} set nel catalogo`: tradurre la frase esterna lascia il parametro `Salva` invariato. Altri testi composti non hanno una voce completa corrispondente nel catalogo JSON. Per la revisione internazionale conviene tradurre esplicitamente queste frasi complete e aggiungere verifiche delle etichette finali, oltre ai controlli della sola presenza dei cataloghi. **Durante questa verifica il codice non è stato modificato.**

Due anomalie iniziali provenivano dalla preparazione del test: una regola Chromium quotata in modo errato e l'assenza della cartella Desktop nel profilo temporaneo. Il profilo e la regola sono stati corretti; il secondo avvio e la successiva apertura del progetto non hanno riproposto quelle anomalie. Non sono classificate come difetti del prodotto.

## Identità e documenti collegati

`S5Studio-2.8.exe` — **247.417.289 byte**.

```text
ee556cbe5a2df507ef8e99bda037feca78aab970ede6396e61691d2d359202cd
```

[Report strutturato](isolated-executable-2.8.json) · [Validazione sorgenti](validation-editor-2.8.json) · [Integrità statica del bundle](executable-build-2.8.json) · [Guida i18n](I18N_2.8.md).
