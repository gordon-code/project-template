#!/usr/bin/env bash
# Behavioral integration test — validates full project lifecycle
set -euo pipefail

HOSTING_PLATFORM="${HOSTING_PLATFORM:-github}"
TEMPLATE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMPDIR="$(mktemp -d)"

cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT INT TERM

# Git identity
export GIT_AUTHOR_NAME="Test User"
export GIT_COMMITTER_NAME="Test User"
export GIT_AUTHOR_EMAIL="test@example.com"
export GIT_COMMITTER_EMAIL="test@example.com"
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="init.defaultBranch"
export GIT_CONFIG_VALUE_0="main"

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1"; exit 1; }

echo "=== Phase 1: Generate + Install (platform: $HOSTING_PLATFORM) ==="

copier copy --trust --vcs-ref HEAD --defaults \
  -d "project_name=test-project" \
  -d "hosting_platform=$HOSTING_PLATFORM" \
  -d "hosting_org=test-org" \
  -d "project_description=Integration test" \
  "$TEMPLATE_DIR" "$TMPDIR/test-project"

cd "$TMPDIR/test-project"
git init -b main && git add . && nix flake update && git add flake.lock
nix develop -c just install
pass "Generate + Install"

echo "=== Phase 2: File structure ==="

for f in flake.nix flake.lock justfile prek.toml cog.toml \
         lib/nix/base.nix lib/nix/project.nix lib/just/base.just \
         .copier-answers.yaml .editorconfig .gitignore .envrc \
         LICENSE README.md CONTRIBUTING.md; do
  [ -f "$f" ] || fail "Missing: $f"
done
pass "Core files present"

if [ "$HOSTING_PLATFORM" = "github" ]; then
  for f in .github/workflows/pr-checks.yaml .github/workflows/renovate.yaml \
           .github/renovate.json .github/actions/nix-setup/action.yaml \
           .github/SECURITY.md; do
    [ -f "$f" ] || fail "Missing GitHub file: $f"
  done
  pass "GitHub files present"
fi

for f in copier.yaml template includes hack tests pytest.ini; do
  [ ! -e "$f" ] || fail "Template artifact leaked: $f"
done
pass "No template artifacts"

if [ "$HOSTING_PLATFORM" != "github" ]; then
  github_files=$(find .github -type f 2>/dev/null | head -1)
  [ -z "$github_files" ] || fail "GitHub files present for $HOSTING_PLATFORM"
  pass "No GitHub files for $HOSTING_PLATFORM"
fi

echo "=== Phase 3: Nix validation ==="

nix flake show >/dev/null 2>&1 || fail "nix flake show"
pass "nix flake show"
nix flake check --no-build 2>&1 || fail "nix flake check"
pass "nix flake check"

echo "=== Phase 4: DevShell packages ==="

nix develop -c cog --version >/dev/null 2>&1 || fail "cog not in devshell"
nix develop -c just --version >/dev/null 2>&1 || fail "just not in devshell"
nix develop -c prek --version >/dev/null 2>&1 || fail "prek not in devshell"
nix develop -c git --version >/dev/null 2>&1 || fail "git not in devshell"
pass "DevShell packages"

echo "=== Phase 5: Just recipes ==="

nix develop -c just --list >/dev/null 2>&1 || fail "just --list"
pass "just --list"
nix develop -c just test >/dev/null 2>&1 || fail "just test"
pass "just test"
nix develop -c just fmt >/dev/null 2>&1 || fail "just fmt"
git diff --exit-code >/dev/null 2>&1 || fail "just fmt changed files"
pass "just fmt (no changes)"
nix develop -c just clean >/dev/null 2>&1 || fail "just clean"
pass "just clean"

echo "=== Phase 6: Git hooks + history ==="

[ -f .git/hooks/pre-commit ] || fail "pre-commit hook missing"
[ -f .git/hooks/commit-msg ] || fail "commit-msg hook missing"
pass "Git hooks installed"
nix develop -c cog check >/dev/null 2>&1 || fail "cog check"
pass "Commit history valid"

echo ""
echo "=== ALL TESTS PASSED ($HOSTING_PLATFORM) ==="
