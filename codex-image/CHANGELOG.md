# Changelog

## 1.0.0 (2026-10-21)

First public version.

- Generate images through the authenticated Codex CLI and finish PNGs in four blog and LinkedIn formats.
- Preserve originals and an append-only local log, with a serialized daily cap counting started CLI calls.
- Flatten transparency onto configurable `#RRGGBB` backgrounds, defaulting to white; keep compressed output as opaque palette PNG.
- Include an image skill with mandatory visual checks, a two-generation maximum and a ready-prompt fallback.
- Support Python 3.9+ with Pillow as the only runtime dependency outside the standard library.
