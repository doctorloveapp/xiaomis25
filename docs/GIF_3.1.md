# GIF layers and compatibility limits — S5 Studio 3.1

[English overview](../README.md) · [Italian overview](../README.it.md) · [Installation](INSTALLATION.md)

## Rules for version 3.1

| Condition | Preview and ZIP behavior |
| --- | --- |
| Visible normal GIF | At most **10 included frames per GIF**, checked in every style |
| More than 10 included frames | Counter and explanation shown; ZIP button disabled; backend refuses export before compilation |
| Visible normal GIF and main analog hands | Hour/minute hands remain; seconds hand and its shadow are omitted |
| Visible normal GIF and small seconds indicators | Small civil seconds, second digits used as pointers and continuous tenths indicators are omitted |
| Visible normal GIF and a chronograph | Crono, Crono Pro and Only Crono activation are unavailable; all chrono indicators, including tenths and POST, are omitted |
| Hidden or deleted normal GIF | The style's saved seconds and chronograph settings become available again |
| Another style without a visible GIF | Its own seconds and chronograph continue to work normally |
| Explicit AOD GIF | One static first included frame; independent AOD composition remains editable and exportable |

The rule applies to a **visible GIF object**, including when PC playback is paused or only one frame is included. Hiding the GIF removes the restriction; hiding only its clock hand does not enable a chronograph. Transparent/zero-opacity GIF objects still count if their visibility switch is on. The limit of 10 is a Studio policy, not an identified firmware frame or byte-size limit.

## Why these limits exist

The owner confirmed GIF playback on a real S5 with version 3.0 but reported intermittent seconds-hand jumps with the full-screen Gatto composition, despite correct 1 Hz native pointer settings. Nine active 480 × 480 PNG frames still caused about 7.5 image changes per second. Reducing the stored frame count alone does not guarantee low drawing/decoding work per second. The precise firmware bottleneck has not been profiled. [Audit and measured tradeoffs](AUDIT_GATTO_GIF_3.0.md).

Version 3.1 implements the requested conservative combination rules. It does not claim to increase the hardware's rendering capacity or guarantee smooth playback for every GIF. Image dimensions, playback speed and other live elements still affect performance and package size.

## Editor workflow

1. Add a static image and/or **＋ Gif**. Import still decodes all frames within the existing 300-frame / 32-million-pixel limits.
2. Select **10 or fewer** included frames. Excluded frames remain editable in the draft; Delete excluded frames and Undo remain available. Checking frames preserves gallery/inspector scrolling.
3. Set speed, position, size and layer order. A visible GIF shows a warning explaining the seconds/chronograph restrictions. Relevant controls and the chronograph preview button are disabled. Excluded indicator layers are marked **Esclusa con GIF / Excluded with GIF**.
4. Configure AOD separately. Normal GIFs are not copied there. Adding or editing an AOD layer enables its export; Include AOD in ZIP is also available. Choose a minimal time display without animation if desired.
5. Export ZIP. The exporter applies restrictions to a detached runtime copy, preserving the original `.s5faceproj` settings. The project file delivered beside the ZIP also retains those editable settings.
6. To use seconds or a chronograph again, hide/delete the GIF in that style, or use a separate style without a visible GIF. Re-export and reinstall to change the installed watchface.

## Implementation and validation

The preview renderer and EasyFace source generator share the same policy. Main seconds and their shadows are not emitted; small seconds/chrono layers are hidden in the runtime copy, and Pro flags are disabled there. The watch receives no active chronograph controller/tap handler for a GIF style. The GIF playback runtime remains unchanged.

Every new `build-report.json`, inside and beside the ZIP, includes **`gifSafety`** with the policy version, frame limit, affected styles, GIF IDs and excluded indicator IDs. The semantic validator checks that record against the runtime project and rejects native seconds pointers or active chrono entry points in GIF styles. A mixed-style export can retain an active Pro controller in its non-GIF style. Existing 3.0 packages retain their own recorded 20-frame policy when validated; recompiling them in 3.1 applies the new limits.

Passed **96 focused source tests**, **9 source-editor checks** and **2 compiler/ZIP integration tests**. Checks cover the 10/11-frame boundary, preserved editable preferences, hiding/showing GIFs, cancelled chrono preview, three UI languages, scroll position, native/long GIF backends, independent styles, AOD and rejection of a reintroduced seconds pointer. All eight Lua source modules remain unchanged from 3.0. No isolated executable launch or regression backup is performed.

The requested restrictions still require the owner's device test. The earlier successful GIF playback report describes 3.0 and does not certify all 3.1 combinations.

[Source validation](validation-editor-3.1.json) · [Editor checks](gif-policy-editor-3.1.json) · [Mixed GIF/Pro export](export-validation-3.1.json) · [Native/long GIF exports](export-validation-gif-paths-3.1.json) · [Executable integrity](executable-build-3.1.json) · [Historical GIF 3.0 architecture](GIF_3.0.md)
