# S5 Studio documentation

[English overview](../README.md) · [Italian overview](../README.it.md) · [Releases](https://github.com/doctorloveapp/xiaomis25/releases)

Current application version: **2.8**. Previous runtime/device report (2.7, unchanged Lua): **Xiaomi Watch S5 M2530W1 / firmware 3.221.024**, user-confirmed on **2026-10-13**. Historical guides describe their own release; the current guides take precedence for present behavior.

## Guides

| Document | Language | Contents |
| --- | --- | --- |
| [Internationalization 2.8](I18N_2.8.md) | English | Language preference, Qt TS/QM, offline JSON and extraction |
| [Installation reference](INSTALLATION.md) | English | Executable/source setup, persistent paths, CLI and reference hashes |
| [Chrono Pro engineering](CHRONO_PRO.md) | English | Shared Lua scene, clocks, scheduling, fractions, transitions and AOD |
| [Distribution scope](DISTRIBUTION.md) | English | Code licensing, personal bundle and third-party asset boundaries |
| [Contribution workflow](../CONTRIBUTING.md) | English | Focused checks, set synchronization and release requirements |
| [Civil-hand fixes 2.7](EDITOR_2.7.md) | Italian | Q8 hour decoding and small-seconds animation |
| [Longines shared-scene composition](LONGINE_LIVELLI_2.6.md) | Italian | Calendar/pointers between moon disc and Pro hands |
| [Calendar simulation](EDITOR_2.6.md) | Italian | Shared day/month/year simulation |
| [Daily moon disc](DISCHI_LUNARI_2.5.md) | Italian | 59 positions, reference date, calibration and native lunar alternatives |
| [POST and calibrated arcs](EDITOR_2.0.md) | Italian | Hundredths/thousandths and endpoint mapping |
| [Variants, complications and packaging](ANALOGICO_VARIANTI_COMPLICAZIONI.md) | Italian | Native resources, configurable slots and semantic metadata |
| [Template analysis](RAPPORTO_TEMPLATE_FUNZIONANTE.md) | Italian | Inventory, metadata differences and protected records |
| [Local uploader analysis](ANALISI_UPLOADER_1.4.md) | Italian | Preview/name behavior and limits of the evidence |
| [Region and capabilities](REGIONE_E_TEST_LOCALE.md) | Italian, historical | No verified Region switch; early local-install observations |
| [Version history](CHANGELOG.md) | Italian | Retained release notes, commands, examples and earlier operating records |

## Evidence for build 2.8

| Record | What it establishes |
| --- | --- |
| [Source validation](validation-editor-2.8.json) | 43 targeted tests and unchanged seven-module watch runtime |
| [Source editor](editor-2.8.json) | 10 checks: language switching/startup, dynamic UI, user data and stable IDs |
| [Executable integrity](executable-build-2.8.json) | Static verification, included catalogs and exact file hash |
| [One-off isolated EXE check](VERIFICA_ISOLATA_2.8.md) | Host-Windows folder/profile isolation; startup, resources, save/reopen and language persistence; incomplete English labels recorded |
| [Set integration](hand-set-integration-2.8.json) | Personal catalog synchronization, originals preserved |

## Historical evidence for build 2.7

| Record | What it establishes |
| --- | --- |
| [Source validation](validation-editor-2.7.json) | 114 targeted tests passed; three generic integration tests omitted and actual export checked separately |
| [Real compiler export](export-validation-2.7.json) | Two Longines styles and AOD; input unchanged; temporary export completed in 11.09 s |
| [Executable integrity](executable-build-2.7.json) | 1,251 embedded resources, 43 application Python modules and seven Lua modules verified statically |
| [Hardware confirmation](hardware-test-2.7.json) | Owner-reported successful operation and declared device/firmware; not an independent laboratory test |
| [Set integration](hand-set-integration-2.7.json) | 11 personal sets / 629 effective hand models; source catalogs unchanged |
| [Runtime manifest](runtime-manifest-2.7.json) | Personal bundle contents and per-file hashes |
| [Documentation validation](documentation-validation-2.7.json) | Bilingual structure, local links/anchors, retained history and unchanged executable hash |

## Language maintenance

`README.md` is the international English entry point; `README.it.md` is its Italian counterpart. Keep their section order, release number, compatibility claims, hashes and risk notices aligned. New language-specific guides should state their language in this index and link back to both entry points. Existing technical guides remain in their original language until translated; no placeholder is presented as an available translation.
