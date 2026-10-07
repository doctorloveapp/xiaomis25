# Componenti e provenienza

S5 Studio usa codice applicativo originale. I formati e gli strumenti pubblici indicati nel piano sono stati studiati per interoperabilità; i sorgenti Mi Create e UnpackMiColorFace non sono incorporati nell'applicazione.

- **PySide6 / Qt 6.9.1 / Shiboken6** — Qt Project, https://www.qt.io/qt-for-python. Dipendenze esterne; le licenze installate sono conservate in `licenses/`. Il pacchetto Python sorgente rimane disponibile e l'app non pone restrizioni alla modifica o al debugging di queste librerie.
- **Pillow 11.3.0** — https://python-pillow.org. Licenza Pillow conservata in `licenses/`, compresi gli avvisi delle librerie di immagini quando presenti.
- **Python 3.13.5** — Python Software Foundation, https://www.python.org. Il runtime viene incluso da PyInstaller; licenza conservata in `licenses/`.
- **PyInstaller 6.17.0** — https://pyinstaller.org. Strumento di confezionamento; non cambia la licenza del codice applicativo. Licenza/bootloader notice conservata quando disponibile nel pacchetto installato.
- **EasyFace Compiler 4.23** — m0tral, https://github.com/m0tral/EasyFace/releases/tag/v4.23. Binario proprietario esterno scaricato per le prove locali richieste. Non incluso nell'eseguibile o negli archivi di distribuzione S5 Studio. Il download separato registra URL e hash; la redistribuzione del compilatore non è dichiarata autorizzata.
- **S5_Custom_digital_original.mwz** — campione Xiaomi fornito dall'utente. Immutato; utilizzato per studio e test, escluso dagli archivi di distribuzione e dai template grafici.
- **Font Windows** — letti dalla macchina in uso, senza includerli nella distribuzione dell'app. Un progetto che incorpora un font scelto dall'utente conserva quel file per portabilità; l'utente sceglie i propri asset.

Le cornici, cifre e grafiche dei modelli Studio sono generate dal codice originale. Le librerie personali di lancette e icone 0.5 provengono invece dai quadranti forniti dall’utente, come indicato sotto.

## Aggiunte 0.4

- **Tailwind CSS 4.3.3** — Tailwind Labs, https://tailwindcss.com. CSS compilato offline con CLI ufficiale; licenza MIT in licenses/Tailwind-MIT.txt. Node e i pacchetti di sviluppo non sono inclusi nell’eseguibile.
- **QtWebEngine / Chromium** — parte della dipendenza PySide6. Il renderer e QtWebChannel sono inclusi da PyInstaller; licenze Qt già conservate in licenses/, riferimenti e avvisi Chromium: https://doc.qt.io/qt-6/qtwebengine-licensing.html. Nessuna restrizione aggiuntiva alla modifica delle librerie.
- **quadrante_funzionante.zip / Suit and tie** — riferimento fornito dall’utente. Non modificato né incluso nelle distribuzioni. Il packaging locale conserva i record protetti del template e rigenera i metadati del nuovo payload. La 0.4 importava i gruppi grafici Suit and tie; questo metodo è stato eliminato nella 0.5. Il riferimento locale rimane necessario per la compilazione.
- **ORIGINALE_quadrante / Ferrari** — attribuito a HaloX78 nei metadati e confermato dall’utente; non OEM Xiaomi. Usato in sola lettura per confronto, escluso dalla distribuzione.
- **ILSpyCmd** — tool esterno usato soltanto in research per ispezionare l’interfaccia binaria della toolchain; codice decompilato non incorporato nel software o nelle distribuzioni.

## Librerie personali 0.5

`quadranti/` è il corpus fornito dall’utente, trattato in sola lettura. `data/hand-presets/` contiene 124 bitmap di lancette intatte con pivot nativi, e `data/weather-presets/` 18 icone; `data/watchface-library.json` conserva autore, quadrante, tema, percorso originario e SHA-256. I diritti delle grafiche rimangono dei rispettivi autori. Le copie locali sono predisposte per l’uso personale richiesto, non accompagnate da una licenza di redistribuzione degli asset.

Gli archivi locali 0.5 includono queste librerie derivate, non i pacchetti originali né il compilatore. Le complicazioni Studio usano cornici, etichette e cifre proprie; possono utilizzare le icone meteo selezionate dalla libreria personale. Nessun sorgente decompilato di terzi è incorporato.
