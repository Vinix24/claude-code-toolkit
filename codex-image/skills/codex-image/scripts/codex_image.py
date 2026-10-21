#!/usr/bin/env python3
"""
Generate and finish images for blogs and LinkedIn through the Codex CLI.

Uses only the built-in image tool through an authenticated Codex CLI.
Archives the original, resizes/crops to the publication format and quantizes
with 256 colours if needed. A usable image is kept even if the CLI fails.

The daily cap counts started CLI calls, including those without an image;
finish never counts. CODEX_IMAGE_HOME relocates the archive, log and lock.
Generation is serialized so concurrent processes cannot bypass the cap.
The log is append-only with flock; status shows the last five log entries.
"""
from __future__ import annotations

import argparse
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    print("Pillow is required; run: python3 -m pip install Pillow", file=sys.stderr)
    raise SystemExit(2)

KINDS = {
    "blog-cover-bg": (1200, 630, 500000),
    "blog-inline": (1200, None, 400000),
    "linkedin-square": (1200, 1200, 5000000),
    "linkedin-landscape": (1200, 628, 5000000),
}
CLOSING_INSTRUCTION = (
    "Generate exactly one image with the built-in image tool. "
    "Do not run shell commands, do not write or move files. "
    "Use a fully opaque background that fills the whole canvas; no transparency. "
    "When the image exists, reply DONE."
)
COST_SOURCE = "unavailable:codex_cli_no_usage"


class ImageFailure(Exception):
    def __init__(self, reason, detail, exit_code=3):
        super().__init__(detail)
        self.reason = reason
        self.exit_code = exit_code


