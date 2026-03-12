# Managed by copier — changes may be overwritten by `copier update`

# Show available recipes
default:
	@just --list

# Install project dependencies and hooks
install:
	#!/usr/bin/env bash
	set -euo pipefail
	[ -d .git ] || git init
	git add .
	if [ ! -f flake.lock ]; then
	  nix flake update && git add flake.lock
	fi
	# prek and cog are devshell tools — use nix develop
	nix develop -c prek install
	git add -u  # stage modifications only (not untracked files)
	# Commit if there are staged changes; skip gracefully if nothing to commit
	if ! git diff --cached --quiet 2>/dev/null; then
	  nix develop -c cog commit chore "initial commit, template applied" --scope copier
	fi

# Run all linters
lint:
	prek run --all-files

# Run tests
test:
	@echo "No tests configured"

# Run integration tests
test-integration:
	@echo "No integration tests configured"

# Remove build artifacts
clean:
	@echo "No clean targets configured"

# Format code
fmt:
	nix fmt

# Install git hooks
hooks-install:
	prek install

# Remove git hooks and cache
hooks-clean:
	prek uninstall
	prek cache clean
