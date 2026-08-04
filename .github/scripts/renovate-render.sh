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
# Renovate's own commit -- no separate push/credential needed.
#
# Deliberately narrower than `just render`: no full wipe-and-regenerate, since
# this only needs to reconcile already-templated files, not audit for
# orphaned/removed template files (that's what the human-reviewed `consistency`
# job and `just render` are for). copier itself only touches files it manages
# (or creates none for files with no template source), so files with no
# .jinja counterpart -- like render-template.yaml -- are never touched here
# and don't need restoring. `justfile`/`.gitignore` DO have generic template
# counterparts that would clobber this repo's self-only customizations, so
# those are snapshotted from the working tree (not git HEAD -- Renovate's own
# edits this round aren't committed yet, so HEAD would be stale) and restored
# after the copy.
#
# Runs via uvx instead of the Nix devshell (unavailable in Renovate's runner).
# copier.yaml requires the jinja2-git-dir extension, which isn't a stock
# copier feature -- inject it explicitly, pinned to what copier-flake bundles.
set -euo pipefail

PRESERVE=(justfile .gitignore)
SNAPSHOT_DIR=$(mktemp -d)
trap 'rm -rf "$SNAPSHOT_DIR"' EXIT

for f in "${PRESERVE[@]}"; do
  [[ -f "$f" ]] && cp "$f" "$SNAPSHOT_DIR/$(basename "$f")"
done

uvx --with jinja2-git-dir==0.5.0 copier==9.13.1 copy --vcs-ref=HEAD --trust --defaults \
  --data-file includes/copier-answers-sample.yml -f . .

for f in "${PRESERVE[@]}"; do
  [[ -f "$SNAPSHOT_DIR/$(basename "$f")" ]] && cp "$SNAPSHOT_DIR/$(basename "$f")" "$f"
done

# copier always restamps _commit/created_on; not something Renovate ever
# legitimately touches, so reverting to the last commit is safe.
git checkout -- .copier-answers.yaml 2>/dev/null || true
