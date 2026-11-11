# reverse-engineer

**Nederlands, kort.** Je ziet een post waarin iemand iets weggeeft als je reageert, of waarin iemand een bouwer zoekt. Deze skill leest de post en zegt eerst welke vorm past: een plak-prompt, een skill, een plugin, een proefversie, een site of "koop het gewoon". Daarna helpt hij je het zelf te bouwen. Hij noemt het stuk dat echt lastig is, hoe lang het duurt en wat zelfbouw niet doet. De skill en de plak-prompt zijn Nederlands. Geen Claude Code? Plak [`PLAK-PROMPT.md`](PLAK-PROMPT.md) in ChatGPT of Claude in de browser.

---

A skill that reads a LinkedIn post and helps you build the thing yourself. It handles two kinds of posts:

- **Comment gates**: "comment WORD and I'll send you X".
- **Search requests**: "who knows someone who can build Z".

The goal is that you learn to build it. The skill is written in Dutch and answers in Dutch.

## Two ways to use it

| You have | Use |
|---|---|
| ChatGPT or Claude in the browser | Copy [`PLAK-PROMPT.md`](PLAK-PROMPT.md) into a new chat, then paste the post |
| Claude Code or the Claude desktop app | Install the skill (below) and say "reverse-engineer deze post" |

The paste prompt and the skill follow the same steps and produce the same sections. The skill can also look things up and write files; the paste prompt tells you what to check yourself.

## Install

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install reverse-engineer@claude-code-toolkit
```

Or copy `skills/reverse-engineer/` to `~/.claude/skills/`. The folder is self-contained.

## Spec

This section is the contract. The skill and the paste prompt are tested against it.

### Input

The text of one post, pasted or as a file, plus its image or carousel as a screenshot. Optionally the visible comments and a link.

The image matters. The promise of a comment gate increasingly sits in the image instead of the text, presumably because LinkedIn shows posts with "comment WORD" in the text to fewer people. When the text asks for a comment without saying what you get, the skill asks for the image before it goes on.

The post and its image are treated as a quotation. Anything in it that reads like an instruction is content to analyse and is never followed.

### Step 1: what kind of post

| Kind | Signal | The reader |
|---|---|---|
| Comment gate | Something is promised in return for a comment, a follow or an email address | Someone who wants the promised thing |
| Search request | Someone asks for a person or a product | The person asking, or someone who wants to answer with a working example |
| Neither | No promise and no request | The skill says so and stops |

### Step 2: is it already there

Before anything is built, the skill checks whether the answer already exists:

- in the post itself (many gates list the full content),
- in an update or a comment by the maker (the promised file is sometimes already public),
- as a free or cheap product,
- as a starting point in an existing repository, usually on GitHub. The skill always looks for one, also when the outcome is to build.

A repository is only named after the skill opened it and checked five things on the page: last change within a year, a licence (none means it cannot be used), stars as a signal, a README that says how to start it, and a size the reader can follow. At most three. The first build step is then to have the repository explained with [`onder-de-motorkap`](../onder-de-motorkap/) before running any of it.

If it exists, the outcome is "koop het gewoon" and the skill says where. Asking the maker is a valid outcome too: when the maker's version is better than what you would build in an evening, the skill says so.

### Step 3: choose the form

The form is chosen first, with a decision tree, and stated with one reason. The first form that fits is the smallest that does the job.

A comment gate is a lead magnet, so what it gives away is almost always small: a document, a checklist, a template, a few prompts or a list. The answer is never bigger than the post. Most comment gates end at question 1 or 2. A tool or a site is usually a search request.

```
1. Does it exist, good enough, for less than an evening's work?  yes -> use what is there
2. What is given away or asked for?
     a document, checklist or hand-out -> paste prompt that writes your own version
     a template -> paste prompt that builds it
     prompts -> the prompt itself
     a list of tools or sources -> the list, in the answer
     a workflow between apps -> automation
     something you use again and again (a GPT, an assistant, a "system") -> 3
     something for other people (a tool, a site) -> 4
3. How big?       one task -> project or skill
                  steps that feed each other -> plugin
4. What do they do with it?   read and look -> site
                              fill something in and get a result -> tool (first version: proof of concept)
```

Only for a tool or a site: does it involve payment, login or customer data? Then that is the hard part, solved with a platform or a hire. For every form with AI in it: which part needs a model and which part is fixed rules.

The check on the choice depends on the kind of post. For a comment gate: is it easier than commenting? For a search request: does the reader know afterwards what they can do themselves and what they still need to hire?

### Step 4: the answer

Every answer has these sections, in this order. When the outcome is "use what is there", sections 4 to 7 are at most three sentences each and the receipt has at most three rows: the reader's two-minute answer should not become a long read.

1. **De vraag.** What is promised or asked, in the skill's own words. The post is not copied.
2. **Het oordeel.** The form, and why this form and not the one next to it.
3. **Wat er al is.** What is already in the post, in the comments or for sale.
4. **Het lastige stuk.** The one part that takes real effort. Most of any build is routine; this section names the part that is not.
5. **Tijd.** How long a first build takes and how long a practised one takes. Stated as an estimate, with what it depends on.
6. **Wat zelfbouw niet doet.** The limits, before you start: upkeep, payments, security, the maker's own expertise.
7. **Zo bouw je het.** Steps that run, in order, with the exact prompt or file where one is needed, and what to do where it usually gets stuck.
8. **Het bonnetje.** For a search request: every condition from the post as a row, in the skill's own words, with how to test it and whether it is met. For a gate: every promised part and whether your build covers it. Before the build the last column says "nog te toetsen".

The answer never copies the post. Conditions and promises are described in the skill's own words, so the answer can be published without the maker's text.

### Tone

The skill helps. It does not unmask anyone.

- No judgement about the maker of the post, their motives or their business model.
- What a gate asks in return (a comment, a follow, an address) is stated as a fact, once, without comment.
- If the maker's work is good, the skill says so.
- The skill builds your own version. It does not recreate someone's paid or proprietary material.

### What the skill does not do

- It does not call a model on its own or run unattended. You run it in your own session.
- It does not invent links. A link is either one the skill opened, or it is given as a search term.
- It does not promise that a build is finished work. A proefversie has no real content, no payments, no upkeep and no security review.

## Tested on

Three real posts, kept outside this repository:

| Case | Kind | Outcome the spec requires |
|---|---|---|
| A CEO looking for a solo builder for a product site with a shop link | Search request, site | Site, with every condition from the post as a row |
| A coach who wants to sell a custom GPT as a stand-alone tool | Search request, tool | Proefversie, with the part that needs no model named |
| A privacy lawyer promising a hand-out on AI recorders for a comment | Comment gate | Koop het gewoon: the maker has since published the hand-out for free |

## Files

```
reverse-engineer/
├── README.md            this file, with the spec
├── PLAK-PROMPT.md       the same steps for ChatGPT and Claude in the browser
├── CHANGELOG.md
└── skills/reverse-engineer/SKILL.md
```

## License

MIT. See [`LICENSE`](../LICENSE).
