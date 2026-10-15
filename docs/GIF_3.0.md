# GIF layers — S5 Studio 3.0

[English overview](../README.md) · [Italian overview](../README.it.md) · [Installation](INSTALLATION.md)

## Creating a composition

Studio now opens with **no layers and AOD disabled**. Named starting layouts and the Bulova example remain optional. The toolbar order is Image, Gif, Hands, Small hands, Disc, Live data, Analog compass, Complication, Time, Date, Text, Shape.

1. Use **＋ Immagine / ＋ Image** for static artwork, then **＋ Gif** for an animation. The GIF dialog accepts `.gif` only and remembers its own last directory.
2. All frames are decoded automatically, including GIF transparency and disposal. A smaller imported GIF starts centered on the watch canvas.
3. Position, resize and reorder the GIF like an image layer. It can sit above a static background, below hands, or between other supported layers. Artwork beyond the 480 × 480 viewport is clipped at export.
4. In **Animazione GIF / GIF animation**, set **Velocità (%) / Speed (%)**. 100% uses the source timing subject to the 25 fps ceiling; 200% requests twice the speed, 50% half the speed. The range is 25–400%.
5. Uncheck frames to exclude them from playback/export. Checkboxes update in place: the gallery, inspector and workspace keep their scroll position. **Elimina fotogrammi esclusi / Delete excluded frames** removes those entries from the project; Undo restores them. At least one frame must remain included.
6. Use **Avvia anteprima GIF / Play GIF preview**, or click a frame thumbnail to inspect it while playback is paused. Preview state is separate from the saved project and chronograph control state.
7. Keep **at most 20 included frames per visible normal GIF**, in every style. A counter and message show the limit; ZIP export is disabled until all styles comply. Excluded frames can remain in the saved project. A draft above the limit can still be imported, opened, edited and saved.
8. Save the portable `.s5faceproj`, add/configure Time or Hands as usual, then export ZIP. The ZIP contains the compiled animation resources and matching metadata; copying the original GIF into a package is unnecessary.

New hand groups start with **Tacche del quadrante / Dial ticks** disabled. Existing saved tick choices are preserved.

## AOD: always editable and exported as configured

**AOD remains accessible even when its export is disabled or the normal screen contains a GIF.** Switch to AOD and create the layers you want: for example, a plain time display on a black background. Adding or changing an AOD layer automatically enables AOD export. Simply inspecting the canvas does not change that preference. If export is disabled, the AOD canvas also offers **Includi AOD nello ZIP / Include AOD in ZIP**. Project settings retain an explicit AOD export switch.

**Normal GIF layers are not copied into AOD.** Its layer list is separate from the normal screen; deleting an AOD layer does not delete a normal-screen layer. Export compiles the chosen AOD composition with its positions, graphics and styling, alongside the animated normal screen.

**Why:** an independent, static AOD preserves the user’s design while avoiding continuous animation in the watch’s low-power display mode.

If you explicitly import a GIF while editing AOD, it exports as **one static image: the first included frame**. This static layer is exempt from the normal-animation 20-frame limit because only that image enters AOD. AOD has no GIF animation entry point or native sprite layout. All normal chronograph/seconds exclusions remain in force. AOD is shared across the project's normal styles, as in earlier versions.

## Export architecture and limits

`s5studio/gif_animation.py` stores complete PNG frames with their original duration and inclusion flag. It builds one playback schedule used by the PC renderer and both watch backends. Excluded frames never enter the watch animation sequence. The project retains excluded frames until they are explicitly deleted. The backend checks the 20-frame export policy before opening the output dialog or starting the compiler, including inactive styles. Hidden GIF layers are excluded from this check.

| Case | Backend | Why |
| --- | --- | --- |
| Uniform timing without repeated entries; at most 255 scheduled frames and interval at most 65,535 ms | Native EasyFace ImageList, compiled to `SpriteGroup` + `ImageArray` | Lets the firmware play the sequence without a Studio Lua polling timer |
| Variable frame holds requiring repeated entries | LVGL GIF entry point using `studio_gif.lua` | Reuses each included bitmap instead of encoding another bitmap for every hold |
| GIF between Lua-controlled indicators | `studio_gif.lua` inside the existing shared scene | Preserves the exact stacking order and keeps taps/chronograph measurement independent |
| Longer schedules or very long frame intervals | Separate LVGL GIF entry point | Avoids overflowing the observed one-byte native image-array frame count or two-byte interval |
| Explicit AOD GIF layer | Static first included frame | Removes animation work from AOD |

