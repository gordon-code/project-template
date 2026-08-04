#!/usr/bin/env bash
# Renovate postUpgradeTask, run before Renovate's own commit is made.
#
# Renovate's native github-actions manager and this repo's .jinja customManagers
# (.github/renovate.json) can each resolve a different version string for the
# same SHA-pinned action/flake input -- e.g. the native manager writes the exact
# newest release tag (v7.0.1) into root .yaml files, while the .jinja source
# resolves independently for the same dependency. Left alone, this makes the
# `consistency` job in pr-checks.yaml fail on every non-major bump, since it
# re-renders from the .jinja sources and diffs against the checked-in files.
#
# Re-rendering here, before Renovate commits, folds any resulting diff into
# Renovate's own commit -- no separate push/credential needed. Mirrors
# `just render`, minus the Nix devshell (unavailable in Renovate's runner);
# copier is installed via pipx in khepri-deps/renovate's workflow instead.
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
command -v copier >/dev/null 2>&1 || pip install --quiet --user copier

find . -maxdepth 1 \
	! -name '.' ! -name '.git' ! -name '.venv' ! -name '.direnv' \
	! -name '.serena' \
	! -name 'template' ! -name 'includes' ! -name 'copier.yaml' \
	! -name 'hack' ! -name 'tests' ! -name 'pytest.ini' \
	! -name 'flake.lock' ! -name 'CHANGELOG.md' \
	-exec rm -rf {} +

copier copy --vcs-ref=HEAD --trust --defaults \
	--data-file includes/copier-answers-sample.yml -f . .

git show HEAD:lib/nix/project.nix > lib/nix/project.nix 2>/dev/null || true
git show HEAD:justfile > justfile 2>/dev/null || true
git show HEAD:.gitignore > .gitignore 2>/dev/null || true
git show HEAD:.github/workflows/render-template.yaml > .github/workflows/render-template.yaml 2>/dev/null || true
git checkout -- .copier-answers.yaml 2>/dev/null || true
