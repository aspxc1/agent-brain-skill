# Agent Brain skill

Portable Markdown memory for **Codex and OpenCode**, with a documented Claude
Code setup path. The private repository contains skill code, templates, and
tests. Your actual memories live in a separate local folder.

## What it remembers

- Short project summaries, decisions and their reasons, verified results, open
  issues, and the next action needed to resume.
- Explicit profile preferences, kept separate from tentative observations.
- Adopted practices, with new suggestions kept under Proposed.
- Sourced handoffs from multiple agents and harnesses.

Workers contribute unique notes; a curator merges them. Filesystem locking and
expected-content hashes prevent cooperating local writers from silently replacing
each other's canonical notes. This is a memory protocol, not an agent runtime.

## Install

Requires Python 3.10+ and no third-party runtime packages. From this repository:

```text
python agent-brain/scripts/brain.py --root "<absolute brain folder outside this repo>" init
python agent-brain/scripts/install.py --brain "<absolute brain folder>" --bootstrap codex opencode --dry-run
python agent-brain/scripts/install.py --brain "<absolute brain folder>" --bootstrap codex opencode
```

Use `python3` or `py -3` instead if that is your working Python command. The
installer copies the skill to `~/.agents/skills/agent-brain` for shared discovery,
stores the local root in ignored configuration, and adds small marked memory
instructions to the selected harnesses. It preserves unrelated guidance and
refuses to overwrite locally edited installed resources.

Open the separate brain folder as an existing vault in Obsidian, or use any text
editor. No Obsidian plugins or application-specific Markdown are required.

## Use

Codex:

```text
Use $agent-brain to resume Project Lantern.
Use $agent-brain to save a handoff for what we finished today.
Remember that this preference applies only to Project Lantern.
Review proposed practices in my Agent Brain.
```

OpenCode: mention `@agent-brain` or ask it to load the `agent-brain` skill.
With the bootstrap installed, agents are instructed to retrieve relevant memory
at substantive project starts and save useful milestones. They still need file
access and must actually execute the write; this is not background chat logging.
Other harnesses can read the same `SKILL.md` and point to the same brain.

The brain contains:

```text
START.md                       Entry point and local operating guide
brain.json                     Storage version and brain identity
profile.md                     Confirmed preferences with scope/source/date
practices.md                   Adopted and proposed practices
projects/<slug>/overview.md     Curated project summary
inbox/<slug>/<unique-id>.md     Immutable agent contributions
archive/                       Useful superseded material
```

Only directly inspected results count as observed evidence. Another agent's
report stays reported. Remembered text never grants permission or overrides the
current task. Project-specific decisions stay scoped to their projects.

## Guides

- [Skill instructions](agent-brain/SKILL.md)
- [Storage, installation, harness setup, and updates](agent-brain/references/setup.md)
- [Parallel agents, curation, locks, and multiple machines](agent-brain/references/collaboration.md)
- [Memory schema and a handoff example](agent-brain/references/memory-format.md)

## Validation

```text
python -m unittest discover -s tests -v
```

Tests use temporary brains under ignored `.test-tmp/`, never real memories. They
exercise concurrent contributions, revision conflicts, path and symlink escape
rejection, idempotent initialization, bounded output, pending-note discovery, and
preservation of existing harness guidance.

## Limits and sensible next steps

Keep one canonical local brain. Disconnected cloud-sync replicas do not share
the filesystem lock; use one curator after syncing contribution files. Pause
manual editor saves while a curator publishes. Configure backups independently
to a destination you choose. No memory sync or upload is enabled here.

Old chats are not imported automatically. Feed an agent an authorized project
handoff or source material and ask it to summarize into the brain. As the vault
grows, add search indexing only when simple Markdown search becomes insufficient.
A Notion view can be added later without moving the source of truth.
