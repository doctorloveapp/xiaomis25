# S5 Studio

![S5 Studio — watchface engineering for Xiaomi Watch S5](docs/assets/s5-studio-banner.svg)

[![Build 2.8](https://img.shields.io/badge/build-2.8-2563eb)](https://github.com/doctorloveapp/xiaomis25/releases) [![54 targeted tests passed](https://img.shields.io/badge/tests-54%20targeted%20passed-15803d)](docs/validation-editor-2.8.json) [![S5 device test user confirmed](https://img.shields.io/badge/S5%20device%20test-user%20confirmed-15803d)](docs/hardware-test-2.7.json) [![Code license MIT](https://img.shields.io/badge/code%20license-MIT-64748b)](LICENSE)

**English** · [Italiano](README.it.md) · [Releases](https://github.com/doctorloveapp/xiaomis25/releases) · [Documentation](docs/README.md)

S5 Studio is a Windows visual editor and compiler pipeline for Xiaomi Watch S5 watchfaces. It combines independent styles, sensor-driven layers and a shared Lua chronograph runtime with template-preserving packaging and export validation, turning custom artwork into configurable, working watchfaces.

**Target:** Xiaomi Watch S5 **M2530W1**, 480 × 480. **Application UI:** Italian (default) and English. Choose Language in the toolbar; the preference is saved in settings.json. Test badges describe recorded checks; the device confirmation refers to the unchanged watch runtime tested in 2.7, not a new hardware certification. [Internationalization guide](docs/I18N_2.8.md).

**2.8 localization refinement:** composed labels, catalog descriptions, tooltips, import dialogs, validation messages and chronograph readouts have been completed in English. Verification covers 161 rendered editor contexts, 54 targeted tests and 11 editor checks. The [earlier isolated test](docs/VERIFICA_ISOLATA_2.8.md) applies to the previous artifact's recorded hash; this updated EXE is checked statically. [Current verification](docs/validation-editor-2.8.json).

## Table of Contents

- [Features](#features)
- [Installation Guide](#installation-guide)
- [Technical Architecture](#technical-architecture)
- [Chrono Pro Documentation](#chrono-pro-documentation)
- [Compatibility](#compatibility)
- [Troubleshooting](#troubleshooting)
- [Common Questions](#common-questions)
- [Development](#development)
- [Documentation and Release History](#documentation-and-release-history)
- [License/Attributions](#licenseattributions)

## Features

| Capability | Implementation and design benefit |
| --- | --- |
| **Italian / English UI** | Live language switching, Qt Linguist TS/QM catalogs, offline JSON frontend and persistent application preference. Italian remains the default. |
| **Layer editor** | Images, text, live data, shapes, hands and discs; reorder, delete, duplicate, lock, undo/redo and Ctrl multi-selection. Drag, arrow keys and alignment operate on the selection. |
| **Artwork and geometry** | Import PNG/JPEG/WebP/BMP/SVG; scale beyond the viewport and crop to 480 × 480 on export. Rotate or curve text/live data; use rectangles, circles or ellipses with independent fill, outline and shadows. |
| **Hand sets** | Import named main/small-hand sets, edit pivots by clicking the graphic, pair hand shadows or generate them. Main hour selection can pair the matching minute/second models; each remains independently editable. |
| **Independent styles** | Up to five styles, each with its own layer collection and properties. Duplicate a style, then change its artwork or hands without hiding layers in the original. **Why:** a style is a complete composition, not a color overlay. |
| **Live data and complications** | Calendar, health, weather, compass and other mapped watchface channels; up to 16 configurable complication slots in the Studio project. Slots are layers and initially show the value alone. This is an application limit, not a certified firmware maximum. |
| **Calendar and rotating discs** | English weekday labels MON–SUN; full month names or JAN–DEC. Import/edit/delete discs, set pivots and shadows, or use a 59-position daily moon wheel. **Why:** the moon wheel derives its position from the date and does not lose days while the display sleeps. |
| **Motion and AOD** | Separate smooth-motion flags for normal hour/minute/second hands; optional smooth chronograph tenths. Seconds and chronograph indicators are excluded from AOD; normal-scene animations stop when AOD begins. |
| **Simulation** | Animated preview, zoom/pan, date simulation with day 1–31, month and year, and frozen chronograph readout. Preview values do not replace the live sources exported to the watch. |
| **Validated export** | Native EasyFace compilation, complete previews, template-based ZIP packaging and a per-build report. **Why:** binary resources, metadata, styles and Lua bindings are checked together before publishing the output file. |

The complete 2.8 build contains **629 hand models and 90 discs**, including assets recovered from 39 supplied watchfaces. These counts describe that build, not a freely redistributable asset library. See [distribution scope](docs/DISTRIBUTION.md).

## Installation Guide

### Prebuilt Windows application

1. Open [GitHub Releases](https://github.com/doctorloveapp/xiaomis25/releases) and read the asset list and distribution notes for the chosen release. A GitHub source archive is not the application executable.
2. For the documented 2.8 build, use **`S5Studio-2.8.exe`** on **Windows x64** with **.NET Framework 4.7.2 or later**. That personal build includes Python, Qt, the compiled UI, catalogs, template and compiler; Python and Node are not required on the destination PC.
3. Verify the downloaded file against the report accompanying that exact asset. Save your work and close the previous version, then launch the EXE or **`Avvia_S5_Studio.cmd`** if supplied. The application opens maximized.
4. Create/open a `.s5faceproj`, configure the normal styles and AOD, save, then select **Esporta ZIP** and choose an output directory.
5. Transfer the resulting ZIP to the phone without extracting it and install using a compatible local watchface uploader. Keep Bluetooth connected and the watch synchronized. Read the [Capabilities FAQ](#why-does-local-installation-fail-with-capabilities) before changing uploader settings.

**Distribution scope:** the current standalone build is a **personal bundle** containing an external compiler and third-party artwork. Its MIT code license does not establish redistribution permission for those components. A public release with a different resource set may have different installation requirements. [Details and prerequisites](docs/INSTALLATION.md) · [Third-party notices](THIRD_PARTY_NOTICES.md).

**Included example:** open **Project and AOD → Open Bulova example**. Bulova is the only bundled project (two styles, 14 embedded assets); save your edited copy to your own folder. Other personal projects, recovery files, preferences and dialog history are excluded. Existing `.s5faceproj` files on your PC remain compatible and can be opened normally. The hand/disc catalogs are retained.

**Included example:** open **Project and AOD → Open Bulova example**. Bulova is the only bundled project (two styles, 14 embedded assets); save your edited copy to your own folder. Other personal projects, recovery files, preferences and dialog history are excluded. Existing `.s5faceproj` files on your PC remain compatible and can be opened normally. The hand/disc catalogs are retained.

### Paths and file integrity

| Purpose | Location |
| --- | --- |
| Project document | User-selected `*.s5faceproj`; embeds the project's images and selected fonts |
| Installed application preferences, recovery and personal catalogs | `%LOCALAPPDATA%/S5Studio/` |
| Source checkout working data | `<repository>/data/` — intentionally gitignored |
| Compiler when running from source | `tools/easyface-4.23/Compiler.exe` with `DeviceInfo.db` |
| Default packaging template when running from source | `quadrante_funzionante.zip` at the repository root |
| Watchface output | Directory chosen in **Esporta ZIP**, including `build-report.json` |

```powershell
Get-FileHash -LiteralPath .\S5Studio-2.8.exe -Algorithm SHA256
```

SHA-256 of the **delivered personal 2.8 executable**:

```text
b1653e60b0c4ff83db1ee96465c4c6b1dd3a9456f12cee67267ddf82e25403d5
```

This hash identifies that exact file; a rebuild or differently packaged public asset will have another hash. Compiler, template and reference-package hashes are retained in the [installation reference](docs/INSTALLATION.md#reference-hashes).

## Technical Architecture

```text
Qt desktop / QtWebEngine + QtWebChannel / offline Tailwind UI
    -> Python project model, asset transforms and preview renderer
    -> Native widgets + one shared Lua scene per interactive style
    -> EasyFace 4.23: FPRJ -> resource.bin
    -> Template-preserving package assembly
    -> Binary / metadata / preview / Lua validation -> ZIP + build-report.json
```

| Component | Responsibility |
| --- | --- |
| `s5studio/model.py`, `render.py`, `frontend/` | Project state, independent style layers, geometry and desktop editing |
| `s5studio/native.py`, `native_graph.py` | Native FPRJ generation, compiler invocation and binary inspection |
| `s5studio/lua_runtime.py`, `s5studio/lua/` | Shared scene generation, chronograph state, coherent civil time and dynamic data |
| `s5studio/semantic_package.py`, `template_package.py` | Protected ZIP records, regenerated semantic metadata and final structural validation |
| `scripts/prepare_runtime.py`, `package.ps1`, `verify_bundle.py` | Personal runtime staging, executable packaging and static resource verification |

**Template surgery:** the verified template preserves **187 protected files and eight directory records**, including its capability data and `hashCode`. The compiler output and previews are replaced; `description.xml`, manifest, UID mapping and editor configuration are regenerated for the new resources. Keeping all those metadata files unchanged would describe the original watchface rather than the exported project.

The local validator checks protected records, CRCs, IDs, offsets, native references, style/slot mappings, previews and embedded Lua. A successful structural check **is not a Xiaomi cryptographic signature** and does not guarantee acceptance by an uploader's capability verifier. [Template analysis](docs/RAPPORTO_TEMPLATE_FUNZIONANTE.md) · [Packaging details](docs/ANALOGICO_VARIANTI_COMPLICAZIONI.md).

**Data boundaries:** mapped channels are watchface framework data, not arbitrary access to raw sensors. Three formatted-text channels observed in the reference corpus are not supported as dynamic text exports. Native widgets are used where possible; dynamic layers inside a shared Lua scene keep their live bindings and layer order. Unsupported interleaved widget types are rejected rather than silently flattened.

## Chrono Pro Documentation

### Modes and control sequence

| Mode | Setup | Tap sequence and large seconds hand |
| --- | --- | --- |
| **Classic chronograph** | Small hands mapped to Ore/Minuti/Secondi Crono; Crono Pro off | Start → Stop → Reset; ordinary large seconds remain independent |
| **Crono Pro** | Enable **Crono Pro** in the large seconds hand tab | Prepare at zero → Start → Stop → Reset; large seconds return to civil time at rest |
| **Only Crono** | Enable **Only Crono** in the same tab | Same Pro sequence; large seconds stay at zero at rest |

**Why one shared scene:** chronograph hour/minute/second hands must read one elapsed-time value and one tap handler. Separate widget VMs cannot be assumed to share globals or module state. Studio registers the measurement hands in one Lua scene per style, removing that dependency; it does not claim to have measured firmware VM isolation.

**How to configure six indicators:** use large chronograph seconds, small chronograph hours/minutes/tenths, and optional **Centesimi (POST)** / **Millesimi (POST)**. Ordinary small seconds, civil 24-hour hands and the moon disc keep their own data sources.

### Timing, motion and POST readout

- **Clock:** choose one available time source for the measurement; calculate elapsed time from timestamps, not the number of callbacks. Pro uses a monotonic clock when available, with an LVGL animation-phase fallback. The exact available clock depends on the firmware.
- **Running:** large chronograph seconds and chronograph hours/minutes advance in steps. Pro tenths can use ten steps per second or an optional **25 fps target** driven by `Anim.exec_cb`. Write-on-change avoids redundant pointer and shadow updates.
- **Transitions:** coordinated prepare/reset sweeps use **720 ms** at a 25 fps target. Full-circle hands return clockwise; bounded arcs stay within their calibrated scale. Normal hour/minute hands continue to show civil time.
- **POST:** hundredths and thousandths remain at their initial position while Running. At Stop, both animate to the fraction captured from the same frozen elapsed value. **Why:** readable precision indicators without continuous high-speed rotations or additional fast Running timers.
- **Precision:** complete fractions are 00–99 and 000–999; single-digit readout is also available. At 12.488 s, full fractions are 48 and 488. Three displayed digits **do not certify 1 ms measurement accuracy**; event delivery, clock resolution and suspension affect the result.
- **AOD and lifecycle:** entering AOD stops normal-scene animations immediately and uses the configured AOD view without seconds or chronograph hands. State is not persisted across a new Lua VM or watchface recreation; display sleep and VM destruction are distinct events.

For a full revolution use ranges 60 for seconds/minutes, 12 for 12-hour chronograph hours, 10 for tenths, 100/1000 for full POST fractions. For a bounded arc specify both value and angle endpoints: e.g. 0–999 mapped to 30°–140°. A value of 800 means 800 ms in the complete thousandths scale. Pivot and initial graphic orientation must also be calibrated.

[Current chronograph engineering guide](docs/CHRONO_PRO.md) · [POST and arc calibration](docs/EDITOR_2.0.md) · [Callback scheduling](docs/EDITOR_2.3.md).

## Compatibility

| Device / firmware | Status | Evidence and scope |
| --- | --- | --- |
| **Xiaomi Watch S5 M2530W1 · 3.221.024 · 480 × 480** | **User-confirmed on build 2.7** | Model and installed firmware explicitly supplied by the tester; successful operation reported on 2026-10-13 |
| Same model, other firmware versions | Not verified | Lua availability, native channels and uploader behavior may differ |
| Other Xiaomi/Redmi watches or Mi Bands | Unsupported target | Related public API examples do not establish package compatibility |
| Windows x64 + .NET Framework 4.7.2 or later | Personal EXE build target | Runtime and compiler requirements; bundle verified statically |
| Linux/macOS desktop or official-store publishing | Not validated | No packaged support or official publishing integration is provided |

The compiler target is **MiWatchS5 / 562**, with package device type **P62**. Historical profiles record m0tral mod **V3.52.0i**; the exact companion-app version used for the latest test was not separately confirmed. Device success is an owner report, not independent certification. Fps, battery consumption and raw firmware clock resolution were not measured. [Hardware confirmation](docs/hardware-test-2.7.json) · [Source tests](docs/validation-editor-2.8.json) · [Bundle report](docs/executable-build-2.8.json).

## Troubleshooting

| Symptom | Action |
| --- | --- |
| **Capabilities** rejected by the local uploader | See the [FAQ below](#why-does-local-installation-fail-with-capabilities); do not assume changing CN/Global is a fix |
| Generic `L00000000001` name or missing phone preview | Local uploader behavior was also observed with the reference package; compare watch/edit previews and the generated preview files before changing the design |
| Export cannot find the compiler or template | A source checkout does not include every personal runtime dependency; follow [source prerequisites](docs/INSTALLATION.md#running-from-source) |
| Watch differs from the edited project | Re-export using the current build and reinstall the new ZIP; already installed packages are not updated by changing the PC application |
| Wrong hand position or scale | Verify the source, range, initial angle and pivot; small civil seconds show actual simulated seconds rather than automatically starting at zero |
| A layer cannot be inserted between Lua-controlled hands | Check the widget type and shared-scene boundary; composite or selectable widgets not supported inside that scene must sit outside it |
| A live value is absent or stale | Verify the corresponding native channel and sensor/app data on the watch; preview examples are not live sensor readings |

[Local uploader investigation](docs/ANALISI_UPLOADER_1.4.md) · [Longines scene composition](docs/LONGINE_LIVELLI_2.6.md) · [2.7 civil-hand corrections](docs/EDITOR_2.7.md).

## Common Questions

### Why does local installation fail with Capabilities?

The same reference ZIP was accepted through the mod's online catalog but rejected by its local uploader. Disabling **Verify capability test** allowed local installation in the reported setup. This supports a difference between upload paths; it does not establish a universal firmware fix.

For a watchface you created and validated for **M2530W1**: confirm the device target, keep the watch connected, temporarily disable that check in the compatible mod if the local uploader rejects it, select the complete ZIP and inspect the installed result. Restore verification for routine use where possible. Disabling the check removes an uploader compatibility gate: it does not sign the package, validate unknown files or guarantee firmware safety. The mod is third-party software and is not distributed by this project.

EasyFace 4.23 exposes no verified Region switch. `deviceRegion=international` and `capability.region=CN` coexist in the supplied references; changing either string is not a demonstrated remedy. [Analysis and limitations](docs/REGIONE_E_TEST_LOCALE.md).

### Does the EXE work alone? Why is data/ gitignored?

The delivered personal 2.8 EXE includes its resources and works without adjacent `data/`, compiler or template folders. A source clone is different: `data/`, the original corpus, template and compiler are intentionally excluded. Rebuilding that identical bundle requires those inputs and their permissions. [Installation details](docs/INSTALLATION.md).

### Are styles and complications really independent?

Each normal style has independent layers, images, colors and hand settings. AOD is shared. Complication slots are movable layers with configurable source choices; 16 slots is Studio's project limit, not proof that every combination is practical on the device. [Editor and packaging model](docs/ANALOGICO_VARIANTI_COMPLICAZIONI.md).

### Is the moon disc an astronomical ephemeris?

No. The 59-position mode models a two-moon mechanical wheel: one daily step and a 59-day revolution. The default reference is 2026-09-26; calibrate its initial angle and day correction for your artwork. Native eight-phase lunar data is a separate source. [Moon-disc guide](docs/DISCHI_LUNARI_2.5.md).

### Can I redistribute every catalog image or the bundled compiler?

The source-code license does not grant rights to third-party artwork, fonts, templates or EasyFace. The present notices do not establish public redistribution permission for the full personal bundle. [Distribution scope](docs/DISTRIBUTION.md) · [Attributions](THIRD_PARTY_NOTICES.md).

## Development

Use **Python 3.13** for the documented Windows environment. Install `requirements.txt` to run the editor, or `requirements-dev.txt` for pytest, PyInstaller and Lupa. Lupa is a development test dependency, not part of the distributed runtime.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

The compiled Tailwind CSS is included in the repository. Node is only needed when rebuilding CSS; run `npm ci` and `npm run build` inside `frontend/`.

```powershell
python -X utf8 scripts/sync_hand_sets.py
python main.py build project.s5faceproj --compiler tools/easyface-4.23/Compiler.exe --output build/export
python main.py apply-template project.fprj quadrante_funzionante.zip build/export
python main.py validate-template quadrante_funzionante.zip build/export/watchface.zip
python main.py inspect build/export/watchface.zip
python -m pytest -q
```

Example file names above are placeholders for your own inputs/outputs. `apply-template` accepts Studio projects and supported FPRJ files; Studio-generated FPRJ restores embedded styles/slots after source-hash checks. External FPRJ widgets that cannot be reconstructed coherently are rejected.

`powershell -File scripts/package.ps1` builds the personal EXE after runtime preflight and set synchronization; `python scripts/verify_bundle.py S5Studio-2.8.exe` checks embedded hashes without launching it. The current packaging script expects the supplied personal catalog and is not a generic clean-clone release builder. See [Contributing](CONTRIBUTING.md) and [source prerequisites](docs/INSTALLATION.md#running-from-source).

## Documentation and Release History

- [Internationalization 2.8](docs/I18N_2.8.md) — language settings, translation extraction and contributor workflow.
- [Documentation index](docs/README.md) — current guides and evidence reports, with language labels.
- [Chrono Pro engineering](docs/CHRONO_PRO.md) — shared state, clocks, formulas, POST and lifecycle.
- [Installation reference](docs/INSTALLATION.md) — paths, dependencies, reference hashes and source builds.
- [Version history](docs/CHANGELOG.md) — retained release notes and earlier operating references, in Italian.
- [Latest device confirmation](docs/hardware-test-2.7.json) — user-reported 2.7 success, separately identified from automated checks.

## License/Attributions

**Original S5 Studio code and documentation:** [MIT License](LICENSE). The software is provided **as is, without warranty**. This is an independent interoperability project; it is not an official Xiaomi development tool or an official-store publishing service.

**Dependencies and research references:** Python/PSF, Qt/PySide6/Shiboken, QtWebEngine/Chromium, Pillow, Tailwind CSS and PyInstaller retain their respective licenses. **m0tral** provides EasyFace and public MiWatchLuaWatchfaces API examples. Mi Create and UnpackMiColorFace were studied for interoperability; their source is not incorporated into the application.

**Artwork and trademarks:** hand/disc/weather graphics and reference watchfaces retain their authors' rights; fonts require their own permissions. HaloX78 is credited as a watchface creator, including the Ferrari reference, which is not treated as an OEM Xiaomi design. Watch brands and model names identify references and do not imply affiliation or endorsement.

Read [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), [licenses/](licenses/) and [distribution scope](docs/DISTRIBUTION.md) before redistributing a bundle or catalog. **The application-code MIT license does not relicense the proprietary compiler or third-party assets.**
