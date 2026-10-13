# Distribution scope and third-party resources

[English README](../README.md#licenseattributions) · [Italian README](../README.it.md#licenseattributions) · [Third-party notices](../THIRD_PARTY_NOTICES.md)

The **MIT license covers original S5 Studio application code and documentation**. It does not grant additional rights in third-party tools, artwork, templates, fonts or trademarks. This page records the existing distribution boundaries; it does not add permissions that are absent from the supplied materials.

## Current components

| Component | Current record | Publication implication |
| --- | --- | --- |
| Original Studio Python, frontend and Lua code | MIT, [LICENSE](../LICENSE) | Preserve copyright/license notice |
| Python, Qt/PySide6/Shiboken, Chromium, Pillow, Tailwind and PyInstaller | Separate dependency licenses/notices in [licenses/](../licenses/) | Retain applicable notices and satisfy each dependency's distribution terms |
| EasyFace 4.23 `Compiler.exe` / database | External compiler, included in the requested personal build; public redistribution permission not established in the current notices | Upstream download or confirmed permission is needed for the chosen public distribution model |
| `quadrante_funzionante.zip` / Suit and tie | User-supplied reference; protected records retained in exported packages; not licensed by Studio | Public inclusion requires its own permission assessment |
| Recovered hands, weather images, compasses and discs | Original authors' artwork from 39 user-supplied watchfaces | Attribution/provenance is preserved, but attribution alone is not redistribution permission |
| Personal hand/disc imports, including branded graphics | User-provided assets, with no blanket public license established here | Verify rights for each asset intended for public inclusion |
| Selected fonts embedded in projects | Supplied by the project author; Windows fonts are not automatically bundled with the app | Project portability does not establish font redistribution permission |
| Bulova example project | Explicitly requested user-supplied example, two styles and 14 embedded assets; the only bundled project | Its assets keep their own rights; the Studio MIT license does not cover third-party artwork/fonts/marks |
| Original S5 Studio SVG banner | Original vector artwork added with this documentation | Covered by the project's MIT license; no third-party bitmap or embedded font |

The existing personal 2.7 executable includes the compiler, template and supplied graphics. It must not be described as an entirely MIT-licensed bundle. The current packaging script has not been converted to a public profile that excludes components with unconfirmed permissions.

## Repository versus executable

`.gitignore` excludes `data/`, original `quadranti/`, projects, the template archive, compiler files and generated EXEs. It does **not** exclude the tracked derived catalogs under `resources/hand-sets/` and `resources/disks/`. Those files require the same provenance/permission review before making the repository public. Ignoring a source corpus does not automatically clear its copied images for publication.

The source clone also lacks inputs required to reproduce the personal bundle. The runtime staging script expects the supplied 595-model base catalog and associated graphics, in addition to the integrated personal sets. A public source release and a self-contained public executable are separate artifacts with separate completeness and distribution requirements. [Build prerequisites](INSTALLATION.md#running-from-source).

Existing analysis records can contain personal file paths and third-party metadata. Review the files selected for publication; do not interpret a successful build or an integrity hash as permission or a privacy audit. No repository visibility change, release upload, asset removal or license change was performed as part of the README update.

## Attribution boundaries

S5 Studio is independent of Xiaomi and the watch brands used in reference artwork. HaloX78's Ferrari watchface is credited as a creator's design, not as an OEM Xiaomi package. Public API examples from m0tral inform interoperability; the Studio Lua runtime is original code. Mi Create and UnpackMiColorFace sources are not incorporated into the application.

Historical notices and file provenance remain in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md), the [library inventory](library-analysis/inventory.md) and versioned runtime manifests. They are evidence of origin and inclusion, not a grant of rights by the respective owners.
