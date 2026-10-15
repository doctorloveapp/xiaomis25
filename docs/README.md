# S5 Studio documentation

[English overview](../README.md) · [Italian overview](../README.it.md) · [Releases](https://github.com/doctorloveapp/xiaomis25/releases)

Current application version: **3.1**. Previous device report (2.7; seven original Lua modules unchanged, 3.0 GIF playback confirmed by owner with native-seconds jitter reported): **Xiaomi Watch S5 M2530W1 / firmware 3.221.024**, user-confirmed on **2026-10-13**. Historical guides describe their own release; the current guides take precedence for present behavior.

## Guides

| Document | Language | Contents |
| --- | --- | --- |
| [GIF restrictions 3.1](GIF_3.1.md) | English | 10-frame cap, seconds/chrono exclusions, preserved settings and independent AOD |
| [GIF layers 3.0](GIF_3.0.md) | English | Frame editing, native/LVGL export, static backgrounds and independent AOD |
| [Internationalization 2.9](I18N_2.9.md) | English | Three languages, aligned header, Chinese fonts and validation |
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

## Evidence for build 3.1

| Record | What it establishes |
| --- | --- |
| [Source validation](validation-editor-3.1.json) | 96 focused tests, including policy boundaries and preserved settings |
| [Source editor](gif-policy-editor-3.1.json) | 9 checks: disabled seconds/chrono, restoration, AOD, scrolling and three languages |
| [Mixed GIF/Pro export](export-validation-3.1.json) | Separate GIF and active Pro styles, with two AOD views and checked binary exclusions |
| [Native/long GIF exports](export-validation-gif-paths-3.1.json) | Native and long-schedule backends, static artwork and AOD |
| [Executable integrity](executable-build-3.1.json) | Static resource/source verification and exact file hash |
| [Set integration](hand-set-integration-3.1.json) | 13 sets checked; no changes; catalogs retained |
| [Runtime manifest](runtime-manifest-3.1.json) | Embedded resources; Bulova remains the only example |

## Historical evidence for build 3.0

| Record | What it establishes |
| --- | --- |
| [Gatto performance audit](AUDIT_GATTO_GIF_3.0.md) | Italian assessment, package measurements and three temporary native compiler probes; no production changes |
| [GIF device report](hardware-gif-3.0.json) | Owner confirms playback and reports intermittent seconds-hand jumps; cause not measured |
| [Current source validation](validation-editor-3.0.json) | 98 focused tests; initial 162-test validation retained as history |
| [Current source editor](gif-hotfix-editor-3.0.json) | 7 checks: AOD access/export, frame limit, exact scroll preservation and three languages |
| [Gatto diagnosis](gatto-gif-diagnosis-3.0.json) | 60/44 source frames, native bitmap duplication and likely timeout |
| [Gatto/AOD export](gatto-export-hotfix-3.0.json) | 20 frames, chosen static AOD, 9.76 s / 31.6 MB; original project unchanged |
| [Initial source editor](editor-3.0.json) | 10 checks from the initial 3.0 build |
| [Initial compiler export](export-validation-3.0.json) | Two styles/AOD with native, interleaved and long-schedule GIFs plus Crono Pro |
| [Executable integrity](executable-build-3.0.json) | Static source/resource verification and exact file hash |
| [Set integration](hand-set-integration-3.0.json) | Lorenz Star Trek added; 13 personal sets and 635 effective hand models |
| [Runtime manifest](runtime-manifest-3.0.json) | Included resources and hashes; Bulova remains the only example |

## Historical evidence for build 2.9

| Record | What it establishes |
| --- | --- |
| [Source validation](validation-editor-2.9.json) | 59 targeted tests; project compatibility and unchanged watch Lua |
| [Source editor](editor-2.9.json) | 16 checks, including all three languages and header alignment at two widths |
| [Chinese localization](localization-coverage-2.9-zh.json) | 161 rendered UI contexts, dynamic text and help |
| [Executable integrity](executable-build-2.9.json) | Static resource/source verification and exact executable hash |
| [Set integration](hand-set-integration-2.9.json) | Swatch Luce added; 12 personal sets and 632 effective hand models |
| [Runtime manifest](runtime-manifest-2.9.json) | Embedded files and per-file hashes |

## Historical evidence for build 2.8

| Record | What it establishes |
| --- | --- |
| [Source validation](validation-editor-2.8.json) | 54 targeted tests and unchanged seven-module watch runtime |
| [Source editor](editor-2.8.json) | 11 checks: language switching/startup, dynamic UI, user data and stable IDs |
| [Executable integrity](executable-build-2.8.json) | Static verification, included catalogs and exact file hash |
| [Rendered localization coverage](localization-coverage-2.8.json) | 161 contexts; refined labels, catalog captions, source/help text and conditional controls |
| [Earlier isolated EXE check](VERIFICA_ISOLATA_2.8.md) | Historical check of the earlier 2.8 hash; its localization findings were corrected in the refined build |
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
