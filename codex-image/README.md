# codex-image

Generate an image through your own Codex CLI login and prepare an opaque PNG for a blog or LinkedIn post. The plugin archives the original, applies the publication crop and size, and keeps a local log with a daily generation cap.

It uses no API key, does not edit the content of existing images, and cannot guarantee correct text rendering. The `finish` command only flattens transparency, resizes/crops and compresses an existing PNG.

## Install

In Claude Code:

```text
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install codex-image@claude-code-toolkit
```

Requires Python 3.9 or newer on macOS or Linux (the script uses POSIX `flock` and process groups). Pillow is the only dependency outside the Python standard library:

```bash
python3 -m pip install Pillow
```

If Pillow is missing, every subcommand prints that installation instruction on stderr and exits 2 before reading prompts, creating state or launching Codex. The skill folder `skills/codex-image/` is self-contained.

## Codex login

Install the Codex CLI, for example with npm:

```bash
npm install -g @openai/codex
codex login
codex login status
```

Sign in with a ChatGPT account on a plan that is **not Free**. Use `codex login status` to check the login before generating. No API key is used or needed: the script removes `OPENAI_API_KEY` and `CODEX_API_KEY` from the environment passed to Codex. The CLI must have its built-in image tool and the `imagegen` skill available.

## Quota warning

Image generation uses the Codex quota roughly **3 to 5 times faster than text work**; this is a practical estimate, not a billing meter. The default daily cap of five started CLI calls protects other Codex work, such as code review, that shares the same quota. Failed calls that started count too; `finish`, a missing executable and rejected requests before startup do not. The cap follows the local calendar day and the call's start time.

The skill allows at most two generations per requested image, including failed attempts. The daily cap is enforced by the script; the two-attempt workflow is enforced by the skill. If an image cannot be delivered, the skill hands you the ready prompt to paste into another generator.

## Where data goes

**The prompt goes to OpenAI through your own Codex login.** The plugin sends nothing else anywhere and keeps the archive and log locally. This tool's generation step is an explicit exception to the toolkit's local-first description; finishing is entirely local. Codex itself uses its own account, configuration and storage.

By default, `~/.codex-image/` contains `originals/`, append-only `log.ndjson` and `generation.lock`. `CODEX_IMAGE_HOME` relocates all three together. The log stores the prompt's SHA-256 digest, not the full prompt, plus paths, outcomes and up to 300 characters of Codex stderr. The prompt file you supply remains where you put it. Codex leaves its generated PNGs under `${CODEX_HOME:-~/.codex}/generated_images/`.

Original source bytes are archived before finishing. Writes of images are atomic; log appends use `flock`. A generation lock serializes calls sharing one image home so they cannot race for the last daily slot. Use the same `CODEX_IMAGE_HOME` for processes that should share a cap. A corrupt log prevents generation because the count is unknown.

## Use

Ask Claude Code to make a post image, blog cover or illustration, or invoke `/codex-image:codex-image`. The skill uses:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/codex_image.py" status
python3 "${CLAUDE_SKILL_DIR}/scripts/codex_image.py" generate --kind blog-cover-bg --prompt-file /path/to/prompt.txt --out /path/to/cover.png
python3 "${CLAUDE_SKILL_DIR}/scripts/codex_image.py" finish --kind linkedin-square --source /path/to/original.png --out /path/to/post.png --background '#123456'
```

For standalone use, replace `${CLAUDE_SKILL_DIR}` with the path to `codex-image/skills/codex-image`. Prompts must be nonempty UTF-8 files. Codex receives the prompt on stdin with an instruction to generate exactly one image using a fully opaque background filling the entire canvas.

| Kind | Dimensions | Limit |
|---|---|---|
| `blog-cover-bg` | 1200 × 630 | 500 KB (500,000 bytes) |
| `blog-inline` | 1200 wide; proportional height | 400 KB (400,000 bytes) |
| `linkedin-square` | 1200 × 1200 | 5 MB (5,000,000 bytes) |
| `linkedin-landscape` | 1200 × 628 | 5 MB (5,000,000 bytes) |

Fixed dimensions use a centre crop; inline images preserve the aspect ratio. Transparency is flattened before resizing. Output is opaque RGB PNG, or a 256-colour palette PNG if compression is needed. Palette output remains a palette PNG with no transparency. An image still over the byte limit is kept and reported with `within_limit: false`.

Open every finished image before publishing. Compare every text string letter for letter with the prompt, check all edges for a background that fills the canvas, and take extra care when `transparent_share > 0.2`. Flattening large transparent areas can make unintended borders. Successful JSON alone is not a visual approval.

## Settings

Command-line `--background` overrides the environment. Quote hex colours so the shell does not treat `#` as a comment.

