# GitHub submission guide — IRIS-48H-10

This package is an isolated fixture-driven prototype. It has **not** been merged into the assessment repository and must not be represented as an already-open pull request.

## Safe submission route

1. Open the assessment repository: <https://github.com/amaurisantosjr/iris-sample>.
2. Use **Fork** to create a copy under your own account. Do not request write access to, or push directly to, the maintainer's repository.
3. Clone your fork locally, create a branch such as `feat/iris-48h-10-water-mine-adapters`, and copy this entire `iris48h10_adapters/` directory into the root of the clone.
4. From inside `iris48h10_adapters/`, install dependencies and run tests using the commands below.
5. Inspect `git diff`, then commit and push the branch to your fork.
6. Open a pull request from your fork/branch to the assessment repository if the repository allows it. Include the commit hash and test output in the PR description. If PRs are not possible, submit a ZIP with the same artefacts as instructed by the assessment brief.

## Local commands

From inside `iris48h10_adapters/`:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m adapters.cli --fixtures-dir fixtures --output outputs/facility-risk.json --as-of 2026-10-24
```

The date is explicit for reproducibility; use the assessment's actual evaluation date if relevant. Include the complete test output from your own environment, not just a copied result file.

## Suggested commit

```bash
git add iris48h10_adapters
git diff --cached --check
git diff --cached --stat
git commit -m "Add fixture-driven water and mine risk adapters"
git push -u origin feat/iris-48h-10-water-mine-adapters
```

## Suggested PR description

> Adds a focused, fixture-driven prototype for one water-right record and one mine/shaft record, normalized into a shared facility-level spatial-risk output. Includes synthetic fixtures, traceable `REVIEW_REQUIRED` flags, deterministic output, geometry QA behavior, automated tests, setup instructions, and a limitations/licensing note. No production systems, credentials, unauthorized scraping, or real-world coordinates are used.

## Before submitting

- Confirm the correct target repository and latest default branch.
- Keep all fixtures clearly synthetic unless a real provider source is explicitly permitted and documented.
- Review the employer's instructions on public forks, repository visibility, and IP/reuse rights.
- Ensure no credentials, secrets, private data, or unrelated local files are committed.
- Report unfinished work honestly; this prototype is not production-integrated and does not establish legal or engineering safety conclusions.
