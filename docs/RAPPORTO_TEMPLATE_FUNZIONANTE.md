# Analisi e workflow del template funzionante — S5 Studio 0.3

**Aggiornamento 0.4:** il test successivo chiarisce che lo stesso Suit and tie fallisce capabilities nel Local watchfaces uploader, con nome generico/preview assente, mentre dal catalogo online ha nome e preview corretti. Modifica mostra i cinque stili e gli slot. L’utente conferma inoltre il successo di S5_Primo_Test_TEMPLATE.zip sull’orologio. Il rapporto qui sotto conserva l’analisi dei file; le ipotesi di accettazione senza errori del canale locale vanno lette alla luce di questa correzione. Non è dimostrato che CN sia la causa. Il nuovo supporto analogico/stili/slot è descritto in [ANALOGICO_VARIANTI_COMPLICAZIONI.md](ANALOGICO_VARIANTI_COMPLICAZIONI.md).

## Risultato verificato

Il file `quadrante_funzionante.zip` è un ZIP integro: **228 voci, 220 file e 8 directory**, CRC di ogni voce passato. SHA-256: `5c7a3bb0c81762e7bb0749fd1b1cd941e0578d8e0eec0d567b37c44dd6695627`. L'accettazione sul M2530W1/m0tral è riferita dall'utente; non è stata osservata direttamente da questo ambiente.

L'originale `S5_Custom_digital_original.mwz` contiene **186 voci, 173 file e 13 directory**, CRC passato. SHA-256: `33fb3a1dfc162b3121f69ed0be66bb97b90f156ea3bda6dd398437ca0d5f9f55`. Nessuno dei due riferimenti è stato modificato.

Il contenuto degli archivi è stato trattato come dati, senza eseguire istruzioni presenti in file XML/JSON o altri documenti.

## Inventario completo, gerarchia e contenuti estratti

