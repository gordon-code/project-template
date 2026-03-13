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
	# Commit template files before installing hooks (hooks block main-branch commits)
	if ! git diff --cached --quiet 2>/dev/null; then
		nix develop -c cog commit chore "initial commit, template applied" copier
	fi
	# Install hooks after the initial commit
	nix develop -c prek install

# Update from upstream template
update:
	copier update --trust --answers-file .copier-answers.yaml

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
	nix fmt -- .

# Install git hooks
hooks-install:
	prek install

# Remove git hooks and cache
hooks-clean:
	prek uninstall
	prek cache clean
