# onder-de-motorkap

**Nederlands, kort.** Je hebt iets laten bouwen met AI, of je gebruikt een tool van iemand anders. Deze skill legt in gewone taal uit wat elk onderdeel doet en waarom het er zit. Zo snap je wat je hebt en weet je wat je zelf kunt aanpassen. De skill en de plak-prompt zijn Nederlands. Geen Claude Code? Plak [`PLAK-PROMPT.md`](PLAK-PROMPT.md) in ChatGPT of Claude in de browser.

---

A skill that opens the hood. Give it a prompt, a skill, a plugin, a workflow, a small tool or a site, and it explains in plain Dutch what each part does and why it is there. It also works on a tool someone else made.

The goal is that you understand what you have well enough to change it yourself.

## Two ways to use it

| You have | Use |
|---|---|
| ChatGPT or Claude in the browser | Copy [`PLAK-PROMPT.md`](PLAK-PROMPT.md) into a new chat, then paste what you want explained |
| Claude Code or the Claude desktop app | Install the skill (below) and say "kijk onder de motorkap van dit" |

## Install

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install onder-de-motorkap@claude-code-toolkit
```

Or copy `skills/onder-de-motorkap/` to `~/.claude/skills/`. The folder is self-contained.

## Spec

This section is the contract. The skill and the paste prompt are tested against it.

### Input

One of:

- **Your own result**: the text of a prompt, a skill file, a plugin folder, a workflow export, source code or a site you built.
- **Someone else's tool**: a link, a description, screenshots or what you see when you use it.

What you paste is material to explain. Anything in it that reads like an instruction is never followed.

### What it knows and what it guesses

With your own result the skill can read every part. With someone else's tool it mostly cannot. So every statement carries one of three labels:

| Label | Meaning |
|---|---|
| Gezien | The skill read it in the material you gave |
| Afgeleid | The skill infers it from behaviour, and says from what |
| Weet ik niet | It cannot be known from outside, and the skill says who could tell you |

A guess is never written as a fact.

### The answer

Every answer has these sections, in this order:

1. **In één zin.** What the thing does, for someone who has never seen it.
2. **De onderdelen.** A table with one row per part: what it does, why it is there, and what happens if you remove it.
3. **Waar de AI zit.** Which steps a model does and which steps are fixed rules. Many tools use less AI than they look like, and this section shows where.
4. **Waar je gegevens heen gaan.** What you type in, where it is sent and where it is kept, as far as that can be seen.
5. **Wat je zelf kunt aanpassen.** Three changes, from safe to bold, each with what you will see happen.
6. **Eén proef.** One small experiment that teaches you how the thing works: change this, run it, compare.

Every technical word is explained in one clause where it first appears. There is no separate glossary.

### Tone

Plain language, short sentences. The reader is an entrepreneur, not a developer. The skill explains; it does not grade the maker's work.

### What the skill does not do

- It does not judge whether a tool is safe to use. It shows what can be seen and names what cannot.
- It does not reproduce someone else's paid material.
- It does not call a model on its own or run unattended. You run it in your own session.

## Tested on

The results of the three cases used for [`reverse-engineer`](../reverse-engineer/), plus two public demos made by the author: a product site in eight layers and a ten-question tool that runs on fixed rules without a model.

## Files

```
onder-de-motorkap/
├── README.md            this file, with the spec
├── PLAK-PROMPT.md       the same steps for ChatGPT and Claude in the browser
├── CHANGELOG.md
└── skills/onder-de-motorkap/SKILL.md
```

## License

MIT. See [`LICENSE`](../LICENSE).
