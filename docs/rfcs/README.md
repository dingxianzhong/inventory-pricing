# RFCs

This directory collects short, in-repo design documents for changes
that are non-trivial enough to need a written argument but don't
warrant their own issue tracker or wiki. The format is a stripped-
down [MADR](https://adr.github.io/madr/) — just enough structure to
make the context, the proposal, and the consequences legible to a
reviewer who wasn't in the original discussion.

## When to write one

Open an RFC when a change:

- alters observable behavior of a public API,
- touches multiple modules in a coordinated way, or
- sits on a design fork where "just pick one" would erase a useful
  discussion.

Purely internal refactors, bug fixes, and documentation-only changes
do **not** need an RFC.

## Lifecycle

Each RFC lives in a single Markdown file at
`docs/rfcs/NNN-kebab-case-title.md`, where `NNN` matches the tracking
GitHub issue number (not a separate counter — keeps the mapping
one-to-one and unambiguous). The top of the file carries a `Status:`
line with one of:

- **Proposed** — under discussion; the corresponding issue is open.
- **Accepted** — decision made; implementation landed or scheduled.
- **Rejected** — decision made not to proceed; kept for history.
- **Superseded by #NNN** — replaced by a later RFC.

Status changes are PRs like any other. Once an RFC is Accepted,
subsequent behavior changes should prefer a new RFC over editing the
old one — the history of how a decision evolved is usually the most
useful thing about a repo's design archive.

## Current RFCs

| # | Title | Status |
|---|---|---|
| [021](./021-delete-on-zero.md) | `Warehouse.remove` deletion-on-zero | Proposed |
