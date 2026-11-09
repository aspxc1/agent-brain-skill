# Memory format

The helper generates YAML frontmatter using JSON-quoted scalar values, which are
valid YAML. No YAML library is required at runtime. Plain Markdown stays readable
in Obsidian, editors, and harness file tools. Relative Markdown links are portable.

## Pending contributions

Required helper fields: `id`, `kind`, `project`, `created_at` (UTC), `harness`,
`agent`, `source`, `evidence`, and `status: pending`. Kind is session, decision,
preference, practice, or handoff. Evidence is reported, observed, or user-confirmed;
it records the contributor's claim, not a cryptographic attestation. Use the least
strong accurate value and label individual claims when evidence is mixed.

Body contract, usually 150-400 words, shorter for one correction:

```markdown
# Project Lantern handoff

## Outcome
Implemented the package-manager migration. Release remains pending.

## Decisions and scope
- Use pnpm for Lantern only. Source: explicit user instruction in this session.
- Existing general npm preference is unchanged.

## Evidence
- Observed: inspected package.json and pnpm-lock.yaml in commit abc1234.
- Reported: OpenCode worker says tests passed; output has not been inspected.

## Open issues and next action
- Run or inspect the relevant test command output before marking verification complete.
- Confirm the release version, then follow the project's release process.

## Sources
- Session reference: session-lantern-17.
- Repository: owner/lantern; branch package-migration; commit abc1234.
```

Replace illustrative values with actual evidence. Omit empty sections. Record
concrete reproduction steps and unsuccessful approaches only if they prevent
repeated work. Keep raw transcripts, secrets, and copied source documents out.

## Canonical project overview

Use `projects/<slug>/overview.md`. Include project identity and local/repository
location, purpose, current status and last-verified date, scoped decisions with
reasons, relevant commands, actual verification evidence, open issues, next
action, and links to contributing note IDs. Include only sections with content.
Avoid duplicating a whole repository README. A note's modification date alone
does not establish the freshness or correctness of its claims.

## Profile and practices

Each durable entry carries its scope, source, and date. Profile stores explicit
preferences; observations remain tentative. Practices has separate Adopted and
Proposed sections. Adoption requires an explicit user statement or an existing
policy with a stated scope; a curator cannot infer universal adoption from one
successful project. Never infer demographic, medical, financial, or other
sensitive profile details from incidental task context.

For corrections, link the replacement to the superseded entry and say why. For
unresolved conflicts, retain both claims with their sources and ask only when the
choice affects the present task. A forget request removes the content rather
than preserving a superseded copy.
