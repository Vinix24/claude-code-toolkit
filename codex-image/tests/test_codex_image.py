#!/usr/bin/env python3
"""
Test the real CLI and image processing without network access.

Images, logs and the executable Codex test double live in a temporary directory.
The production CLI runs through subprocess with explicit isolated homes.

Run from the plugin directory: python3 -m pytest -q
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "skills/codex-image/scripts/codex_image.py"
FIELDS = {"outcome", "reason", "kind", "out", "original", "codex_source", "width",
          "height", "bytes", "limit_bytes", "within_limit", "quantized", "seconds",
          "prompt_sha256", "flattened", "transparent_share"}
COST_SOURCE = "unavailable:codex_cli_no_usage"
STUB = r'''import json
import os
from pathlib import Path
import shutil
import sys
import time

if os.environ.get("STUB_MODE") == "startup_exit":
    sys.exit(1)
prompt = sys.stdin.read()
capture = Path(os.environ["STUB_CAPTURE"])
capture.write_text(json.dumps({"argv": sys.argv[1:], "prompt": prompt,
                               "api_key_present": any(key in os.environ for key in
                                                      ("OPENAI_API_KEY", "CODEX_API_KEY"))}))
mode = os.environ.get("STUB_MODE", "ok")
if mode in {"ok", "capacity", "image_timeout", "long_stderr", "slow"}:
    if mode == "slow":
        time.sleep(0.3)
    dest = Path(os.environ["CODEX_HOME"]) / "generated_images/session/image.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(os.environ["STUB_SOURCE"], dest)
if mode in {"timeout", "image_timeout"}:
    time.sleep(30)
if mode == "capacity":
    print("Selected model is at capacity", file=sys.stderr)
    sys.exit(1)
if mode == "refused":
    print("I cannot generate this image: content policy refusal", file=sys.stderr)
    sys.exit(1)
if mode == "long_stderr":
    print("x" * 500 + " tail", file=sys.stderr)
print('{"event": "test-cli-complete"}')
'''


def guarded_cleanup(path):
    target = os.path.realpath(path)
    home = os.path.realpath(os.path.expanduser("~"))
    roots = {os.path.realpath(tempfile.gettempdir()), os.path.realpath("/tmp")}
    if os.environ.get("TMPDIR"):
        roots.add(os.path.realpath(os.environ["TMPDIR"]))
    under_scratch_root = any(target == r or target.startswith(r + os.sep) for r in roots)
    if (target == os.path.realpath("/") or os.path.dirname(target) == os.path.realpath("/")
            or target == home or home.startswith(target + os.sep) or not under_scratch_root):
        raise RuntimeError(f"REFUSING to delete unsafe path: {target}")
    if os.path.isdir(target):
        shutil.rmtree(target)
    else:
        os.remove(target)


class CodexImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="codex-image-test-")).resolve()
        self.addCleanup(guarded_cleanup, self.tmp)
        self.home = self.tmp / "archive"
        self.codex_home = self.tmp / "codex"
        self.source = self.tmp / "source.png"
        Image.new("RGB", (1774, 887), "#234567").save(self.source)
        self.prompt = self.tmp / "prompt.txt"
        self.prompt.write_text("An image with one orange arrow.", encoding="utf-8")
        self.binary = self.tmp / "codex test binary"
        self.binary.write_text(f"#!{sys.executable}\n" + STUB, encoding="utf-8")
        self.binary.chmod(0o700)
        self.capture = self.tmp / "capture.json"
        self.out = self.tmp / "output/subdir/result.png"
        self.env = os.environ.copy()
        for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_IMAGE_BACKGROUND"):
            self.env.pop(key, None)
        self.env.update(CODEX_HOME=str(self.codex_home), CODEX_IMAGE_HOME=str(self.home),
                        CODEX_IMAGE_CODEX_BIN=str(self.binary), CODEX_IMAGE_DAILY_CAP="5",
                        PYTHONDONTWRITEBYTECODE="1", STUB_SOURCE=str(self.source),
                        STUB_CAPTURE=str(self.capture), STUB_MODE="ok")

    def command(self, *args):
        return [sys.executable, str(SCRIPT), *map(str, args)]

    def run_cli(self, *args, code=0, env=None):
        completed = subprocess.run(self.command(*args), env=env or self.env,
                                   capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, code, completed.stdout + completed.stderr)
        self.assertEqual(len(completed.stdout.splitlines()), 1, completed.stdout)
        data = json.loads(completed.stdout)
        if args[0] != "status":
            self.assertEqual(set(data), FIELDS)
        return data

    def generate(self, *extra, code=0):
        return self.run_cli("generate", "--kind", "linkedin-square", "--prompt-file",
                            self.prompt, "--out", self.out, *extra, code=code)

    def finish(self, kind="blog-cover-bg", source=None, code=0):
        return self.run_cli("finish", "--kind", kind, "--source", source or self.source,
                            "--out", self.out, code=code)

    def log_rows(self):
        rows = [json.loads(line) for line in (self.home / "log.ndjson").read_text().splitlines()]
        for row in rows:
            self.assertTrue(FIELDS.issubset(row))
            self.assertEqual(row["billing"], "subscription")
            self.assertEqual(row["cost_source"], COST_SOURCE)
            self.assertLessEqual(len(row["codex_stderr_tail"]), 300)
            self.assertEqual(datetime.fromisoformat(row["ts"]).utcoffset(), timedelta(0))
        return rows

    def test_generate_success_argv_stdin_and_original(self):
        data = self.generate()
        self.assertEqual(data["outcome"], "ok")
        self.assertEqual((data["width"], data["height"]), (1200, 1200))
        self.assertEqual(Path(data["original"]).read_bytes(), self.source.read_bytes())
        digest = hashlib.sha256(self.prompt.read_bytes()).hexdigest()
        self.assertEqual(data["prompt_sha256"], digest)
        self.assertTrue(Path(data["original"]).name.endswith(digest[:12] + ".png"))
        capture = json.loads(self.capture.read_text())
        self.assertEqual(capture["argv"], ["exec", "--skip-git-repo-check", "--json",
                                          "--sandbox", "read-only"])
        self.assertEqual(capture["prompt"], "$imagegen\n\n" + self.prompt.read_text() +
                         "\n\nGenerate exactly one image with the built-in image tool. "
                         "Do not run shell commands, do not write or move files. "
                         "Use a fully opaque background that fills the whole canvas; no transparency. "
                         "When the image exists, reply DONE.")
        self.assertEqual(self.log_rows()[0]["codex_exit"], 0)

    def test_nonzero_capacity_after_image_is_success(self):
        self.env["STUB_MODE"] = "capacity"
        self.assertEqual(self.generate()["outcome"], "ok")
        row = self.log_rows()[0]
        self.assertEqual(row["codex_exit"], 1)
        self.assertIn("Selected model is at capacity", row["codex_stderr_tail"])

    def test_no_image_is_fallback_and_counts_attempt(self):
        self.env["STUB_MODE"] = "empty"
        self.assertEqual(self.generate(code=3)["reason"], "no_image")
        self.assertEqual(self.run_cli("status")["count"], 1)
        self.assertEqual(len(self.log_rows()), 1)

    def test_png_older_than_start_is_ignored(self):
        self.env["STUB_MODE"] = "empty"
        old = self.codex_home / "generated_images/old/file.png"
        old.parent.mkdir(parents=True)
        shutil.copyfile(self.source, old)
        stamp = (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
        os.utime(old, (stamp, stamp))
        self.assertEqual(self.generate(code=3)["reason"], "no_image")
        self.assertIsNone(self.log_rows()[0]["codex_source"])

    def test_early_exit_with_large_stdin_is_structured_fallback(self):
        self.env["STUB_MODE"] = "startup_exit"
        self.prompt.write_text("image " * 200000)
        self.assertEqual(self.generate(code=3)["reason"], "no_image")
        self.assertEqual(self.log_rows()[0]["codex_exit"], 1)

    def test_timeout_without_image(self):
        self.env["STUB_MODE"] = "timeout"
        self.assertEqual(self.generate("--timeout", "0.5", code=3)["reason"], "timeout")
        self.assertLess(self.log_rows()[0]["codex_exit"], 0)

    def test_timeout_recovers_existing_image(self):
        self.env["STUB_MODE"] = "image_timeout"
        self.assertEqual(self.generate("--timeout", "0.5")["outcome"], "ok")
        self.assertLess(self.log_rows()[0]["codex_exit"], 0)

    def test_missing_codex_does_not_count(self):
        self.env["CODEX_IMAGE_CODEX_BIN"] = str(self.tmp / "missing")
        self.assertEqual(self.generate(code=3)["reason"], "codex_missing")
        self.assertFalse(self.log_rows()[0]["generation_attempted"])
        self.assertEqual(self.run_cli("status")["count"], 0)

    def test_codex_refusal(self):
        self.env["STUB_MODE"] = "refused"
        self.assertEqual(self.generate(code=3)["reason"], "codex_refused")
        self.assertEqual(self.log_rows()[0]["codex_exit"], 1)

    def test_stderr_is_last_300_characters(self):
        self.env["STUB_MODE"] = "long_stderr"
        self.generate()
        self.assertEqual(self.log_rows()[0]["codex_stderr_tail"], ("x" * 500 + " tail\n")[-300:])

    def test_sixth_refused_and_override_logged_without_truncation(self):
        for _ in range(5):
            self.generate()
        before = (self.home / "log.ndjson").read_bytes()
        self.assertEqual(self.generate(code=3)["reason"], "cap_reached")
        self.assertEqual(self.generate("--over-cap-reason", "operator smoke check")["outcome"], "ok")
        rows = self.log_rows()
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[-1]["over_cap_reason"], "operator smoke check")
        self.assertTrue((self.home / "log.ndjson").read_bytes().startswith(before))
        status = self.run_cli("status")
        self.assertEqual((status["count"], status["cap"]), (6, 5))
        self.assertEqual(status["last_five"], rows[-5:])

    def test_cap_env_zero_and_blank_override(self):
        self.env["CODEX_IMAGE_DAILY_CAP"] = "0"
        self.assertEqual(self.generate("--over-cap-reason", "   ", code=3)["reason"], "cap_reached")
        self.assertFalse(self.capture.exists())
        self.assertEqual(self.run_cli("status")["cap"], 0)
        self.log_rows()

    def test_finish_never_counts_and_works_at_cap(self):
        self.env["CODEX_IMAGE_DAILY_CAP"] = "0"
        self.finish()
        self.assertEqual(self.run_cli("status")["count"], 0)
        self.assertIsNone(self.log_rows()[0]["codex_exit"])
        self.assertFalse(self.capture.exists())

    def test_local_day_count_uses_timestamp_offset(self):
        self.generate()
        row = self.log_rows()[0]
        now = datetime.now(timezone.utc)
        today = dict(row, ts=now.isoformat(), generation_started_at=now.isoformat())
        yesterday = dict(row, ts=(now - timedelta(days=1)).isoformat(),
                         generation_started_at=(now - timedelta(days=1)).isoformat())
        # Only the test fixture is rewritten, atomically and outside the real archive.
        temporary = self.home / "log.ndjson.tmp"
        temporary.write_text(json.dumps(today) + "\n" + json.dumps(yesterday) + "\n")
        os.replace(temporary, self.home / "log.ndjson")
        self.env["TZ"] = "Pacific/Honolulu"
        self.assertEqual(self.run_cli("status")["count"], 1)

    def test_concurrent_generations_cannot_both_take_last_slot(self):
        self.env.update(CODEX_IMAGE_DAILY_CAP="1", STUB_MODE="slow")
        command = self.command("generate", "--kind", "linkedin-square", "--prompt-file",
                               self.prompt, "--out", self.out)
        processes = [subprocess.Popen(command, env=self.env, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True) for _ in range(2)]
        results = []
        try:
            for process in processes:
                stdout, stderr = process.communicate(timeout=20)
                self.assertIn(process.returncode, (0, 3), stderr)
                results.append(json.loads(stdout))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
        self.assertEqual(sorted(r["outcome"] for r in results), ["fallback", "ok"])
        self.assertEqual(len(self.log_rows()), 2)
        self.assertEqual(self.run_cli("status")["count"], 1)

    def test_landscape_source_all_four_kinds(self):
        sizes = {"blog-cover-bg": (1200, 630), "blog-inline": (1200, 600),
                 "linkedin-square": (1200, 1200), "linkedin-landscape": (1200, 628)}
        for kind, expected in sizes.items():
            with self.subTest(kind=kind):
                data = self.finish(kind)
                with Image.open(self.out) as image:
                    self.assertEqual(image.size, expected)
                self.assertEqual((data["width"], data["height"]), expected)
                self.assertEqual(data["bytes"], self.out.stat().st_size)
        self.assertEqual(len(self.log_rows()), 4)

    def test_square_source_all_four_kinds(self):
        Image.new("RGB", (1254, 1254), "navy").save(self.source)
        sizes = {"blog-cover-bg": (1200, 630), "blog-inline": (1200, 1200),
                 "linkedin-square": (1200, 1200), "linkedin-landscape": (1200, 628)}
        for kind, expected in sizes.items():
            with self.subTest(kind=kind):
                data = self.finish(kind)
                with Image.open(self.out) as image:
                    self.assertEqual(image.size, expected)
                self.assertEqual((data["width"], data["height"]), expected)
        self.assertEqual(len(self.log_rows()), 4)

    def test_noisy_gradient_cover_quantizes_to_opaque_palette_within_limit(self):
        rng = random.Random(1729)
        width, height = 1774, 887
        pixels = bytearray(width * height * 3)
        for y in range(height):
            for x in range(width):
                offset = (y * width + x) * 3
                pixels[offset:offset + 3] = bytes((
                    min(255, x * 220 // width + rng.randrange(24)),
                    min(255, y * 220 // height + rng.randrange(24)),
                    min(255, (x + y) * 220 // (width + height) + rng.randrange(24))))
        Image.frombytes("RGB", (width, height), bytes(pixels)).save(self.source)
        data = self.finish()
        self.assertTrue(data["quantized"])
        with Image.open(self.out) as image:
            self.assertEqual(image.mode, "P")
            self.assertNotIn("transparency", image.info)
            self.assertNotIn("A", image.getbands())
            self.assertIsNotNone(image.getcolors(maxcolors=256))
        self.assertEqual(data["bytes"], self.out.stat().st_size)
        self.assertTrue(data["within_limit"])
        self.assertLessEqual(data["bytes"], 500000)
        self.log_rows()

    def test_quantized_rgba_border_is_opaque_palette_with_white_edges(self):
        pixels = random.Random(1729).randbytes(1120 * 550 * 3)
        center = Image.frombytes("RGB", (1120, 550),
                                 bytes(128 + value // 2 for value in pixels))
        image = Image.new("RGBA", (1200, 630), (255, 0, 0, 0))
        image.paste(center.convert("RGBA"), (40, 40))
        image.save(self.source)
        data = self.finish()
        self.assertTrue(data["quantized"])
        self.assertTrue(data["flattened"])
        with Image.open(self.out) as published:
            self.assertEqual(published.mode, "P")
            self.assertNotIn("transparency", published.info)
            self.assertNotIn("A", published.getbands())
            self.assertIsNotNone(published.getcolors(maxcolors=256))
            rgb = published.convert("RGB")
            for box in ((0, 0, 1200, 40), (0, 590, 1200, 630),
                        (0, 40, 40, 590), (1160, 40, 1200, 590)):
                border = rgb.crop(box)
                self.assertEqual(border.getcolors(),
                                 [(border.width * border.height, (255, 255, 255))])
        self.log_rows()

    def test_over_limit_after_quantization_keeps_image(self):
        pixels = random.Random(42).randbytes(1200 * 1200 * 3)
        Image.frombytes("RGB", (1200, 1200), pixels).save(self.source)
        data = self.finish("blog-inline")
        self.assertTrue(data["quantized"])
        self.assertFalse(data["within_limit"])
        self.assertGreater(data["bytes"], 400000)
        self.assertTrue(self.out.is_file())
        self.assertEqual(self.log_rows()[0]["outcome"], "ok")

    def test_cover_center_crop_and_inline_preserves_edges(self):
        image = Image.new("RGB", (1774, 887), "green")
        image.paste("red", (0, 0, 400, 887))
        image.paste("blue", (1374, 0, 1774, 887))
        image.save(self.source)
        self.finish("linkedin-square")
        with Image.open(self.out) as result:
            self.assertEqual(result.getpixel((0, 600)), (0, 128, 0))
            self.assertEqual(result.getpixel((1199, 600)), (0, 128, 0))
        self.finish("blog-inline")
        with Image.open(self.out) as result:
            self.assertEqual(result.getpixel((0, 300)), (255, 0, 0))
            self.assertEqual(result.getpixel((1199, 300)), (0, 0, 255))
        self.log_rows()

    def test_finish_latest_since_picks_newest_nested_png(self):
        generated = self.codex_home / "generated_images"
        since = datetime.now(timezone.utc) - timedelta(minutes=10)
        for name, seconds in (("a/old.png", 10), ("b/new.png", 20), ("c/future.jpg", 30)):
            path = generated / name
            path.parent.mkdir(parents=True)
            shutil.copyfile(self.source, path)
            stamp = since.timestamp() + seconds
            os.utime(path, (stamp, stamp))
        data = self.run_cli("finish", "--kind", "blog-cover-bg", "--latest-since",
                            since.isoformat(), "--out", self.out)
        self.assertEqual(data["codex_source"], str(generated / "b/new.png"))
        self.assertIsNone(data["prompt_sha256"])
        self.log_rows()

    def test_finish_latest_since_missing_is_logged(self):
        data = self.run_cli("finish", "--kind", "blog-cover-bg", "--latest-since",
                            datetime.now(timezone.utc).isoformat(), "--out", self.out, code=3)
        self.assertEqual(data["reason"], "no_image")
        self.log_rows()

    def test_finish_invalid_or_missing_source(self):
        for source in (self.tmp / "missing.png", self.prompt):
            with self.subTest(source=source.name):
                self.assertEqual(self.finish(source=source, code=3)["reason"], "invalid_source")
        self.assertEqual(len(self.log_rows()), 2)

    def test_finish_flattens_rgba_border_and_reports_source_share(self):
        image = Image.new("RGBA", (24, 24), (255, 0, 0, 0))
        image.paste((255, 255, 255, 255), (6, 6, 18, 18))
        image.putpixel((10, 10), (255, 255, 255, 249))
        image.putpixel((11, 10), (255, 255, 255, 250))
        image.putpixel((12, 10), (255, 255, 255, 254))
        image.save(self.source)
        data = self.finish("linkedin-square")
        with Image.open(self.out) as published:
            self.assertEqual(published.mode, "RGB")
            self.assertEqual(published.format, "PNG")
            for point in ((0, 0), (1199, 1199), (0, 600), (1199, 600),
                          (600, 0), (600, 1199)):
                self.assertEqual(published.getpixel(point), (255, 255, 255))
        self.assertIs(data["flattened"], True)
        self.assertEqual(data["transparent_share"], 0.752)
        row = self.log_rows()[0]
        self.assertIs(row["flattened"], True)
        self.assertEqual(row["transparent_share"], 0.752)
        self.assertEqual(Path(data["original"]).read_bytes(), self.source.read_bytes())

    def test_finish_rgb_reports_no_flattening(self):
        data = self.finish()
        self.assertIn("flattened", data)
        self.assertIs(data["flattened"], False)
        self.assertEqual(data["transparent_share"], 0.0)
        with Image.open(self.out) as image:
            self.assertEqual(image.mode, "RGB")
        row = self.log_rows()[0]
        self.assertIs(row["flattened"], False)
        self.assertEqual(row["transparent_share"], 0.0)

    def test_finish_flattens_la_and_palette_transparency(self):
        for mode in ("LA", "P"):
            with self.subTest(mode=mode):
                if mode == "LA":
                    image = Image.new("LA", (24, 24), (255, 0))
                    image.paste((255, 128), (6, 6, 18, 18))
                else:
                    image = Image.new("P", (24, 24), 0)
                    image.putpalette([255, 0, 0, 255, 255, 255] + [0] * 762)
                    image.paste(1, (6, 6, 18, 18))
                    image.info["transparency"] = bytes((0, 128))
                image.save(self.source)
                data = self.finish("linkedin-square")
                with Image.open(self.out) as published:
                    self.assertEqual(published.mode, "RGB")
                    self.assertEqual(published.getpixel((0, 0)), (255, 255, 255))
                    self.assertEqual(published.getpixel((600, 600)), (255, 255, 255))
                self.assertIs(data["flattened"], True)
                self.assertEqual(data["transparent_share"], 1.0)
                self.assertEqual(Path(data["original"]).read_bytes(), self.source.read_bytes())
        self.assertEqual(len(self.log_rows()), 2)

    def test_finish_removes_fully_opaque_alpha(self):
        Image.new("RGBA", (24, 24), (255, 255, 255, 255)).save(self.source)
        data = self.finish()
        with Image.open(self.out) as image:
            self.assertEqual(image.mode, "RGB")
            self.assertEqual(image.getpixel((600, 300)), (255, 255, 255))
        self.assertIs(data["flattened"], True)
        self.assertEqual(data["transparent_share"], 0.0)

    def test_finish_preserves_original_hash_and_blends_transparency(self):
        Image.new("RGBA", (1254, 1254), (255, 255, 255, 128)).save(self.source)
        data = self.finish()
        digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.assertTrue(Path(data["original"]).name.endswith(digest[:12] + ".png"))
        self.assertEqual(Path(data["original"]).read_bytes(), self.source.read_bytes())
        with Image.open(self.out) as image:
            self.assertEqual(image.mode, "RGB")
            self.assertEqual(image.getpixel((600, 300)), (255, 255, 255))
        self.log_rows()

    def test_refinish_archived_source_reuses_original_without_new_archive(self):
        original = self.home / "originals/prompt-hash.png"
        original.parent.mkdir(parents=True)
        shutil.copyfile(self.source, original)
        original_bytes = original.read_bytes()
        data = self.finish(source=original)
        self.assertEqual(data["original"], str(original))
        self.assertEqual(list(original.parent.iterdir()), [original])
        self.assertEqual(original.read_bytes(), original_bytes)

    def test_repeated_prompt_preserves_different_originals(self):
        first = self.generate()
        first_bytes = Path(first["original"]).read_bytes()
        Image.new("RGB", (1774, 887), "orange").save(self.source)
        second = self.generate()
        self.assertNotEqual(first["original"], second["original"])
        self.assertEqual(Path(first["original"]).read_bytes(), first_bytes)
        self.assertEqual(Path(second["original"]).read_bytes(), self.source.read_bytes())
        self.assertEqual(len(self.log_rows()), 2)

    def test_missing_or_empty_prompt_is_usage_error_and_logged(self):
        self.prompt = self.tmp / "missing-prompt.txt"
        self.assertEqual(self.generate(code=2)["reason"], "invalid_prompt")
        self.prompt.write_text("   ")
        self.assertEqual(self.generate(code=2)["reason"], "invalid_prompt")
        self.assertFalse(self.capture.exists())
        self.assertEqual(len(self.log_rows()), 2)

    def test_invalid_usage_errors_before_codex(self):
        cases = [
            ["finish", "--kind", "blog-cover-bg", "--latest-since", "not-a-date", "--out", self.out],
            ["finish", "--kind", "blog-cover-bg", "--out", self.out],
            ["generate", "--kind", "unknown", "--prompt-file", self.prompt, "--out", self.out],
        ]
        for timeout in ("0", "-1", "nan", "inf", "text"):
            cases.append(["generate", "--kind", "blog-cover-bg", "--prompt-file", self.prompt,
                          "--out", self.out, "--timeout", timeout])
        for args in cases:
            with self.subTest(args=args):
                completed = subprocess.run(self.command(*args), env=self.env, capture_output=True,
                                           text=True, timeout=10)
                self.assertEqual(completed.returncode, 2)
        self.assertFalse(self.capture.exists())

    def test_invalid_cap_is_usage_error(self):
        for cap in ("-1", "invalid", "1.5"):
            with self.subTest(cap=cap):
                self.env["CODEX_IMAGE_DAILY_CAP"] = cap
                completed = subprocess.run(self.command("status"), env=self.env,
                                           capture_output=True, text=True, timeout=10)
                self.assertEqual(completed.returncode, 2)

    def test_corrupt_log_fails_closed(self):
        self.home.mkdir()
        (self.home / "log.ndjson").write_text("null\n")
        self.assertEqual(self.generate(code=3)["reason"], "invalid_log")
        self.assertFalse(self.capture.exists())
        self.assertTrue((self.home / "log.ndjson").read_text().startswith("null\n"))
        self.assertEqual(self.run_cli("status", code=3)["reason"], "invalid_log")

    def test_empty_status_has_no_side_effects(self):
        self.assertEqual(self.run_cli("status"), {
            "date": datetime.now().astimezone().date().isoformat(), "count": 0,
            "cap": 5, "last_five": []})
        self.assertFalse(self.home.exists())

    def test_output_cannot_overwrite_archived_original(self):
        first = self.finish()
        original = Path(first["original"])
        original_bytes = original.read_bytes()
        self.out = original
        self.assertEqual(self.finish(code=2)["reason"], "invalid_output")
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertEqual(len(self.log_rows()), 2)

    def test_inaccessible_log_home_is_structured_fallback(self):
        self.home.write_text("not a directory")
        self.assertEqual(self.generate(code=3)["reason"], "log_error")
        self.assertFalse(self.capture.exists())

    def test_output_io_failure_is_logged(self):
        blocker = self.tmp / "not-a-directory"
        blocker.write_text("occupied")
        self.out = blocker / "out.png"
        self.assertEqual(self.finish(code=3)["reason"], "io_error")
        self.assertEqual(self.log_rows()[0]["reason"], "io_error")

    def test_default_background_is_white_for_both_commands(self):
        Image.new("RGBA", (24, 24), (255, 0, 0, 0)).save(self.source)
        for command in (self.finish, self.generate):
            with self.subTest(command=command.__name__):
                data = command()
                self.assertTrue(data["flattened"])
                self.assertEqual(data["transparent_share"], 1.0)
                with Image.open(self.out) as image:
                    self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_background_flag_reaches_pixels_for_both_commands(self):
        Image.new("RGBA", (24, 24), (255, 255, 255, 128)).save(self.source)
        for subcommand in ("finish", "generate"):
            with self.subTest(subcommand=subcommand):
                source_args = (["--source", self.source] if subcommand == "finish"
                               else ["--prompt-file", self.prompt])
                data = self.run_cli(subcommand, "--kind", "linkedin-square", "--out", self.out,
                                    *source_args, "--background", "#204060")
                self.assertTrue(data["flattened"])
                with Image.open(self.out) as image:
                    self.assertEqual(image.getpixel((600, 600)), (144, 160, 176))

    def test_background_env_reaches_pixels_for_both_commands(self):
        self.env["CODEX_IMAGE_BACKGROUND"] = "#12aBcD"
        Image.new("RGBA", (24, 24), (255, 0, 0, 0)).save(self.source)
        for command in (self.finish, self.generate):
            with self.subTest(command=command.__name__):
                command()
                with Image.open(self.out) as image:
                    self.assertEqual(image.getpixel((0, 0)), (18, 171, 205))

    def test_background_flag_overrides_env_for_both_commands(self):
        Image.new("RGBA", (24, 24), (255, 0, 0, 0)).save(self.source)
        for subcommand in ("finish", "generate"):
            for environment in ("#ABCDEF", "invalid"):
                with self.subTest(subcommand=subcommand, environment=environment):
                    self.env["CODEX_IMAGE_BACKGROUND"] = environment
                    source_args = (["--source", self.source] if subcommand == "finish"
                                   else ["--prompt-file", self.prompt])
                    self.run_cli(subcommand, "--kind", "blog-cover-bg", "--out", self.out,
                                 *source_args, "--background", "#123456")
                    with Image.open(self.out) as image:
                        self.assertEqual(image.getpixel((0, 0)), (18, 52, 86))

    def test_invalid_background_is_usage_error_before_work(self):
        for subcommand in ("finish", "generate"):
            for setting in ("flag", "env"):
                for value in ("", "white", "123456", "#FFF", "#GG0000", "#12345678",
                              " #123456", "#123456\n"):
                    with self.subTest(subcommand=subcommand, setting=setting, value=value):
                        environment = self.env.copy()
                        source_args = (["--source", self.source] if subcommand == "finish"
                                       else ["--prompt-file", self.prompt])
                        args = [subcommand, "--kind", "blog-cover-bg", "--out", self.out,
                                *source_args]
                        if setting == "env":
                            environment["CODEX_IMAGE_BACKGROUND"] = value
                        else:
                            args.extend(["--background", value])
                        completed = subprocess.run(self.command(*args), env=environment,
                                                   capture_output=True, text=True, timeout=10)
                        self.assertEqual(completed.returncode, 2, completed.stderr)
                        self.assertEqual(completed.stdout, "")
                        self.assertIn("background must be a #RRGGBB colour", completed.stderr)
                        self.assertFalse(self.home.exists())
                        self.assertFalse(self.out.exists())
                        self.assertFalse(self.capture.exists())

    def test_api_keys_are_removed_from_codex_environment(self):
        # Empty sentinel values are sufficient to detect presence without any credentials.
        self.env.update(OPENAI_API_KEY="", CODEX_API_KEY="")
        self.generate()
        self.assertFalse(json.loads(self.capture.read_text())["api_key_present"])

    def test_default_home_is_dot_codex_image(self):
        self.env.pop("CODEX_IMAGE_HOME")
        self.env["HOME"] = str(self.tmp)
        # Preserve a user-installed Pillow when changing HOME hides user site-packages.
        self.env["PYTHONPATH"] = os.pathsep.join(filter(None, (
            str(Path(Image.__file__).resolve().parents[1]), self.env.get("PYTHONPATH"))))
        data = self.finish()
        expected_home = self.tmp / ".codex-image"
        self.assertEqual(Path(data["original"]).parent, expected_home / "originals")
        self.assertTrue((expected_home / "log.ndjson").is_file())
        self.assertTrue((expected_home / "generation.lock").is_file())
        self.assertFalse(self.home.exists())

    def test_missing_pillow_exits_two_before_any_work(self):
        # Remove every sys.path entry that exposes PIL; execute the real script unchanged.
        launcher = """
import runpy
import sys
from importlib.machinery import PathFinder
sys.path[:] = [entry for entry in sys.path
               if PathFinder.find_spec('PIL', [entry]) is None]
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        for subcommand in ("status", "finish", "generate"):
            with self.subTest(subcommand=subcommand):
                completed = subprocess.run(
                    [sys.executable, "-c", launcher, str(SCRIPT), subcommand],
                    env=self.env, capture_output=True, text=True, timeout=10)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, "")
                self.assertEqual(completed.stderr,
                                 "Pillow is required; run: python3 -m pip install Pillow\n")
                self.assertFalse(self.home.exists())
                self.assertFalse(self.out.exists())
                self.assertFalse(self.capture.exists())


if __name__ == "__main__":
    unittest.main()
