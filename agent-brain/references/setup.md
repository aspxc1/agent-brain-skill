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

## Choose or move the brain folder

Choose any agent-neutral folder the intended harnesses can read and write. The
brain does not need to be under Codex, OpenCode, or the skill repository. All
harnesses share memories only when their resolved roots identify the same store;
different copies with the same folder name are separate stores.

To move an existing brain while preserving its identity:

1. Stop other writers. Rerun the current installer against the old root once so
   its machine-local manifest records the existing `brain_id`.
2. Move the whole folder, including `brain.json`, to an unused destination. Keep
   its contents intact; do not run `init` to create a replacement brain.
3. Rebind the shared skill and every installed harness bootstrap explicitly:

   ```text
   python agent-brain/scripts/install.py --brain "<new folder>" --previous-root "<old folder>" --bootstrap codex opencode
   ```

4. Check explicit task paths and any `AGENT_BRAIN_ROOT` overrides. Start fresh
   harness sessions if startup guidance was already loaded with the old path.
5. Run `brain.py status` from each configured entry point. Verify the same resolved
   root and `brain_id`, then read back a saved contribution through both routes.

`--previous-root` authorizes rebinding the same recorded brain, not switching to
an unrelated one. The installer compares identities before modifying configuration.
It updates the shared root config and selected bootstrap blocks; it does not move
the folder itself or change sandbox permissions. Include Claude's bootstrap when
Claude is actually installed. Existing unrelated guidance is preserved.

## Automatic retrieval and saving

With the bootstrap installed, a configured agent is instructed to load relevant
project memories and scoped mistakes before substantive work, and save useful
milestone/handoff summaries. It can create a project's contribution directory and
curated overview as needed. No separate manual project registration is required.
This remains instruction-driven behavior: it is not a background recorder of
every conversation or a guarantee that a save ran. The harness must load the
guidance and have file access. For a definite checkpoint, ask it to save a project
handoff and report the saved path. Native OpenCode/Claude execution is verified
only after observing those harnesses, not merely by reading their configuration.

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
