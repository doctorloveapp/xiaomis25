# Text formatting

The `feature/text-formatting` branch adds formatting controls to text, live
numeric values, clock and date layers in both editors. Complication slots keep
their existing formatting controls; they are not changed by this feature.

- **Character spacing:** 0–40 integer pixels between adjacent characters or
  numeric cells. Zero preserves existing layouts. Numeric cells remain fixed
  width, so changing values does not move the entire field unexpectedly.
- **Bold / italic:** select the matching Windows system font face. Imported
  TTF/OTF files keep their own face: import a bold/italic face when needed.
- **Underline:** rasterized into text and numeric glyphs, so it also survives
  export without requiring a font installation on the watch. Numeric underlines
  are per cell, with gaps matching the configured spacing.
- Existing font size, alignment, color and opacity controls remain available.

Increase layer width/height if the layout warning indicates that the formatted
content does not fit. Old projects load with zero spacing, no italic and no
underline; their existing bold flag is retained. Properties are saved with the
layer and participate in style overrides and undo/redo.

Preview and generated EasyFace FPRJ use the same glyph metrics and tracking.
Transformed/shadowed live numbers use the same tracked positions in Lua sprite
generation. Native FPRJ numeric widgets export `Spacing` and the corresponding
widget width. A real compiler/device test of this new spacing is still required.

## Validation (3.1 source branch)

- Personal hand-set synchronization: passed, no new sets found.
- New formatting tests: 11 passed.
- Formatting plus available calendar tests: 24 passed, 2 deselected.
- Full calendar test file: 13 passed, 2 failed because the external source
  catalog is absent (`dateWeek` / `dateDay` sources are not available).
- Python source compilation: passed.
- Translation extraction/compilation: passed. The full extraction drops dynamic
  source labels when the external catalog is absent; those unrelated generated
  changes were discarded. Existing Qt catalogs were preserved and the three new
  messages added explicitly before recompiling.
- Executable packaging: blocked at preflight because the verified
  `quadrante_funzionante.zip` template is missing. No executable or demonstration
  watchface ZIP was produced. No physical device test was performed.

No new application version or release is declared by this feature branch.