| Setting | Default | Purpose |
|---|---|---|
| `CODEX_IMAGE_HOME` | `~/.codex-image` | Local originals, log and generation lock |
| `CODEX_IMAGE_BACKGROUND` | `#FFFFFF` | Flattening colour; exactly `#RRGGBB`, case insensitive |
| `CODEX_IMAGE_DAILY_CAP` | `5` | Non-negative started CLI calls per local day; `0` disables generation unless overridden |
| `CODEX_IMAGE_CODEX_BIN` | `codex` on `PATH` | Executable path, including a test double; not a shell command |
| `CODEX_HOME` | `~/.codex` | Codex home; new PNGs are found recursively under `generated_images/` |
| `--kind` | Required | One of the four formats above, for `generate` and `finish` |
| `--out` | Required | Finished PNG path, for `generate` and `finish` |
| `--background` | Environment or white | Flattening colour for `generate` and `finish`; no effect on opaque pixels |
| `--prompt-file` | Required for `generate` | UTF-8 prompt file |
| `--timeout` | `600` seconds | Positive, finite timeout for Codex; its process group is stopped on expiry |
| `--over-cap-reason` | None | Nonblank explicit reason to exceed the cap; recorded in the log |
| `--source` | One source selector required | PNG to finish; mutually exclusive with `--latest-since` |
| `--latest-since` | One source selector required | ISO-8601 timestamp; finish the newest Codex PNG since then; no offset means local time |

## JSON and exit codes

Every normal invocation writes one JSON object to stdout, with diagnostics on stderr. Argument errors and missing Pillow produce no JSON. A usable image can yield success even if Codex exits nonzero or times out; the log records the CLI failure.

For `generate` and `finish`:

| Field | Meaning |
|---|---|
| `outcome`, `reason` | `ok` with a null reason, or `fallback` with a reason code |
| `kind`, `out` | Requested format and absolute output path |
| `original`, `codex_source` | Archived original and input PNG paths, or null if unavailable |
| `width`, `height`, `bytes`, `limit_bytes` | Output dimensions, file bytes and format byte limit; results may be null on failure |
| `within_limit` | Whether the output meets the byte limit; check even after exit 0 |
| `quantized` | Whether a 256-colour palette was used |
| `flattened` | Whether the source had alpha or transparency, including fully opaque alpha |
| `transparent_share` | Original fraction of pixels with alpha below 250, rounded to three decimals |
| `seconds` | Elapsed operation time, including waiting for the lock |
| `prompt_sha256` | Hash of the prompt file bytes; null for `finish` |

`status` returns `date`, `count`, `cap` and `last_five`. A status read failure returns `outcome: fallback` and `reason`. Log entries add `subcommand`, `ts` (UTC), `codex_exit`, `codex_stderr_tail`, `over_cap_reason`, `generation_attempted`, `generation_started_at`, `billing: subscription` and `cost_source: unavailable:codex_cli_no_usage`. No token or money usage is inferred.

| Exit code | Meaning |
|---|---|
| `0` | Operation completed; still check `within_limit` and inspect the image |
| `2` | Usage/dependency error, invalid prompt, or output would overwrite the archive |
| `3` | Runtime fallback: cap, missing/failed Codex, timeout, refusal, no image, invalid source/log, archive conflict or I/O failure |

Reason codes include `cap_reached`, `codex_missing`, `codex_failed`, `timeout`, `codex_refused`, `no_image`, `invalid_prompt`, `invalid_source`, `invalid_log`, `original_conflict`, `invalid_output`, `io_error` and `log_error`. Do not automatically retry failures. On fallback, provide the complete prompt for another generator.

## Tests

```bash
cd codex-image
python3 -m pytest -q
```

Tests run the actual script with isolated image/Codex homes and an executable Codex test double. They use no network and spend no image quota. They cover formats, compression, alpha, archives, concurrency, caps, CLI failures, background settings and missing Pillow.