def iso_time(value):
    """Parse ISO-8601; timestamps without an offset use the local timezone."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
    except (ValueError, AttributeError, TypeError) as exc:
        raise argparse.ArgumentTypeError("expected an ISO-8601 timestamp") from exc


def positive_timeout(value):
    try:
        number = float(value)
        if not math.isfinite(number) or number <= 0:
            raise ValueError
        return number
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be positive and finite") from exc


def background_colour(value):
    """Accept only an RGB hex colour, including its leading hash."""
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise argparse.ArgumentTypeError("background must be a #RRGGBB colour")
    return value


def image_home():
    return Path(os.environ.get("CODEX_IMAGE_HOME") or
                Path.home() / ".codex-image").expanduser().resolve()


def generated_home():
    return (Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
            .expanduser().resolve() / "generated_images")


@contextmanager
def generation_lock(home):
    home.mkdir(parents=True, exist_ok=True)
    with (home / "generation.lock").open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def read_log(path):
    """Reject corrupt logs: an unknown daily count must not allow generation."""
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_SH)
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict) or row.get("subcommand") not in {"generate", "finish"}:
                    raise ValueError("unknown log record")
                iso_time(row.get("ts"))
                if row.get("generation_started_at") is not None:
                    iso_time(row["generation_started_at"])
                if "generation_attempted" in row and not isinstance(row["generation_attempted"], bool):
                    raise ValueError("generation_attempted must be a boolean")
            except (ValueError, argparse.ArgumentTypeError) as exc:
                raise ImageFailure("invalid_log", f"invalid log line {number}: {exc}") from exc
            rows.append(row)
    return rows


def today_count(rows):
    today = datetime.now().astimezone().date()
    return sum(
        row.get("subcommand") == "generate"
        and row.get("generation_attempted", row.get("reason") not in {
            "cap_reached", "codex_missing", "invalid_prompt", "invalid_log"
        })
        and iso_time(row.get("generation_started_at") or row["ts"]).date() == today
        for row in rows
    )


def append_log(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def latest_png(since):
    candidates = []
    for path in generated_home().rglob("*.png"):
        try:
            modified = path.stat().st_mtime
            if path.is_file() and modified >= since:
                candidates.append((modified, str(path), path))
        except FileNotFoundError:
            continue
    return max(candidates)[2] if candidates else None


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def finish_image(source, out, kind, home, result, background="#FFFFFF"):
    """Archive source bytes and flatten alpha onto the background before resizing.

    Write an opaque PNG as RGB or a palette without transparency.
    """
    source = source.expanduser().resolve()
    result["codex_source"] = str(source)
    try:
        original_bytes = source.read_bytes()
        with Image.open(io.BytesIO(original_bytes)) as opened:
            if opened.format != "PNG":
                raise ValueError("source must be PNG")
            flattened = "A" in opened.getbands() or "transparency" in opened.info
            transparent_share = 0.0
            if flattened:
                rgba = opened.convert("RGBA")
                alpha = rgba.getchannel("A")
                transparent_share = round(
                    sum(alpha.histogram()[:250]) / (opened.width * opened.height), 3)
                image = Image.new("RGB", opened.size, background)
                image.paste(rgba, mask=alpha)
            else:
                image = opened.convert("RGB")
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ImageFailure("invalid_source", str(exc)) from exc
    result.update(flattened=flattened, transparent_share=transparent_share)

    source_sha = hashlib.sha256(original_bytes).hexdigest()
    digest = result["prompt_sha256"] or source_sha
    day = datetime.now().astimezone().date().isoformat()
    original = home / "originals" / f"{day}-{digest[:12]}.png"
    if source.parent == (home / "originals").resolve():
        original = source
    # A repeated prompt can produce a different image: preserve both originals.
    if original.exists() and original.read_bytes() != original_bytes:
        original = home / "originals" / f"{day}-{source_sha[:12]}.png"
    if original.exists() and original.read_bytes() != original_bytes:
        raise ImageFailure("original_conflict", "archive name already exists with different contents")
    if out == original.resolve():
        raise ImageFailure("invalid_output", "output must not overwrite the archive", 2)
    if not original.exists():
        atomic_write(original, original_bytes)
    result["original"] = str(original)

    width, height, limit = KINDS[kind]
    if height is None:
        height = max(1, round(image.height * width / image.width))
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    else:
        scale = max(width / image.width, height / image.height)
        image = image.resize((math.ceil(image.width * scale), math.ceil(image.height * scale)),
                             Image.Resampling.LANCZOS)
        left, top = (image.width - width) // 2, (image.height - height) // 2
        image = image.crop((left, top, left + width, top + height))
    buffer = io.BytesIO()
    assert image.mode == "RGB" and "transparency" not in image.info
    image.save(buffer, format="PNG", optimize=True)
    quantized = buffer.tell() > limit
    if quantized:
        reduced = image.quantize(
            colors=256, method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.FLOYDSTEINBERG)
        assert reduced.mode == "P" and "transparency" not in reduced.info
        assert reduced.palette.mode == "RGB"
        buffer = io.BytesIO()
        reduced.save(buffer, format="PNG", optimize=True)
    data = buffer.getvalue()
    atomic_write(out, data)
    result.update(outcome="ok", reason=None, width=width, height=height,
                  bytes=len(data), within_limit=len(data) <= limit, quantized=quantized)


def run_codex(prompt, timeout, metadata):
    """Communicate handles closed stdin; timeouts also stop CLI child processes."""
    argv = [os.environ.get("CODEX_IMAGE_CODEX_BIN") or "codex", "exec",
            "--skip-git-repo-check", "--json", "--sandbox", "read-only"]
    started = time.time()
    metadata["generation_started_at"] = datetime.fromtimestamp(started, timezone.utc).isoformat()
    environment = os.environ.copy()
    for key in ("OPENAI_API_KEY", "CODEX_API_KEY"):
        environment.pop(key, None)
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE, start_new_session=True, env=environment)
    except FileNotFoundError as exc:
        raise ImageFailure("codex_missing", str(exc)) from exc
    except OSError as exc:
        raise ImageFailure("codex_failed", str(exc)) from exc
    metadata["generation_attempted"] = True
    failure = "no_image"
    try:
        _, stderr = proc.communicate(input=prompt.encode("utf-8"), timeout=timeout)
    except (subprocess.TimeoutExpired, BrokenPipeError) as exc:
        failure = "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "codex_failed"
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        _, stderr = proc.communicate()
    stderr = (stderr or b"").decode("utf-8", errors="replace")
    metadata.update(codex_exit=proc.returncode, codex_stderr_tail=stderr[-300:])
    source = latest_png(started)
    if source is not None:
        return source
    if failure == "no_image" and re.search(
        r"refus(?:e[ds]?|al|ing)|cannot (?:generate|create)|can't (?:generate|create)|"
        r"content policy|safety policy", stderr, re.IGNORECASE
    ):
        failure = "codex_refused"
    raise ImageFailure(failure, "Codex did not leave a new PNG file")


def perform(args, home, cap, result, metadata):
    if args.subcommand == "generate":
        if today_count(read_log(home / "log.ndjson")) >= cap and not args.over_cap_reason:
            raise ImageFailure("cap_reached", "daily cap reached")
        try:
            prompt_bytes = args.prompt_file.expanduser().read_bytes()
            prompt = prompt_bytes.decode("utf-8")
            if not prompt.strip():
                raise ValueError("prompt is empty")
        except (OSError, ValueError) as exc:
            raise ImageFailure("invalid_prompt", str(exc), 2) from exc
        result["prompt_sha256"] = hashlib.sha256(prompt_bytes).hexdigest()
        source = run_codex("$imagegen\n\n" + prompt + "\n\n" + CLOSING_INSTRUCTION,
                           args.timeout, metadata)
    else:
        source = args.source or latest_png(args.latest_since.timestamp())
        if source is None:
            raise ImageFailure("no_image", "no PNG found since the specified timestamp")
    finish_image(source, Path(result["out"]), args.kind, home, result, args.background)


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="subcommand", required=True)
    generate = sub.add_parser("generate", help="generate one image through the Codex CLI")
    finish = sub.add_parser("finish", help="finish an existing PNG file")
    sub.add_parser("status", help="daily count, cap and last five log entries")
    for command in (generate, finish):
        command.add_argument("--kind", choices=KINDS, required=True)
        command.add_argument("--out", type=Path, required=True)
        command.add_argument("--background", type=background_colour,
                             default=os.environ.get("CODEX_IMAGE_BACKGROUND", "#FFFFFF"),
                             help="flatten transparency onto #RRGGBB (env: CODEX_IMAGE_BACKGROUND; "
                                  "default: #FFFFFF)")
    generate.add_argument("--prompt-file", type=Path, required=True)
    generate.add_argument("--timeout", type=positive_timeout, default=600)
    generate.add_argument("--over-cap-reason", type=str.strip)
    sources = finish.add_mutually_exclusive_group(required=True)
    sources.add_argument("--source", type=Path)
    sources.add_argument("--latest-since", type=iso_time)
    return cli


def main(argv=None):
    cli = parser()
    args = cli.parse_args(argv)
    try:
        cap = int(os.environ.get("CODEX_IMAGE_DAILY_CAP", "5"))
        if cap < 0:
            raise ValueError
    except ValueError:
        cli.error("CODEX_IMAGE_DAILY_CAP must be a non-negative integer")
    home = image_home()
    if args.subcommand == "status":
        try:
            rows = read_log(home / "log.ndjson")
            print(json.dumps({"date": datetime.now().astimezone().date().isoformat(),
                              "count": today_count(rows), "cap": cap,
                              "last_five": list(deque(rows, maxlen=5))}, ensure_ascii=False))
            return 0
        except (ImageFailure, OSError) as exc:
            print(json.dumps({"outcome": "fallback", "reason": getattr(exc, "reason", "io_error")}))
            print(str(exc), file=sys.stderr)
            return 3

    started = time.monotonic()
    result = dict(outcome="fallback", reason=None, kind=args.kind,
                  out=str(args.out.expanduser().resolve()), original=None, codex_source=None,
                  width=None, height=None, bytes=None, limit_bytes=KINDS[args.kind][2],
                  within_limit=False, quantized=False, flattened=False,
                  transparent_share=0.0, seconds=0, prompt_sha256=None)
    metadata = dict(subcommand=args.subcommand, codex_exit=None, codex_stderr_tail="",
                    over_cap_reason=getattr(args, "over_cap_reason", None),
                    billing="subscription", cost_source=COST_SOURCE,
                    generation_attempted=False, generation_started_at=None)
    exit_code = 0
    try:
        # Finish also takes this lock to serialize archive names and temporary files.
        with generation_lock(home):
            try:
                perform(args, home, cap, result, metadata)
            except ImageFailure as exc:
                result["reason"], exit_code = exc.reason, exc.exit_code
                print(str(exc), file=sys.stderr)
            except (OSError, ValueError) as exc:
                result["reason"], exit_code = "io_error", 3
                print(str(exc), file=sys.stderr)
            result["seconds"] = round(time.monotonic() - started, 3)
            append_log(home / "log.ndjson", dict(result, **metadata,
                       ts=datetime.now(timezone.utc).isoformat()))
    except OSError as exc:
        result.update(outcome="fallback", reason="log_error",
                      seconds=round(time.monotonic() - started, 3))
        print(str(exc), file=sys.stderr)
        exit_code = 3
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
