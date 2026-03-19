# Managed by copier — baseline imported from lib/just/base.just
set allow-duplicate-recipes

import 'lib/just/base.just'

# ~~~ Add project-specific recipes below this line ~~~

# Regenerate root files from template
render:
	#!/usr/bin/env bash
	set -euo pipefail
	# Delete generated root files (preserve non-template dirs)
	find . -maxdepth 1 \
		! -name '.' ! -name '.git' ! -name '.venv' ! -name '.direnv' \
		! -name '.serena' \
		! -name 'template' ! -name 'includes' ! -name 'copier.yaml' \
		! -name 'hack' ! -name 'tests' ! -name 'pytest.ini' \
		! -name 'flake.lock' ! -name 'CHANGELOG.md' \
		-exec rm -rf {} +
	# Regenerate from template
	copier copy --vcs-ref=HEAD --trust --defaults \
		--data-file includes/copier-answers-sample.yml -f . .
	# Restore repo-specific files (copier copy overwrites extension sections)
	git show HEAD:lib/nix/project.nix > lib/nix/project.nix 2>/dev/null || true
	git show HEAD:justfile > justfile 2>/dev/null || true
	git show HEAD:.gitignore > .gitignore 2>/dev/null || true
	git show HEAD:.github/workflows/render-template.yaml > .github/workflows/render-template.yaml 2>/dev/null || true

# Run unit tests
test:
	pytest

# Run integration tests
test-integration:
	bash tests/test_project.sh
