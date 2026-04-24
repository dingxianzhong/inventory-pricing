# Contributing

## Releases

Releases are cut by pushing a `v<version>` tag that matches the `version`
field in `pyproject.toml`. The `Release` workflow
(`.github/workflows/release.yml`) then runs the full test matrix, builds
sdist + wheel, attaches them to a GitHub Release, and (optionally)
uploads to TestPyPI and PyPI.

### Required repository secrets

Two Actions secrets gate the PyPI uploads. They are **optional** in the
sense that the workflow is designed not to fail when they are absent
(so forks and test-tag pushes stay green), but if you want a tag to
actually reach PyPI, both must be set:

| Secret name           | Where to get it                         | Used by                   |
| --------------------- | --------------------------------------- | ------------------------- |
| `TEST_PYPI_API_TOKEN` | <https://test.pypi.org/manage/account/> | `testpypi-publish` job    |
| `PYPI_API_TOKEN`      | <https://pypi.org/manage/account/>      | `pypi-publish` job        |

Add them under **Settings → Secrets and variables → Actions → Repository
secrets**. The `gh` CLI equivalent (from a clone of this repo):

```bash
gh secret set TEST_PYPI_API_TOKEN --repo dingxianzhong/inventory-pricing
gh secret set PYPI_API_TOKEN      --repo dingxianzhong/inventory-pricing
```

Note: the secrets live under the **Actions** scope specifically — not
Dependabot secrets, not Codespaces secrets, and not Variables. An
easy-to-make mistake is putting them in the wrong tab; if that happens,
the publish jobs will silently skip (see below).

### What a missing-secret run looks like

If either token is absent when a `v*` tag is pushed, the corresponding
publish job still reports success (by design) but emits a workflow
annotation at the top of the run summary page:

> ⚠️ **PyPI publish skipped** — `PYPI_API_TOKEN` secret is not set on
> this repository, so the PyPI upload was skipped. …

The annotation is yellow, appears above the job graph, and links back
to the repo's secrets page. If you tagged a release expecting it to
publish and you see one of these annotations instead, the fix is to
add the missing secret and re-run the workflow (`gh run rerun <id>`) —
no re-tagging needed.

This warning exists because we shipped the 0.1.1 release with three
successive green workflow runs that were all silently skipping
publish; the annotation makes that state impossible to miss on the
next round. The longer-term fix is migrating to PyPI trusted
publishing (OIDC), tracked in issue #3, which removes the need for
long-lived tokens entirely.
