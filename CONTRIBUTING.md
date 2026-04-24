# Contributing

## Development setup

Clone the repo and install it in editable mode with the `test` and
`lint` extras:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[test,lint]
```

### Running tests

```bash
pytest -v
```

### Linting

Two tools run on every commit (via pre-commit) and in CI:

- `ruff` — configured via `[tool.ruff]` in `pyproject.toml`
  (defaults + isort). Run locally with `ruff check inventory tests`
  or with `--fix` to auto-apply safe fixes.
- `flake8` — the classic pycodestyle/pyflakes linter.
  Run locally with `flake8 inventory tests`.

Tool versions are pinned in two places that must be kept in sync: the
`lint` extra in `pyproject.toml` (used by CI) and the `rev:` fields in
`.pre-commit-config.yaml` (used by developers locally). Bump them
together in the same commit.

### Pre-commit hooks

Install the hooks once per clone so ruff/flake8 run on every commit
automatically:

```bash
pip install pre-commit
pre-commit install
```

Run all hooks across the whole repo on demand:

```bash
pre-commit run --all-files
```

## Releases

Releases are cut by pushing a `v<version>` tag that matches the `version`
field in `pyproject.toml`. The `Release` workflow
(`.github/workflows/release.yml`) then runs the full test matrix, builds
sdist + wheel, attaches them to a GitHub Release, and uploads to
TestPyPI and PyPI.

### Authentication: PyPI Trusted Publishing (OIDC)

Uploads authenticate to PyPI and TestPyPI via
[Trusted Publishing][tp] — no long-lived API token is stored in the
repo. Each workflow run mints a short-lived OIDC credential that PyPI
validates against a pre-registered tuple of (GitHub owner, repo,
workflow filename, environment).

[tp]: https://docs.pypi.org/trusted-publishers/

This means:

- No token to rotate, leak, or forget to add. The 0.1.1-era failure
  mode of "secret silently missing from Actions scope → publish skips
  → tagged release never reaches PyPI" is structurally impossible —
  misconfiguration makes the job **fail**, not silently skip.
- Forks cannot publish. OIDC credentials are bound to the upstream
  `dingxianzhong/inventory-pricing` repo, and the workflow is
  additionally guarded with
  `if: github.repository == 'dingxianzhong/inventory-pricing'` on
  both publish jobs.

### One-time setup on PyPI / TestPyPI

If you're standing this up on a fresh repo (or re-registering after a
rename), configure each index once via the web UI:

**PyPI** — <https://pypi.org/manage/project/inventory-pricing/settings/publishing/>

- PyPI Project Name: `inventory-pricing`
- Owner: `dingxianzhong`
- Repository name: `inventory-pricing`
- Workflow filename: `release.yml`
- Environment name: `pypi`

**TestPyPI** — <https://test.pypi.org/manage/project/inventory-pricing/settings/publishing/>

- Same four fields, except Environment name: `testpypi`

(For a project that doesn't exist on (Test)PyPI yet, use the "pending
publisher" flow under the account's Publishing tab instead — it
pre-authorizes the first upload to create the project.)

On the GitHub side, create the two environments under **Settings →
Environments**:

- `pypi`
- `testpypi`

Environments may be left with default settings; they exist so the OIDC
binding has something concrete to reference. Optional hardening:
protection rules (required reviewers, tag pattern restriction to
`v*`) can be added to either environment without changing the
workflow.

### What a misconfigured run looks like

Unlike the previous token-based flow, a missing or misconfigured
publisher registration causes the publish job to **fail**, not
silently succeed. The failing step is the
`pypa/gh-action-pypi-publish` action itself, and its error message
names the mismatched field (wrong workflow filename, wrong
environment, unregistered repo, etc.). Fix the registration on the
PyPI side and re-run the workflow with `gh run rerun <id>` — no
re-tagging needed.
