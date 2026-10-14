# Installation reference

[English overview](../README.md#installation-guide) · [Italian overview](../README.it.md#installation-guide) · [Documentation](README.md)

## Windows executable

The documented **personal 2.9 build** is `S5Studio-2.9.exe`, targeting Windows x64. It contains Python 3.13.5, Qt/PySide6 6.9.1, the offline UI, Lua modules, supplied catalogs, the verified template and EasyFace Compiler 4.23. The compiler requires **.NET Framework 4.7.2 or later**. Python and Node do not need to be installed on the destination PC.

Check the asset description in [GitHub Releases](https://github.com/doctorloveapp/xiaomis25/releases) before downloading. The repository's automatically generated source archives do not include the personal executable or all inputs needed to reconstruct it. This guide documents the existing bundle, not a claim that every release asset is already public or has identical contents.

Save the current project and close the older version before opening 2.9. Launch the EXE directly or use `Avvia_S5_Studio.cmd`, which prefers 2.9 when present. Keep the launcher beside the EXE if you use it. No adjacent resource folders are needed by this personal bundle. The application extracts its bundled resources to a temporary directory at startup; extraction is normal for its PyInstaller one-file format.

The compiler, template and supplied graphics have separate distribution conditions. Their presence in a personal EXE does not establish public redistribution permission. Read [distribution scope](DISTRIBUTION.md) before publishing that asset.

## Persistent files and paths

| Location | Contents / behavior |
| --- | --- |
| User-selected `*.s5faceproj` | Portable project document with images and selected font files; schema 1/2 read, schema 2 written |
| `%LOCALAPPDATA%/S5Studio/` | EXE preferences, recovery and personal catalogs; writable data is separate from extracted resources |
| `%LOCALAPPDATA%/S5Studio/settings.json` | Application language and compiler preference; other keys are preserved |
| `%LOCALAPPDATA%/S5Studio/dialog-paths.json` | Last directory per file-dialog category |
| `%LOCALAPPDATA%/S5Studio/hand-sets/catalog.json` | Personal hand sets and edits; synchronized for personal builds without modifying this source catalog |
| `<repository>/data/` | Working data when running from source, including `dialog-paths.json`; intentionally gitignored |
| `tools/easyface-4.23/Compiler.exe` and `DeviceInfo.db` | Source-mode default compiler location; do not rename the database |
| `quadrante_funzionante.zip` | Source-mode default reference template at repository root |
| Chosen export directory | ZIP, `resource.bin`, equivalent `.face`, previews, project, FPRJ/bitmaps, log and `build-report.json` |

The source-mode paths are relative to the repository; the EXE resolves read-only resources inside its extracted bundle. Moving the EXE does not move the persistent user-data directory. Project dialogs continue to ask for a file name when saving, while remembering the category's last directory.

## First watchface

1. Choose an Analogico, Digitale or Salute starting layout, import the artwork and position layers.
2. Choose hand models or custom PNG/SVG graphics pointing toward twelve o'clock. Set pivots, length/thickness and optional shadows; verify the complete preview before export.
3. Duplicate styles if needed. Each normal style owns its layers; AOD is shared. New projects use a personal ID to reduce collisions with the template's original ID.
4. Add complication slots and choose their allowed sources/default selection. The editor allows up to 16 slots; confirm the actual design on hardware rather than assuming a firmware maximum.
5. Configure AOD. It excludes seconds and chronograph indicators; select an economical static design.
6. Save `.s5faceproj`, select **Esporta ZIP**, choose the destination and wait for the completed-build notification. The generated previews use simulated values but include the visible layers.
7. Copy the ZIP to the phone without extracting it. Connect/synchronize the watch and use a compatible local uploader. Consult the [Capabilities FAQ](../README.md#why-does-local-installation-fail-with-capabilities) if the local path rejects it.
8. Verify time, sources, all styles, complication choices and sleep/AOD behavior on the actual watch. Re-export and reinstall after changing the PC project; an installed ZIP is not updated automatically.

## Bundled example and existing projects

The only bundled project is `resources/examples/Bulova.s5faceproj`. Open it through **Project and AOD → Open Bulova example**, then save your own copy. The bundle retains the hand/disc catalogs and excludes all other personal projects, autosaves, preferences and dialog history. Your existing project files remain on your PC and can be opened through **Open**.

## Reference hashes

These hashes identify the original local inputs and delivered executable. They are integrity records, not cryptographic vendor signatures or proof of redistribution permission. A rebuilt executable requires its own hash/report.

| File | SHA-256 |
| --- | --- |
| `S5Studio-2.9.exe` — delivered personal build | `fe5508ae527e1f7d7c367936ce9564f19088aff73f58250a3f0aacc1f53c9116` |
| EasyFace 4.23 release archive | `5b62773369c10c3402f369e8aa579f13393af359d0214c0d979464e5cc776cef` |
| `tools/easyface-4.23/Compiler.exe` | `bfb8c3b6666b79de165884d832c69d46e5bbfa581c65c1e188cddfc4b9d6723a` |
| `quadrante_funzionante.zip` | `5c7a3bb0c81762e7bb0749fd1b1cd941e0578d8e0eec0d567b37c44dd6695627` |
| `S5_Custom_digital_original.mwz` — analysis reference | `33fb3a1dfc162b3121f69ed0be66bb97b90f156ea3bda6dd398437ca0d5f9f55` |

```powershell
Get-FileHash -LiteralPath .\S5Studio-2.9.exe -Algorithm SHA256
python scripts/verify_bundle.py S5Studio-2.9.exe --report build/bundle-check.json
```

The second command requires the development environment and PyInstaller. It inspects embedded records without launching the EXE. The recorded 2.9 check verified **1,267 resources, 45 application Python modules, the entry point and seven Lua modules**. [Bundle report](executable-build-2.9.json) · [Toolchain record](../tools/toolchain.json) · [Template analysis](RAPPORTO_TEMPLATE_FUNZIONANTE.md).

## Running from source

Use Python 3.13 in the documented Windows environment. The editor dependencies are pinned in `requirements.txt`; development tools are in `requirements-dev.txt`.

```powershell
git clone https://github.com/doctorloveapp/xiaomis25.git
cd xiaomis25
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

The commands use the virtual-environment interpreter directly, so activating a PowerShell script is unnecessary. Subsequent examples using `python` assume it resolves to that environment. The application UI supports Italian (default), English and Simplified Chinese. Choose Language in the toolbar; see [i18n settings and extraction](I18N_2.9.md). The checked-in compiled CSS is sufficient to run it; use Node/npm only to change the CSS:

```powershell
cd frontend
npm ci
npm run build
cd ..
```

**Export prerequisites:** obtain EasyFace 4.23 from its [upstream release](https://github.com/m0tral/EasyFace/releases/tag/v4.23), preserve `Compiler.exe` and `DeviceInfo.db` together, and verify the toolchain hashes. That upstream release lists Mi Watch S5 support. Supply the verified template and any external assets your project requires. There is no verified CN/Global compiler switch; the configured target is **MiWatchS5 / 562**.

**Reproducing the personal EXE:** `scripts/prepare_runtime.py` additionally requires `data/watchface-library.json`, its original hand/weather/compass assets, `resources/hand-sets/`, `resources/disks/`, `resources/examples/Bulova.s5faceproj`, toolchain records, the template and license files. The current staging code explicitly expects the original **595-model catalog** from the supplied corpus. A fresh source clone does not contain all these inputs and cannot reproduce the identical 2.9 bundle by installing Python packages alone.

For a locally available, appropriately authorized corpus, `scripts/create_watchface_library.py` builds the library from the saved corpus analysis, and `scripts/create_compass_catalog.py` builds compass resources. `scripts/create_disk_catalog.py` handles disc recovery. These are corpus-specific utilities, not public asset downloaders. Preserve the original files and provenance; see [the inventory](library-analysis/inventory.md).

```powershell
python -X utf8 scripts/sync_hand_sets.py
powershell -File scripts/package.ps1
```

Preflight rejects missing/altered resources; packaging also repeats hand-set synchronization. The output is the **personal** `S5Studio-2.9.exe`, followed by static bundle validation. The script's current resource selection has not been converted to a generic public-distribution profile. [Contribution workflow](../CONTRIBUTING.md) · [Distribution scope](DISTRIBUTION.md).

## CLI reference

File names below are examples. Create/save the input project first; replace output names with those actually produced by the build.

```powershell
python main.py --help
python main.py self-test
python main.py render project.s5faceproj build/preview.png --variant 0
python main.py build project.s5faceproj --compiler tools/easyface-4.23/Compiler.exe --output build/export
python main.py apply-template project.s5faceproj quadrante_funzionante.zip build/export
python main.py apply-template project.fprj quadrante_funzionante.zip build/export
python main.py validate-template quadrante_funzionante.zip build/export/watchface.zip --report build/template-check.json
python main.py inspect build/export/watchface.zip
```

Create the destination parent directory before a standalone `render` or a report command that does not create it. `--variant` uses indexes 0–4; `render --aod` renders the shared AOD. Studio-generated FPRJ can restore the embedded project after hash checks, including styles and slots. External FPRJ support is limited to widgets that can be reconstructed consistently, including images, digits, image-value lists and hands; unsupported widgets are rejected.

Historical editor smoke commands, sample projects and package names are retained in [version history](CHANGELOG.md). Personal example ZIPs and `projects/` are not promised as public release contents.
