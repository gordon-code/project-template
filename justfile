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
	  ! -name 'flake.lock' \
	  -exec rm -rf {} +
	# Regenerate from template
	copier copy -r HEAD --trust --defaults \
	  --data-file includes/copier-answers-sample.yml -f . .
	# Restore project.nix (copier copy doesn't honor _skip_if_exists)
	git checkout -- lib/nix/project.nix 2>/dev/null || true

# Run unit tests
test:
	pytest

# Run integration tests
test-integration:
	bash tests/test_project.sh