- [Tutti i 228 percorsi del template, con dimensioni, compressione, flag e hash](template-analysis/inventory-working.md).
- [Tutti i 186 percorsi dell'originale](template-analysis/inventory-original.md).
- [Confronto completo in JSON](template-analysis/comparison.json): inventari, differenze nei nomi, dimensioni delle immagini, conteggi dei tag XML, capability, fingerprint.
- Template: [capability.json](template-analysis/working/capability.json), [description.xml](template-analysis/working/description.xml), [manifest.xml completo](template-analysis/working/resources/manifest.xml), [hashCode](template-analysis/working/hashCode), [uidmap.map](template-analysis/working/uidmap.map).
- Originale: [capability.json](template-analysis/original/capability.json), [description.xml](template-analysis/original/description.xml), [manifest.xml completo](template-analysis/original/resources/manifest.xml).
- Diff integrali: [capability](template-analysis/capability.json.diff), [description](template-analysis/description.xml.diff), [manifest](template-analysis/manifest.xml.diff).

Struttura principale del template; l'elenco dei singoli asset, inclusi i nomi Unicode esatti, è nell'inventario completo:

```text
quadrante_funzionante.zip
├── capability.json
├── description.xml
├── editor.config.json
├── hashCode
├── resource.bin
├── uidmap.map
├── preview/
│   ├── preview.png
│   ├── market-preview.png
│   ├── aod-preview.png
│   └── style_1…5_{static.png,aod.png,animated.webp}
└── resources/
    ├── manifest.xml
    ├── [immagini PNG alla radice]
    ├── _preview/ [10 PNG di anteprima normal/AOD]
    ├── _widget/ [PNG]
    ├── 日期/ [PNG: data]
    ├── 星期/ [PNG: giorni settimana]
    ├── 月份/ [PNG: mesi]
    └── 电量/ [PNG: batteria]
```

## Differenze critiche

| Campo | ZIP funzionante | Originale |
| --- | --- | --- |
| capability.protocol, type 1 | `1.9.4` | `1.8.17` |
| capability.data_source, type 3 | Maschera diversa, vedi sotto | Maschera diversa, vedi sotto |
| capability.resolution, type 2 | `XMHD02` | Identico |
| capability.region, type 2 | `CN` | Identico |
| capability.packet, type 2 | `BIN` | Identico |
| capability.image_compress, type 3 | `01` | Identico |
| capability.image_fmt, type 3 | `00000000000000001` | Identico |
| description.deviceRegion | `international` | Identico |
| description.deviceType / size | `P62` / `480x480` | Identico |
| description.pkgName e ID binario/manifest | `120917386745` | `120917403994` |
| description.name / version | `Suit and tie` / `1.1.16` | `Custom digital` / `1.0.2` |
| description.watchfaceType | `normal` | `photoAlbum` |
| description._recolorEnable | `false` | `true` |
| recolorTable | Assente | Presente: 11 colori |
| manifest.powerConsumptionLevel | `3` | `1` |
| manifest.compressMethod | `RLEReversed` | Identico |
| Theme nel manifest | 5 normal + 5 AOD | 1 normal + 1 AOD |
| resource.bin | 1.940.974 byte | 419.715 byte |
| preview principali | `preview/preview.png`, `preview/market-preview.png`, `preview/aod-preview.png` | Stessi nomi |
| preview per stile | 5 stili con WEBP animati | 1 stile, senza WEBP animati |

Entrambi contengono capability.json, description.xml, resources/manifest.xml, editor.config.json, hashCode e uidmap.map. Nessuna immagine `src` del manifest del template risulta mancante. I due archivi condividono 19 percorsi; nessun file non-directory condiviso ha contenuto identico. Le differenze dettagliate di _id, date di esportazione/aggiornamento, nomi delle risorse e layout sono nei diff integrali.

Maschera `data_source` del funzionante, riportata esattamente senza interpretare l'ordine dei bit:

```text
10010010000000000000100100100000,00000000000000000000000000000000,00000000000000010000000100001000,00000100010000000000000000000000,00000000000000000000000000000000,0000000001
```

Maschera dell'originale:

```text
10010000000000000000100100100000,00000000000000000010000000000000,00000000010000000110001011011000,00000000101000000000101000000000,00000000000000000000000000000000,0000000001
```

## Perché il template viene accettato

L'evidenza più forte è che **regione e geometria sono uguali**, mentre cambiano protocollo e richieste dichiarate nella maschera data_source. La differenza normal/photoAlbum e la ricolorazione possono spiegare richieste funzionali diverse; la correlazione non dimostra la semantica dei singoli bit. Quindi la prima ipotesi è una differenza nelle capacità richieste/compatibilità del pacchetto, non una stringa CN da trasformare in Global. Non sono permessi del filesystem: sono dichiarazioni nel JSON del pacchetto, il cui confronto esatto nella specifica mod non è stato decodificato qui.

Entrambi gli archivi hanno la struttura ZIP completa e le stesse anteprime principali. La presenza dei cinque stili e dei WEBP non prova che siano necessari per superare il controllo. L'originale che funziona disattivando la verifica mostra inoltre che un rifiuto del controllo non equivale a un binario incapace di funzionare sul dispositivo.

Per attribuire la causa a protocollo o a specifici bit servirebbe il risultato del controllo della mod o un confronto controllato sul dispositivo. Questa analisi non inventa quella prova.

## Packaging su template e valori predefiniti

S5 Studio 0.3 usa il template della root e ne verifica lo SHA-256 prima di ogni build normale. Se manca o cambia, la compilazione si ferma: nessun fallback alla costruzione ipotetica dello ZIP. I nuovi progetti ricavano nome, autore, versione, ID, sfondo nero e AOD dal template; metadati completi e capacità sono conservati anche nella configurazione di default in data/template-defaults.json. Il progetto iniziale è projects/Primo_test_template.s5faceproj.

Il packager sostituisce esclusivamente **resource.bin e 28 anteprime** in preview/ e resources/_preview/. Mantiene formato e dimensioni di ogni anteprima; i WEBP sostituiti sono statici. Preserva esattamente i record locali compressi, contenuti, nomi, ordine, attributi, date, extra field e commenti di tutti gli altri file e directory. Aggiorna solo CRC/dimensioni delle voci sostituite e offset della directory centrale. Non aggiunge report o altri file al ZIP: i report sono esterni.

Per mantenere description.xml e manifest.xml intatti, il binario nuovo riceve l'ID completo del template `120917386745`. La CLI EasyFace 4.23 usa Int32 e fallisce se riceve direttamente quel valore: il backend compila con l'ID intermedio verificato `167210065`, poi assegna l'ID del template nel campo ASCII di 64 byte del solo binario generato. Gli ID del progetto non cambiano l'identità del pacchetto locale. L'installazione può sostituire lo slot del quadrante originale.

`scripts/package.ps1` crea l'app desktop e controlla il template prima di confezionarla. Il packaging del quadrante è in s5studio/template_package.py, condiviso da GUI e CLI.

```powershell
python main.py apply-template progetto.fprj quadrante_funzionante.zip cartella_output
python main.py apply-template projects/Primo_test_template.s5faceproj quadrante_funzionante.zip cartella_output
python main.py validate-template quadrante_funzionante.zip cartella_output/progetto_TEMPLATE.zip
python main.py template-info --report docs/template-build-profile.json
```

Per FPRJ occorrono images/ e, se presente, AOD/ accanto al progetto, più Screen Bitmap 480x480. Il compilatore predefinito è tools/easyface-4.23/Compiler.exe; è disponibile --compiler per un percorso diverso. Gli output esistenti non sono sovrascritti.

## Validator e limite della garanzia

La firma strutturale comprende tutte le voci in ordine, proprietà ZIP, hash dei file preservati e dei loro record compressi, formati/dimensioni delle preview. Fingerprint del template: `59e5e50128915342b718765026ef2091f8e9595241861c0554f958bdd42d422b`. Il validator controlla il template prima del patching, lo ZIP temporaneo e il file finale prima di pubblicare la build. Controlla CRC, ID, limiti e riferimenti del nuovo binario, oltre ai binding richiesti dalla compilazione.

**Conformità strutturale non significa firma crittografica o compatibilità garantita.** hashCode, uidmap.map, editor.config.json e manifest descrivono il progetto originale: conservarli non li rigenera per il payload nuovo. I tre valori hashCode non coincidono con lo SHA-256 diretto di alcun file dell'archivio; il loro algoritmo resta sconosciuto. La maschera capability preservata potrebbe non descrivere nuovi widget. Il template ha cinque stili normal/AOD, mentre il backend Studio crea una schermata normal e, per default, una AOD: le risorse/layout originali rimangono nel contenitore. Queste differenze sono dichiarate nei report, non nascoste dal validator.

Sono passati **30 test**, incluse compilazioni reali di Digitale/Analogico/Salute/AOD e FPRJ, conservazione dei record compressi, default letti dal template e rifiuto di file di sistema alterati, preview errate e binari corrotti. Il ZIP pronto S5_Primo_Test_TEMPLATE.zip è strutturalmente conforme; il nuovo payload richiede ancora la prova sulla mod e sull'orologio con le impostazioni usate per il template funzionante.

L'eseguibile S5Studio-0.3.exe è stato confezionato tramite scripts/package.ps1 e provato separatamente: self-test, UI Qt, caricamento dei default e compilazione reale su template passati. Il test packaged è in executable-build-test-0.3.json; il validator CLI sul ZIP pronto è in cli-validation-0.3.json. La schermata dei valori predefiniti è in screenshots/template-defaults-0.3.png.
