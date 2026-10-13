# Chrono Pro engineering guide

[English overview](../README.md#chrono-pro-documentation) · [Italian overview](../README.it.md#chrono-pro-documentation) · [Documentation](README.md)

This guide describes the **current 2.7 behavior**. Earlier guides retain the implementation at their release date, including older scheduling periods and sweep durations.

## One scene, one measurement

The chronograph is local to the watchface; it does not control the watch's system Stopwatch application. `studioChronoSecond`, `studioChronoMinute`, `studioChronoHour` and the fraction sources are Studio runtime bindings, not invented Xiaomi sensor IDs.

The native exporter creates an EasyFace **Shape 34 App**, with an entry point `app/lua/studio_vN_scene.lua` for each interactive normal style. It registers the relevant views in one Lua scene and packages the runtime, hand PNGs and shadows for compilation into the binary. Placing an unreferenced Lua file beside an already compiled binary is insufficient.

**Why:** the earlier separate-App approach could leave hands using unrelated state. A shared entry point guarantees one measurement controller without assuming that `_G` or `require` caches are shared between widget VMs. Firmware VM isolation itself was not measured. The original fix was confirmed on hardware in version 1.0. [Classic chronograph guide](EDITOR_1.0.md) · [Hardware record](hardware-test-1.0.json).

The scene preserves saved layer order. Calendar labels and ordinary pointers can be included through `studio_scene_data.lua` without joining the chronograph controller. The moon wheel uses `studio_moon_disk.lua` and the calendar. Ordinary hands/discs must not be driven by chronograph elapsed time. [Composition details](LONGINE_LIVELLI_2.6.md).

## State and tap handling

| Current state | Tap / completion | Result |
| --- | --- | --- |
| Rest | Tap | Prepare measurement hands at zero; Pro large seconds leave civil time |
| Preparing | Animation completes | Ready |
| Ready | Tap | Running, with one common start timestamp |
| Running | Tap | Freeze elapsed time; animate POST indicators if present |
| POST reading | Animation completes | Stopped, all measurement readings frozen |
| Stopped | Tap | Coordinated reset |
| Resetting | Animation completes | Rest; large seconds return to civil time, or zero with Only Crono |

The full-screen transparent tap surface uses `lvgl.EVENT.PRESSED`, with `CLICKED` as fallback. A short tap guard and transition states prevent multiple actions from the same touch. A temporary page pause caused by touch is handled separately from AOD/OFF; a pending touch can be processed on resume. In AOD/OFF taps do not advance the chronograph.

The **classic** controller remains separate: Start → Stop → Reset, with small measurement hands and no takeover of large civil seconds. Pro is enabled by the flag on the large seconds tab. **Only Crono** selects the Pro idle behavior, keeping that hand at zero instead of showing civil seconds. Hiding graphics is not equivalent to removing the Pro configuration; each normal style owns its configuration.

## Elapsed time and clocks

The runtime selects a clock and preserves its origin throughout a measure. It computes elapsed time from the current timestamp and start timestamp, rather than incrementing a counter per callback.

| Path | Clock strategy | Limitation |
| --- | --- | --- |
| Available monotonic LVGL API | `lvgl.tick_get`, with 32-bit wrap handling | Availability depends on firmware |
| Available monotonic system read | `/proc/uptime` | File/API availability and resolution depend on firmware |
| Pro fallback | Phase deltas from a running LVGL animation | Stop can only use the latest published phase; it is frame-sampled |
| Civil compensation during suspended fallback operation | `os.time` when usable | One-second resolution; can be affected by system-time adjustments |

The classic runtime also has an `os.time` fallback. Pro replaces an unsuitable wall-second/absent live clock with its animation-phase clock. The implementation does not claim an official firmware callback named `elapsedMs`; it uses the already supported `Anim.exec_cb`.

Display sleep does not necessarily destroy the VM. Monotonic time or the supported civil compensation lets a running measure account for suspension; if no usable sleep clock exists the runtime stops rather than inventing elapsed time. Recreating the scene/VM or changing the watchface resets state; persistence across that event is not implemented.

## Scheduling and write-on-change

During Pro Running, the animation callback updates the fallback clock first, when used, then refreshes all views from the same current time. With a direct clock, the callback is only a frame notification and reads that clock. Refresh is gated by elapsed-time buckets:

| Active indicators | Update bucket | Visible behavior |
| --- | --- | --- |
| At least one smooth Pro-tenths hand | 40 ms target | Up to 25 requested updates per second |
| Stepped Pro tenths only | 100 ms | Ten nominal steps per second |
| No Pro tenths | 1,000 ms | Stepped seconds/minutes/hours; slow timer path where applicable |

The current callback path avoids a separate asynchronous 100 ms polling timer. A delayed callback catches up to the clock without counting the missed invocations. The rendered-value cache avoids repeated `Pointer:set` calls for unchanged values, including shadows and POST hands. This reduces redundant work without changing the clock or measurement scale.

**25 fps is a scheduling target, not measured device frame rate.** Callback delivery and rendering are controlled by the firmware. Original hidden `_ticks.png` resources are omitted entirely when ticks are disabled, avoiding compilation of the former transparent 360 × 360 bitmap. Enabled ticks, including AOD ticks, remain. [2.3 scheduling analysis](EDITOR_2.3.md).

## Values and calibration

For common elapsed time `E` in milliseconds:

| Indicator | Value |
| --- | --- |
| Pro large seconds | `floor(E / 1000) % 60` |
| Chronograph minutes | `floor(E / 60000) % configured_range` — normally 60 |
| Chronograph hours | `floor(E / 3600000) % configured_range` — normally 12 |
| Stepped Pro tenths | `floor((E % 1000) / 100)` |
| Smooth Pro tenths | Fraction `(E % 1000) / 1000`, mapped to the configured scale |
| Complete POST hundredths | `floor((E % 1000) / 10)` — 00–99 |
| Complete POST thousandths | `floor(E % 1000)` — 000–999 |

POST single-digit mode applies modulo 10. At **12.488 s**, tenths = 4, full hundredths = 48 and full thousandths = 488; the single hundredths/thousandths digits are both 8. Tenths single-digit and complete-fraction modes both use the 0–9 scale. They do not alter the optional interpolation between ticks.

Use **0/60/360°** for a complete seconds/minutes revolution, **0/12/360°** for 12-hour chronograph hours, and **0/10/360°** for tenths. POST complete-revolution ranges are **100/1000**; their last integer ticks are 99/999. The initial value describes the scale origin, not the simulated time or a forced starting pose.

For bounded arcs, configure **initial/final values**, **initial/final angles** and **direction**. Map 0–999 to the required thousandths arc; if a printed “8” means 0.800 s, its complete-fraction value is 800. Angles 30°→140° cover 110° clockwise or 250° counterclockwise; a short counterclockwise 110° arc uses 140°→30°. Values outside the configured scale clamp at the endpoints. Calibrate pivot and artwork orientation with the start/end preview controls. [Detailed arc guide](EDITOR_2.0.md).

## Transitions, POST and AOD

Prepare/reset and POST positioning share **720 ms** transitions with a **25 fps target** and eased interpolation. Full-circle return motion is clockwise. Bounded arcs interpolate within their printed scale, including the reverse path on reset, rather than crossing an unused sector. All measurement hands join the coordinated reset; ordinary hour/minute hands continue civil time.

POST hands stay at their initial pose while Running; only Stop reads and positions them. **Why:** a third fractional digit is useful for a frozen readout, but continuous thousandths rotations add rendering work without readable motion. The two indicators add images and optional shadows, not new fast Running timers.

Entering AOD/OFF immediately stops the normal-scene clock animation and transitions. Pro graphics are hidden and the project's AOD view is used without seconds or chronograph indicators. An interrupted POST readout retains its frozen value and returns to the final pose on wake. The separate daily moon disc, if included in AOD, is static between activations and has no periodic AOD animation.

Normal hour/minute smooth flags use coherent civil samples rather than independent 25 fps loops. Normal small seconds in a shared scene use a separate one-second animation triggered by changed real-second notifications. They remain independent of Pro taps. [Civil-hand correction](EDITOR_2.7.md).

## Precision, validation and evidence

**Three displayed fraction digits are not a claim of 1 ms accuracy.** Clock resolution, event delivery, fallback sampling and sleep compensation limit the measurement. Neither frame rate nor power consumption has been instrumented on the test watch. The chronograph is not a certified timing instrument.

The export validates scene entry points, views, source mappings, shared tap ownership, native bindings, runtime hashes and `interactive="true"` in the applicable manifest. `build-report.json` records `interactive.chronoPro`, POST settings and `interactive.sceneDynamicData` where used. Automatic `hardwareVerified:false` fields mean the exporter does not perform a physical test; owner confirmations are separate records.

Build 2.7 passed **114 targeted source tests**, actual temporary Longines export with two styles/AOD, and static executable verification. **User confirmation on 2026-10-13:** M2530W1, firmware **3.221.024**, successful operation after the civil-hand fixes. The report does not claim a new independent physical measurement or an installed-package hash.

[Source test report](validation-editor-2.7.json) · [Actual export](export-validation-2.7.json) · [Hardware confirmation](hardware-test-2.7.json) · [Bundle integrity](executable-build-2.7.json).
