# Setup and harness integration

## Storage choice

Use a local folder of Markdown notes as the canonical store. Obsidian can open an
existing folder as a vault without changing the memory protocol. Notion can be a
later, user-authorized publishing view; an export/import or bidirectional sync is
a separate integration, not part of this skill. Avoid maintaining two competing
canonical stores.

Keep the actual brain outside this skill's repository. `brain.local.json` stores
the per-machine root and is ignored by Git. `AGENT_BRAIN_ROOT` overrides that
config when explicitly set by the environment; `--root` overrides both. Root
resolution does not scan the disk or guess between multiple brains.

## Install

From the source repository, using any available Python 3.10+:

```text
python agent-brain/scripts/brain.py --root "<absolute local folder>" init
python agent-brain/scripts/install.py --brain "<absolute local folder>" --bootstrap codex opencode --dry-run
python agent-brain/scripts/install.py --brain "<absolute local folder>" --bootstrap codex opencode
```

The installer copies one skill into `~/.agents/skills/agent-brain`, a location
documented by both Codex and OpenCode. It writes only that skill and the selected
harnesses' small marked bootstrap blocks. Existing unrelated global guidance is
preserved; its initial contents are backed up alongside it before modification.
It refuses to overwrite unmanaged skills, locally edited installed files, or a
different configured brain root. No administrator rights or Python packages are
needed. Harness sandbox approval may still be needed for installation or memory
access outside a current workspace.

The optional bootstrap loads this skill at substantive project starts and asks
for useful milestone summaries. It is guidance executed by the harness during
tasks, not a daemon, guaranteed per-message hook, or retrospective chat importer.
Without it, use explicit invocation or normal automatic skill discovery.

Paths for bootstrap blocks:

| Harness | Global guidance |
|---|---|
| Codex | `$CODEX_HOME/AGENTS.md`, or `~/.codex/AGENTS.md` |
| OpenCode | `$XDG_CONFIG_HOME/opencode/AGENTS.md`, or `~/.config/opencode/AGENTS.md` |
| Claude Code, when requested | `~/.claude/CLAUDE.md` |

`--home` selects a different home for portable installs/tests and intentionally
uses its `.codex` and `.config` folders rather than the host's environment overrides.

Codex: invoke `$agent-brain` or ask to resume/remember a project. OpenCode: mention
`@agent-brain`, or ask it to load the skill using its available skill tool. Start a
fresh session if discovery does not refresh. Do not claim an installed skill was
loaded by a harness until observed in that harness.

## Claude Code later

Claude supports user skills in `~/.claude/skills/<name>/SKILL.md`. Copy this skill
folder there when setting up Claude; keep its `brain.local.json` pointing to the
same brain. Avoid installing duplicate definitions into a harness that already
discovers the shared folder. The installer can add Claude's bootstrap with
`--bootstrap claude` when requested, but it intentionally leaves the native
Claude skill-folder copy as a separate explicit setup step. Directly reading the
absolute SKILL.md path from the bootstrap also works without native discovery.

## Updating and removing

Edit the source repository, validate, then rerun the installer. Installed local
edits are rejected so they can be preserved first. The installer updates source
files but does not delete obsolete installed files; inspect removed resources
when changing skill versions. Keep personal path config and memory out of commits.

For a brain initialized before `mistakes.md` existed, inspect whether the register
is missing and create it with `publish mistakes.md --expected-sha missing` using
the new template or sourced lessons. `init` does not modify existing brains; do
not replace an existing register or other user notes when adding this file.

To stop use, remove only the marked Agent Brain blocks from selected harness
guidance and remove the installed skill directory after checking its exact path.
The actual brain is separate and remains intact. No uninstall deletes memories.

## Verified documentation

- [Codex local skill discovery](https://learn.chatgpt.com/docs/build-skills)
- [Codex global and project guidance](https://learn.chatgpt.com/docs/customization/overview)
- [OpenCode skill discovery](https://opencode.ai/docs/skills/)
- [OpenCode global rules](https://opencode.ai/docs/rules/)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Obsidian: open an existing folder as a vault](https://help.obsidian.md/Files+and+folders/Manage+vaults)