The Lua fallback uses an LVGL animation callback and writes a new image source only when the frame changes. It stops on page pause, screen OFF/AOD and object deletion; wake starts the sequence again. All **eight Lua source files are unchanged from the initial 3.0 build**, including the seven modules carried over from 2.9. Previously generated 3.0 packages remain valid under their original encoding report. Native sprite playback is delegated to the firmware's normal-screen lifecycle.

GIF import allows up to **300 frames and 32 million logical-screen pixels across all frames**; export allows **20 included frames per visible normal GIF**. Scheduling is capped at 6,000 entries. Playback loops continuously, with a minimum visible-frame duration of **40 ms** (25 fps maximum). Variable source delays are represented by repeated references to frame images; schedules needing finer timing are quantized, with cumulative rounding to limit drift. Large or very fast source animations therefore may not reproduce their original timing exactly.

**The 20-frame cap is a Studio export policy, not a discovered Xiaomi firmware limit.** No exact package-size limit has been verified for this watch. Frame dimensions, styles, static graphics and other resources still affect ZIP size. Twenty full-screen frames can produce a sizable package; the cap does not guarantee that every composition fits the watch’s available space.

The compiler also limits the entire Lua resource table to **256 files**, including other modules and graphics. An exceptionally large interleaved GIF may require fewer included frames; Studio reports this limit rather than dropping frames. Full-screen animation consumes more memory/rendering work than a small animated element. The 25 fps target is a configured ceiling, not a measured hardware performance guarantee.

## Gatto diagnosis and correction

The supplied `Gattos5faceproj.s5faceproj` contains **60 frames, 44 included**, and no enabled/configured AOD. Variable delays of 60/70 ms expanded those 44 images into **73 native schedule entries**, each re-encoded by the compiler. Including all 60 would produce 100 entries. The previous successful export contained an **84.0 MB binary / 90.6 MB ZIP**. The failed log ended at “App found, packing” without completion; the approximately 93-second job interval is consistent with preparation plus the **90-second compiler timeout**. This supports a timeout diagnosis, not a hard 44-frame firmware limit.

The correction encodes each included image once and reuses it for timing holds. A temporary test using **20 selected Gatto frames and a separately chosen static clock/text AOD** compiled and validated in **9.76 seconds**, producing a **31.6 MB ZIP** (65.1% smaller than the previous 44-frame export). The comparison also reflects the reduced frame selection. AOD was present, contained no animation, and its exported preview matched the configured AOD pixel for pixel. The original project was unchanged and the temporary output was removed.

## Validation

The native group target, interval, repeat count, initial frame and array count are checked against the binary and regenerated manifest/UID mapping. GIF resources participate in the existing ZIP CRC, protected-template, metadata-hash and Lua-injection checks. `build-report.json`, both inside the ZIP and beside it, includes `gifAnimations`, selected backend, frame counts, interval, cycle duration, speed, encoding version and export policy for every visible normal GIF layer.

The refreshed 3.0 passed **98 focused source tests**, **7 source-editor checks** and the real Gatto compiler/AOD export described above. Editor checks verify the exact unchanged scroll/checkbox position, early export blocking, unlocking at 20 frames, AOD access and automatic export enablement, and Italian/English/Chinese messages. The initial 3.0 had separately passed 162 source tests, 10 editor checks and a compiler fixture with two styles/two AOD views, native/shared/long-schedule GIFs and Crono Pro; those records remain historical evidence.

The executable is inspected statically without being launched. **On 2026-10-15 the owner confirmed GIF playback on the watch, while reporting intermittent native seconds-hand jumps with the full-screen Gatto animation.** The package correctly uses 1 Hz native pointers. Rendering/PNG-decoding contention is suspected, not device-profiled. Three temporary native compiler probes preserved pointer sources/periods and AOD, with timing/size tradeoffs; they do not establish a hardware performance fix. Sleep/wake and AOD were not separately reported in this test. [Detailed audit](AUDIT_GATTO_GIF_3.0.md) · [Owner report](hardware-gif-3.0.json).

[Current validation](validation-editor-3.0.json) · [Editor checks](gif-hotfix-editor-3.0.json) · [Gatto diagnosis](gatto-gif-diagnosis-3.0.json) · [Gatto/AOD compiler export](gatto-export-hotfix-3.0.json) · [Executable integrity](executable-build-3.0.json)
