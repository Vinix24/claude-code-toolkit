---
name: codex-image
description: Generate a new image for a post, blog cover or illustration through the user's own Codex CLI login, then prepare a publication-sized PNG. Use when the user wants an image made for a blog or LinkedIn post; not for editing the content of an existing image.
---

# Codex image

Use the bundled script for generation and finishing. It requires Python 3.9+, Pillow,
and a Codex CLI signed in with a non-Free ChatGPT plan. No API key is needed.
The prompt is sent to OpenAI through that login; the archive and log stay local.
Image generation uses the shared Codex quota roughly 3 to 5 times faster than text
work. Keep the daily cap and make at most **two generations per requested image**,
including failed attempts. Finishing an existing PNG uses no generation quota.

## Choose the format and write the prompt

| Kind | Output | Byte limit |
|---|---|---|
| `blog-cover-bg` | 1200 × 630 | 500,000 |
| `blog-inline` | 1200 wide, proportional height | 400,000 |
| `linkedin-square` | 1200 × 1200 | 5,000,000 |
| `linkedin-landscape` | 1200 × 628 | 5,000,000 |

Write the complete prompt to a UTF-8 file. Include the composition, intended crop,
colours, and every required text string exactly. Ask for a fully opaque background
that fills the entire canvas. The script appends this opaque-background instruction
as well. Keep the ready prompt available for the fallback.

## Run the script

Always resolve the script through this skill's directory:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/codex_image.py" status
python3 "${CLAUDE_SKILL_DIR}/scripts/codex_image.py" generate --kind blog-cover-bg --prompt-file /path/to/prompt.txt --out /path/to/cover.png
python3 "${CLAUDE_SKILL_DIR}/scripts/codex_image.py" finish --kind blog-cover-bg --source /path/to/original.png --out /path/to/cover.png
```

- `status` reports today's `count`, `cap` and `last_five` log entries. The default cap
  is five started CLI calls per local day, including calls that produce no image.
- `generate` launches Codex, finds its new PNG, archives it and finishes the output.
  `--timeout` defaults to 600 seconds. Do not use `--over-cap-reason` unless the user
  has explicitly supplied a reason to exceed the cap; never invent one.
- `finish` only archives, flattens, resizes/crops and compresses a PNG. Instead of
  `--source`, `--latest-since 2026-10-21T12:00:00+02:00` selects the newest PNG under
  the Codex generated-images directory since that timestamp. Prefer a known source
  path when several Codex sessions might be producing images.

Both image commands accept `--background '#RRGGBB'` for flattening transparency.
It overrides `CODEX_IMAGE_BACKGROUND`; the default is white (`#FFFFFF`). This colour
fills transparent pixels only. It does not recolour an opaque image.

## Read the result and inspect the image

The script emits one JSON object on stdout and diagnostics on stderr. Exit 0 means
the operation completed; exit 2 means usage or dependency trouble; exit 3 means a
runtime fallback. With Pillow missing it prints only the installation instruction
on stderr and exits 2 before doing any work.

For image commands, check `outcome` (`ok` or `fallback`) and `reason` first. A nonzero
Codex exit may still produce a usable image. Check `within_limit` even when the
script exits 0: a quantized PNG may remain too large. `out` is the finished file;
`original` is the preserved source; `codex_source` identifies the input PNG.
`width`, `height`, `bytes`, `limit_bytes`, `quantized`, `flattened`,
`transparent_share`, `seconds`, and `prompt_sha256` describe the result.

**After every generated or finished image, open `out` with an available image-viewing
tool.** Compare every visible text string with the prompt **letter for letter**,
including punctuation and accents. Check that the background fills the whole canvas,
including all edges and corners, and that cropping leaves the subject intact. Take
extra care when `transparent_share` is above **0.2**: flattening may leave large plain
areas or an unintended border. This field measures the original share of pixels with
alpha below 250, not whether the finished image looks correct. If image viewing is
unavailable, say the visual check could not be completed.

Do not present the image as ready until its text, canvas and size checks pass. One
corrective generation is allowed after a visual failure, within the two-generation
maximum and the daily cap. Do not keep retrying a refusal, missing login, timeout,
or exhausted quota. `finish` can correct format or flattening without another call.

## Fallback

If generation cannot run, the cap is reached, the image remains unsuitable after two
attempts, or the required visual check cannot be completed, hand the user the complete,
ready-to-paste prompt for another generator. Explain the concrete limitation and
include the target dimensions. Do not claim image text is guaranteed to render correctly.
