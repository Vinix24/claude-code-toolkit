# slop-lint

A deterministic linter for AI tics in Dutch prose. In Claude Code it lints every text file Claude writes and hands the findings back, so Claude fixes them in the same turn. A skill runs the same check on demand, also in Claude Desktop.

**Built for Dutch.** The rules target Dutch prose (with English variants of the word-list rules), and the rule names, output and skill are in Dutch.

## The problem

Writing rules in `CLAUDE.md` load into every session and still do not hold. In the corpus these rules were measured on, the writing rules said "no em-dashes" in every session, and the text contained 3,282 of them. An instruction the model may follow is not a check.

A hook is. Claude Code runs it after every `Write` and `Edit`, whatever the model decides. This plugin never blocks a write: in prose a finding is a judgement call, not an error. It reports, and Claude repairs what is a real tic.

## What it catches

25 rules in three layers, measured on over 300,000 words of real prose rather than taken from a list.

| Layer | Rules | Example it flags |
|---|---|---|
| `lexicaal` (word list) | `buzzword`, `ai-opener`, `ai-overgang`, `eerlijk-tic`, `caveat`, `is-echt-calque`, `em-dash` | "Een revolutionair systeem — echt waar." |
| `structuur` (comma chains) | `komma-en`, `komma-maar`, `komma-dan`, `komma-dus`, `komma-want` | "Ik heb het nagekeken, en het klopt deels." |
| `frames` (rhetorical skeletons) | `niet-X-maar-Y`, `geen-X-maar-Y`, `drieslag`, `drieslag-met-en`, `niet-alleen-maar-ook`, `not-just-X` and seven more | "De aanpak is sneller, beter, slimmer." |

The measurement behind the layers: the word list is nearly a solved problem (five buzzwords in 310,000 words), while the comma structure accounts for most of the volume (1,219 times `, en`). A list of equal items ("A, B, C, en D") does not count as `komma-en`.

## Install

### Claude Code

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install slop-lint@claude-code-toolkit
```

From a terminal: `claude plugin marketplace add Vinix24/claude-code-toolkit`, then `claude plugin install slop-lint@claude-code-toolkit`. Add `--scope project` to install it for one project only.

It needs `python3` (3.9 or newer, standard library only) and `sh`. Word files are linted only when the interpreter has `python-docx`; point `SLOP_LINT_PYTHON` at one that does.

### Claude Desktop (chat and Cowork)

Add the same marketplace under Customize > Plugins > Add > Add marketplace (`Vinix24/claude-code-toolkit`), or upload the `slop-lint` folder as a zip. Cowork needs a paid plan and the macOS or Windows app ([platform support](https://claude.com/docs/plugins/platform-support), [getting started with Cowork](https://support.claude.com/en/articles/13345190-getting-started-with-cowork)).

What works where:

| | Hook (automatic after each write) | Skill `slop-check` (on demand) |
|---|---|---|
| Claude Code (terminal, IDE, desktop Code tab) | Yes, tested | Yes, tested |
| Cowork | Loaded per Anthropic's docs. Whether `PostToolUse` fires is not documented, and a public report says plugin hooks never run in Cowork. Do not count on it | Yes, when Python is available in the session |
| Chat | No, chat ignores hooks | Yes, in the code execution sandbox |

So outside Claude Code, ask for the check: "check deze tekst op slop", or `/slop-lint:slop-check`. A plugin installed through claude.ai also syncs to Claude Code as a synced plugin, where the hook does run.

The skill folder `skills/slop-check/` is self-contained: the script imports nothing outside it. It works without the rest of the plugin.

## Configuration

Settings are read from, in this order, each overriding the one before per key:

1. the defaults;
2. `~/.claude/slop-lint.json`, for all projects (always in the home directory, also when `CLAUDE_CONFIG_DIR` points elsewhere, so one file serves several accounts);
3. the nearest `.claude/slop-lint.json`, searched upwards from the file being linted (hook) or the current directory (command line);
4. a file passed with `--config` (command line only).

Lists replace each other; `rules` and `profiles` are merged per name. A bad value falls back to the previous one with a message on stderr. Cowork does not read `~/.claude`, so there only a project file in a connected folder can apply.

| Key | Default | What it does |
|---|---|---|
| `enabled` | `true` | `false` switches the hook off for the project. The command line still runs when you call it |
| `include` | `["*"]` | Globs for the files the hook lints, relative to the project folder (the folder that holds `.claude/`). `*` also matches across folders |
| `exclude` | `[]` | Globs the hook skips, on top of the built-in `node_modules`, `.git`, `dist`, `build`, `.venv`, `vendor` and `.claude` |
| `extensions` | `[".docx", ".eml", ".md", ".txt"]` | File types that are linted |
| `disable` | `[]` | Rule names to switch off, for example `["komma-maar"]` |
| `rules` | `{}` | Your own rules: `{"naam": "regex"}` or `{"naam": {"pattern": "regex", "layer": "frames"}}`. Without a layer they land in `eigen`. A rule with a built-in name replaces that rule |
| `min_words` | `40` | Files with fewer words are skipped |
| `max_density` | `null` | Report only above this many findings per 1,000 words. `null` reports every finding |
| `profiles` | `{}` | Named sets of paths for the command line: `{"blog": ["Content/blog"]}` |

An example for a content repository:

```json
{
  "include": ["Content/*", "docs/*"],
  "exclude": ["Content/archief/*"],
  "disable": ["komma-maar"],
  "rules": {"kortom": "\\bkortom\\b"},
  "profiles": {"blog": ["Content/blog"]}
}
```

To switch the hook off for one shell: `CLAUDE_SLOP_LINT=off`. To switch it off everywhere: `/plugin disable slop-lint@claude-code-toolkit`.

To keep a single line, put `slop-negeer:` with a reason on it: `"Sneller, beter, slimmer." slop-negeer: citaat uit de brochure`.

## Command line and CI

```
python3 skills/slop-check/scripts/slop_lint.py tekst.md           # files or folders
python3 skills/slop-check/scripts/slop_lint.py --profiel blog     # a profile from the config
python3 skills/slop-check/scripts/slop_lint.py --uit komma-maar   # switch a rule off for this run
python3 skills/slop-check/scripts/slop_lint.py --laag structuur   # one layer only
```

Exit code 1 when something is found, 0 when clean, 2 on a usage error.

A gate at zero stops almost everything at first: on the measured corpus it would have blocked 49 of 60 published posts, and a gate that blocks everything gets switched off. Use `--max-dichtheid N` as a ratchet instead: set it at the current median, and only ever lower it.

## What it does not do

- It matches patterns, not meaning. Every finding is a prompt to look, and Claude is told that a list of equal items or a quote is not a tic.
- The hook only sees `Write` and `Edit`. A file produced by a script through `Bash` is not linted.
- It never blocks a write, and a broken installation never blocks the session: the shim never exits 2.

## Tests

```
cd slop-lint
python3 -m pytest -q
```

Each rule is tested with a sentence it must catch and a close sentence it must not. The hook is tested end to end through `run.sh`, with an isolated `HOME`.
