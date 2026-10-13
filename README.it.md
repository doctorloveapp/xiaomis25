# S5 Studio

![S5 Studio — progettazione di quadranti per Xiaomi Watch S5](docs/assets/s5-studio-banner.svg)

[![Build 2.7](https://img.shields.io/badge/build-2.7-2563eb)](https://github.com/doctorloveapp/xiaomis25/releases) [![114 test mirati superati](https://img.shields.io/badge/tests-114%20targeted%20passed-15803d)](docs/validation-editor-2.7.json) [![Test S5 confermato dall'utente](https://img.shields.io/badge/S5%20device%20test-user%20confirmed-15803d)](docs/hardware-test-2.7.json) [![Licenza codice MIT](https://img.shields.io/badge/code%20license-MIT-64748b)](LICENSE)

[English](README.md) · **Italiano** · [Releases](https://github.com/doctorloveapp/xiaomis25/releases) · [Documentazione](docs/README.md)

S5 Studio è un editor visuale Windows per creare quadranti Xiaomi Watch S5 da immagini personalizzate. Integra stili indipendenti, livelli dinamici e un cronografo Lua condiviso con compilazione nativa, packaging su template e validazione finale, per produrre quadranti funzionanti e configurabili.

**Dispositivo:** Xiaomi Watch S5 **M2530W1**, 480 × 480. **Interfaccia:** italiana. La documentazione bilingue non implica una UI inglese. I badge descrivono risultati registrati per la build 2.7, non un servizio CI continuo.

## Indice

- [Features — Funzionalità](#features)
- [Installation Guide — Installazione](#installation-guide)
- [Technical Architecture — Architettura](#technical-architecture)
- [Chrono Pro Documentation — Cronografo](#chrono-pro-documentation)
- [Compatibility — Compatibilità](#compatibility)
- [Troubleshooting — Risoluzione problemi](#troubleshooting)
- [Common Questions — FAQ](#common-questions)
- [Development — Sviluppo](#development)
- [Documentation and Release History — Guide e storico](#documentation-and-release-history)
- [License/Attributions — Licenza e crediti](#licenseattributions)

## Features

| Funzione | Implementazione e vantaggio |
| --- | --- |
| **Editor a livelli** | Immagini, testi, dati live, forme, lancette e dischi; riordino, eliminazione, duplicazione, blocco e Annulla/Ripeti. Ctrl abilita la selezione multipla; trascinamento, frecce e allineamenti agiscono sulla selezione. |
| **Grafica e geometria** | Importazione PNG/JPEG/WebP/BMP/SVG; ingrandimento oltre il canvas con ritaglio finale a 480 × 480. Rotazione e arco di testo/dati; rettangoli, cerchi ed ellissi con riempimento, cornice e ombre indipendenti. |
| **Set lancette** | Importazione di set grandi/piccoli con nome, pivot impostabile cliccando sulla grafica, ombre abbinate o generate. Il modello ore può abbinare automaticamente minuti/secondi; ogni lancetta resta modificabile separatamente. |
| **Stili indipendenti** | Fino a cinque stili con livelli e proprietà propri. Duplica uno stile e cambia sfondo/lancette senza nascondere quelli dell'originale. **Perché:** ogni stile è una composizione completa, non una sovrapposizione di colore. |
| **Dati live e complicazioni** | Calendario, salute, meteo, bussola e altri canali mappati; fino a 16 slot nel progetto Studio. Gli slot sono livelli, inizialmente con il solo valore. È un limite applicativo, non il massimo certificato del firmware. |
| **Calendario e dischi** | Giorni MON–SUN; mesi inglesi completi oppure JAN–DEC. Importazione, modifica ed eliminazione dischi, pivot e ombre; ruota lunare giornaliera a 59 posizioni. **Perché:** la posizione deriva dalla data e recupera i giorni trascorsi a schermo spento. |
| **Movimento e AOD** | Flag fluidi distinti per ore/minuti/secondi normali; decimi crono fluidi facoltativi. Secondi e indicatori del cronografo sono esclusi dall'AOD; le animazioni della scena normale si interrompono entrando in AOD. |
| **Simulazione** | Anteprima animata, zoom/panoramica, giorno 1–31, mese e anno, lettura congelata del cronografo. I valori simulati non sostituiscono le sorgenti reali esportate. |
| **Esportazione validata** | Compilazione EasyFace nativa, anteprime complete, ZIP su template e rapporto per build. **Perché:** binario, metadati, stili e binding Lua sono verificati insieme prima di pubblicare il file di output. |

La build personale 2.7 comprende **629 modelli di lancette e 90 dischi**, anche da 39 quadranti forniti per lo studio. I numeri descrivono quella build: non costituiscono una libreria liberamente redistribuibile. [Ambito di distribuzione](docs/DISTRIBUTION.md).

## Installation Guide

### Applicazione Windows precompilata

1. Apri le [GitHub Releases](https://github.com/doctorloveapp/xiaomis25/releases) e leggi asset e note della release scelta. L'archivio dei sorgenti GitHub non è l'eseguibile.
2. La build documentata usa **`S5Studio-2.7.exe`**, **Windows x64** e **.NET Framework 4.7.2 o successivo**. Questa build personale incorpora Python, Qt, UI compilata, cataloghi, template e compilatore; sul PC di destinazione non servono Python o Node.
3. Verifica l'hash del file con il rapporto associato a quell'esatto asset. Salva il lavoro, chiudi la versione precedente e avvia l'EXE oppure **`Avvia_S5_Studio.cmd`**, se fornito. La finestra si apre massimizzata.
4. Crea/apri un `.s5faceproj`, configura stili normali e AOD, salva e premi **Esporta ZIP**, scegliendo la cartella di destinazione.
5. Copia il ZIP sul telefono senza estrarlo e installalo con un uploader locale compatibile. Mantieni Bluetooth e sincronizzazione attivi. Consulta la [FAQ Capabilities](#perché-linstallazione-locale-fallisce-con-capabilities) prima di modificare le impostazioni dell'uploader.

**Ambito:** l'eseguibile autonomo attuale è un **bundle personale**, con compilatore esterno e grafiche di terzi. La licenza MIT del codice non stabilisce il diritto di redistribuirli. Un pacchetto pubblico con risorse differenti può avere requisiti diversi. [Requisiti e dettagli](docs/INSTALLATION.md) · [Avvisi di terze parti](THIRD_PARTY_NOTICES.md).

### Percorsi e integrità

| Uso | Percorso |
| --- | --- |
| Progetto | `*.s5faceproj` nella cartella scelta; incorpora immagini e font selezionati |
| Preferenze, recuperi e cataloghi dell'EXE | `%LOCALAPPDATA%/S5Studio/` |
| Dati di lavoro dei sorgenti | `<repository>/data/`, intenzionalmente nel gitignore |
| Compilatore dai sorgenti | `tools/easyface-4.23/Compiler.exe` insieme a `DeviceInfo.db` |
| Template predefinito dai sorgenti | `quadrante_funzionante.zip` nella root |
| Esportazioni | Cartella scelta in **Esporta ZIP**, compreso `build-report.json` |

```powershell
Get-FileHash -LiteralPath .\S5Studio-2.7.exe -Algorithm SHA256
```

SHA-256 dell'**eseguibile personale 2.7 consegnato**:

```text
f955eb7d34278e0715646c3c7047232759f6e5d91da918958f61f9e786115205
```

Identifica quell'esatto file: una ricompilazione o un asset pubblico con risorse diverse avrà un hash diverso. Gli hash di compilatore, template e campione originale sono conservati nella [guida di installazione](docs/INSTALLATION.md#reference-hashes).

## Technical Architecture

```text
Qt desktop / QtWebEngine + QtWebChannel / UI Tailwind offline
    -> Modello Python, trasformazione asset e rendering anteprima
    -> Widget nativi + scena Lua condivisa per stile interattivo
    -> EasyFace 4.23: FPRJ -> resource.bin
    -> Assemblaggio conservando i record protetti del template
    -> Validazione binario / metadati / preview / Lua -> ZIP + build-report.json
```

| Componente | Responsabilità |
| --- | --- |
| `s5studio/model.py`, `render.py`, `frontend/` | Progetto, livelli indipendenti per stile, geometria ed editor |
| `s5studio/native.py`, `native_graph.py` | Generazione FPRJ, compilazione e ispezione binaria |
| `s5studio/lua_runtime.py`, `s5studio/lua/` | Scena condivisa, stato crono, clock civile coerente e dati dinamici |
| `s5studio/semantic_package.py`, `template_package.py` | Record ZIP protetti, metadati rigenerati e validazione strutturale |
| `scripts/prepare_runtime.py`, `package.ps1`, `verify_bundle.py` | Preparazione runtime personale, EXE e verifica statica |

**Chirurgia su template:** vengono conservati **187 file protetti e otto record di directory**, comprese capability e `hashCode`. Si sostituiscono binario e anteprime; description, manifest, UID ed editor sono rigenerati in relazione alle nuove risorse. Lasciare tutti questi metadati invariati descriverebbe ancora il quadrante originale.

Il validator verifica record protetti, CRC, ID, offset, riferimenti nativi, stili/slot, anteprime e Lua incorporato. La firma strutturale locale **non è una firma crittografica Xiaomi** e non garantisce il superamento del controllo capabilities dell'uploader. [Analisi template](docs/RAPPORTO_TEMPLATE_FUNZIONANTE.md) · [Packaging](docs/ANALOGICO_VARIANTI_COMPLICAZIONI.md).

**Confini dei dati:** i canali mappati appartengono al framework dei quadranti, non danno accesso arbitrario ai sensori grezzi. Tre sorgenti di testo formattato osservate nei campioni non sono esportabili come testo dinamico. Si usano widget nativi dove possibile; i livelli dinamici nella scena Lua conservano binding e ordine. I tipi intermedi non supportati sono rifiutati, senza trasformarli silenziosamente in immagini fisse.

## Chrono Pro Documentation

### Modalità e tap

| Modalità | Impostazione | Sequenza e secondi grandi |
| --- | --- | --- |
| **Crono classico** | Piccole impostate su Ore/Minuti/Secondi Crono; Pro disattivo | Avvia → Stop → Reset; secondi grandi normali indipendenti |
| **Crono Pro** | Flag **Crono Pro** nella scheda secondi grandi | Prepara allo zero → Avvia → Stop → Reset; a riposo i secondi grandi tornano all'ora |
| **Only Crono** | Flag **Only Crono** nella stessa scheda | Stessa sequenza Pro; secondi grandi fermi a zero a riposo |

**Perché una scena condivisa:** ore/minuti/secondi crono devono leggere lo stesso tempo trascorso e lo stesso gestore tap. Non si può presumere che VM di widget distinti condividano globali o moduli. Studio registra le lancette di misura nella stessa scena Lua per stile, eliminando questa dipendenza; non dichiara di aver misurato l'isolamento delle VM del firmware.

**Configurazione a sei indicatori:** secondi grandi, piccole ore/minuti/decimi crono e due piccole facoltative **Centesimi (POST)** / **Millesimi (POST)**. Secondi piccoli normali, ore civili 24h e disco lunare continuano a usare le proprie sorgenti.

### Tempo, movimento e lettura POST

- **Clock:** una sola sorgente temporale per la misura; tempo trascorso calcolato dai timestamp, non contando i callback. Pro usa un clock monotono quando disponibile, con fallback alla fase dell'animazione LVGL. La disponibilità effettiva dipende dal firmware.
- **Running:** secondi grandi e ore/minuti crono avanzano a scatti. I decimi Pro offrono dieci scatti al secondo oppure un target fluido **25 fps**, guidato da `Anim.exec_cb`. La cache write-on-change evita scritture uguali su lancette e ombre.
- **Transizioni:** preparazione/reset coordinati da **720 ms**, target 25 fps. Le lancette a giro completo rientrano in senso orario; gli archi restano nella scala calibrata. Ore/minuti grandi continuano a segnare l'ora civile.
- **POST:** centesimi/millesimi rimangono nella posizione iniziale durante Running. Allo Stop raggiungono la frazione dello stesso tempo congelato. **Perché:** lettura precisa sul quadrante senza rotazioni continue velocissime o nuovi timer rapidi durante la misura.
- **Precisione:** frazioni complete 00–99 e 000–999, oppure singola cifra. A 12,488 s: 48 e 488. Tre cifre **non certificano precisione di 1 ms**: contano risoluzione del clock, consegna del tap e sospensioni.
- **AOD e ciclo di vita:** interrompe subito le animazioni della scena normale e usa l'AOD configurato senza secondi o lancette crono. Lo stato non persiste se viene ricreata la VM o il quadrante; spegnimento del display e distruzione della VM sono eventi differenti.

Per un giro completo: intervallo 60 per secondi/minuti, 12 per ore crono su scala 12h, 10 per decimi e 100/1000 per frazioni POST complete. Per un arco definisci estremi di valore e angolo, per esempio 0–999 su 30°–140°. Nella lettura completa dei millesimi, 800 significa 800 ms. Calibra anche pivot e orientamento iniziale della grafica.

[Guida tecnica attuale](docs/CHRONO_PRO.md) · [POST e archi](docs/EDITOR_2.0.md) · [Scheduling dei callback](docs/EDITOR_2.3.md).

## Compatibility

| Dispositivo / firmware | Stato | Evidenza e ambito |
| --- | --- | --- |
| **Xiaomi Watch S5 M2530W1 · 3.221.024 · 480 × 480** | **Build 2.7 confermata dall'utente** | Modello e firmware installato dichiarati dal tester; funzionamento confermato il 2026-10-13 |
| Stesso modello, altri firmware | Non verificato | API Lua, canali e uploader possono differire |
| Altri Xiaomi/Redmi o Mi Band | Target non supportato | Gli esempi API di modelli affini non dimostrano compatibilità dei pacchetti |
| Windows x64 + .NET Framework 4.7.2 o successivo | Target dell'EXE personale | Requisiti runtime/compilatore; bundle verificato staticamente |
| Linux/macOS o pubblicazione nello store ufficiale | Non validato | Nessun pacchetto supportato o integrazione di pubblicazione ufficiale |

Target compilatore **MiWatchS5 / 562**, tipo dispositivo del pacchetto **P62**. I profili storici indicano mod m0tral **V3.52.0i**; la versione esatta dell'app nell'ultimo test non è stata confermata separatamente. L'esito hardware è riferito dal proprietario, non una certificazione indipendente. Fps, consumo e risoluzione grezza del clock non sono stati misurati. [Esito reale](docs/hardware-test-2.7.json) · [Test sorgenti](docs/validation-editor-2.7.json) · [Bundle](docs/executable-build-2.7.json).

## Troubleshooting

| Sintomo | Azione |
| --- | --- |
| Rifiuto **Capabilities** nell'uploader locale | Segui la [FAQ](#perché-linstallazione-locale-fallisce-con-capabilities); cambiare CN/Global non è una soluzione dimostrata |
| Nome `L00000000001` o preview assente sul telefono | Osservato anche sul riferimento; confronta preview sull'orologio, in Modifica e nei file generati prima di cambiare la grafica |
| Compilatore/template mancanti | Il clone non include ogni dipendenza personale; consulta i [requisiti sorgenti](docs/INSTALLATION.md#running-from-source) |
| Risultato sull'orologio diverso dall'editor | Riesporta dalla build corrente e reinstalla il nuovo ZIP; aggiornare il programma sul PC non aggiorna i quadranti installati |
| Lancetta in posizione/dimensione inattesa | Verifica sorgente, intervallo, angolo e pivot; i secondi civili indicano i secondi simulati, non partono automaticamente da zero |
| Livello non ammesso fra lancette Lua | Verifica tipo e confini della scena: widget compositi/selezionabili non supportati devono restare fuori |
| Dato live assente o fermo | Verifica canale nativo e dati del sensore/app sull'orologio; i numeri di esempio non sono letture reali |

[Analisi uploader](docs/ANALISI_UPLOADER_1.4.md) · [Scena Longines](docs/LONGINE_LIVELLI_2.6.md) · [Correzioni lancette 2.7](docs/EDITOR_2.7.md).

## Common Questions

### Perché l'installazione locale fallisce con Capabilities?

Lo stesso ZIP di riferimento funzionava dal catalogo online della mod, mentre l'uploader locale lo rifiutava. Disattivare **Verify capability test** ha consentito l'installazione nella configurazione riportata. È evidenza di una differenza fra percorsi di caricamento, non una correzione universale del firmware.

Per un quadrante creato e validato da te per **M2530W1**: controlla il target, mantieni l'orologio collegato, disattiva temporaneamente quel controllo nella mod compatibile se il percorso locale rifiuta il file, seleziona il ZIP completo e verifica l'installazione. Ripristina il controllo nell'uso ordinario dove possibile. Il bypass rimuove un controllo di compatibilità dell'uploader: non firma il pacchetto, non valida file sconosciuti e non garantisce la sicurezza sul firmware. La mod è software di terzi e non viene distribuita dal progetto.

EasyFace 4.23 non espone un selettore Regione verificato. Nei campioni coesistono `deviceRegion=international` e `capability.region=CN`: cambiarli non è un rimedio dimostrato. [Analisi e limiti](docs/REGIONE_E_TEST_LOCALE.md).

### L'EXE funziona da solo? Perché data/ è nel gitignore?

L'EXE personale 2.7 consegnato incorpora le risorse: non richiede cartelle `data/`, compilatore o template accanto al file. Il clone dei sorgenti è diverso: dati personali, corpus originale, template e compilatore sono esclusi. Per riprodurre quel bundle occorrono gli input originali e i relativi permessi. [Installazione](docs/INSTALLATION.md).

### Stili e complicazioni sono indipendenti?

Ogni stile normale ha livelli, immagini, colori e lancette propri. L'AOD è comune. Gli slot complicazione sono livelli spostabili con scelte dati configurabili; 16 è il limite del progetto Studio, non la prova che ogni combinazione sia pratica sull'hardware. [Modello ed esportazione](docs/ANALOGICO_VARIANTI_COMPLICAZIONI.md).

### Il disco lunare è un'epemeride astronomica?

No. La modalità a 59 posizioni simula una ruota meccanica con due lune: un passo al giorno, giro in 59 giorni. Riferimento predefinito 2026-09-26; calibra angolo iniziale e correzione giorni rispetto alla grafica. Le otto fasi native sono una sorgente distinta. [Guida dischi lunari](docs/DISCHI_LUNARI_2.5.md).

### Posso redistribuire tutte le immagini e il compilatore?

La licenza del codice non concede diritti su grafiche, font, template o EasyFace. Gli avvisi attuali non stabiliscono il diritto alla redistribuzione pubblica dell'intero bundle personale. [Ambito di distribuzione](docs/DISTRIBUTION.md) · [Crediti](THIRD_PARTY_NOTICES.md).

## Development

L'ambiente Windows documentato usa **Python 3.13**. `requirements.txt` contiene le dipendenze dell'editor; `requirements-dev.txt` aggiunge pytest, PyInstaller e Lupa. Lupa serve ai test e non entra nel runtime distribuito.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

Il CSS Tailwind compilato è nel repository. Node serve soltanto per ricostruirlo: esegui `npm ci` e `npm run build` dentro `frontend/`.

```powershell
python -X utf8 scripts/sync_hand_sets.py
python main.py build project.s5faceproj --compiler tools/easyface-4.23/Compiler.exe --output build/export
python main.py apply-template project.fprj quadrante_funzionante.zip build/export
python main.py validate-template quadrante_funzionante.zip build/export/watchface.zip
python main.py inspect build/export/watchface.zip
python -m pytest -q
```

Sostituisci i nomi di esempio con i tuoi input/output. `apply-template` accetta progetti Studio e FPRJ supportati; per FPRJ Studio ripristina stili/slot dal progetto incorporato dopo averne verificato gli hash. I widget esterni non ricostruibili coerentemente vengono rifiutati.

`powershell -File scripts/package.ps1` prepara l'EXE personale dopo preflight e sincronizzazione; `python scripts/verify_bundle.py S5Studio-2.7.exe` controlla gli hash incorporati senza avviarlo. Il packaging attuale richiede il catalogo personale fornito e non è un builder generico da clone pulito. [Contributi](CONTRIBUTING.md) · [Prerequisiti sorgenti](docs/INSTALLATION.md#running-from-source).

## Documentation and Release History

- [Indice documentazione](docs/README.md) — guide correnti e rapporti, con lingua indicata.
- [Ingegneria Crono Pro](docs/CHRONO_PRO.md) — stato condiviso, clock, formule, POST e ciclo di vita.
- [Installazione](docs/INSTALLATION.md) — percorsi, dipendenze, hash e build dai sorgenti.
- [Storico versioni](docs/CHANGELOG.md) — note di release e riferimenti operativi precedenti conservati in italiano.
- [Conferma hardware 2.7](docs/hardware-test-2.7.json) — riscontro utente distinto dai controlli automatici.

## License/Attributions

**Codice originale e documentazione S5 Studio:** [licenza MIT](LICENSE), software fornito **così com'è, senza garanzie**. Progetto indipendente di interoperabilità, non un tool ufficiale Xiaomi né un servizio di pubblicazione nello store ufficiale.

**Dipendenze e ricerca:** Python/PSF, Qt/PySide6/Shiboken, QtWebEngine/Chromium, Pillow, Tailwind CSS e PyInstaller mantengono le proprie licenze. **m0tral** fornisce EasyFace e gli esempi API pubblici MiWatchLuaWatchfaces. Mi Create e UnpackMiColorFace sono stati studiati per interoperabilità; i loro sorgenti non sono incorporati nell'applicazione.

**Grafiche e marchi:** immagini di lancette/dischi/meteo e quadranti di riferimento restano dei rispettivi autori; i font hanno permessi propri. HaloX78 è accreditato come autore di quadranti, compreso il riferimento Ferrari, che non è trattato come OEM Xiaomi. Marchi e modelli identificano i riferimenti senza implicare affiliazione o approvazione.

Leggi [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), [licenses/](licenses/) e [ambito di distribuzione](docs/DISTRIBUTION.md) prima di redistribuire bundle o cataloghi. **La MIT del codice applicativo non cambia la licenza del compilatore proprietario o degli asset di terzi.**
