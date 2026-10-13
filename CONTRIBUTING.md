# Contributing to S5 Studio

[English README](README.md#development) · [Italian README](README.it.md#development) · [Build prerequisites](docs/INSTALLATION.md#running-from-source)

## Development environment

The documented environment is Windows x64 with Python 3.13 and `requirements-dev.txt`. Node/npm are only needed to rebuild the checked-in Tailwind CSS. The complete personal executable additionally requires the external compiler, template and original catalog inputs described in the installation guide.

Before changing the project, run:

```powershell
python -X utf8 scripts/sync_hand_sets.py
```

Integrate new/updated personal sets into `resources/hand-sets/`; preserve source catalogs. Packaging repeats this check and validates PNGs, hashes and pivots. The installed application's catalog takes precedence over the source-mode catalog for the same ID. Do not introduce third-party assets into a public distribution without establishing their permissions.

## Changes and validation

- Preserve project compatibility, independent style data, layer order and calibration unless the change explicitly requires otherwise.
- Run checks for the changed behavior. Broaden tests when failures or unresolved concerns justify it; do not report old test counts as newly executed tests.
- For runtime/export changes, check both generated Lua and native binary bindings, AOD exclusion, pause/resume and representative styles. Use temporary compiler exports when necessary, not retained demonstration watchfaces by default.
- Update both README languages, the relevant guide and the versioned evidence report. Record physical owner tests separately from source tests and static bundle inspection.
- Preserve the user's existing `.gitignore` entries. Do not create regression backups or launch the executable in an isolated test environment. Source tests and static bundle verification are the project's established validation workflow.

```powershell
python -m pytest -q
python scripts/verify_bundle.py S5Studio-2.7.exe --report build/bundle-check.json
```

The full test suite includes compiler-dependent tests; supply the documented toolchain/fixtures before treating those results as representative. For documentation-only edits, verify Markdown structure, local links, anchors and factual consistency. Do not rebuild an already tested executable solely to change external documentation.

## Release workflow

1. Synchronize personal sets and update the requested application version when making a new software release.
2. Run the necessary source/editor/compiler checks and record their actual scope.
3. Review the selected assets and dependency notices for the intended distribution. The existing full bundle is personal; the staging script is not a generic public release profile.
4. Build the requested executable with `scripts/package.ps1`, which performs runtime preflight and set synchronization.
5. Verify the bundle statically and publish its exact SHA-256 with matching release notes. Preserve previous historical evidence without treating an owner report as independent certification.

Repository visibility changes and release uploads are separate maintainer actions. A successful build does not establish third-party redistribution permission. [Distribution scope](docs/DISTRIBUTION.md).

## Useful issue information

Use the repository's [issue tracker](https://github.com/doctorloveapp/xiaomis25/issues). Include application version, device model, exact firmware, companion-app version, reproducible steps and relevant export diagnostics. Distinguish PC-preview behavior from a real device result. Share only project assets and log excerpts you have permission to publish, and remove personal paths/data when appropriate.

For chronograph timing issues, include the selected source, range/angles, smooth flags, mode, elapsed duration and whether display sleep/AOD or a style change occurred. The application's `build-report.json` can help identify the generated bindings and runtime hashes.
