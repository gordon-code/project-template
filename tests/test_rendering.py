"""Smoke tests for template rendering."""

import pytest

from conftest import PLATFORMS, check_file_contents, parse_toml, parse_yaml


@pytest.mark.parametrize("hosting_platform", PLATFORMS)
def test_renders_without_error(generate, hosting_platform):
    """Template renders without error for all platforms."""
    project = generate(hosting_platform=hosting_platform)
    assert project.exists()
    assert any(project.iterdir()), "Output directory is empty"


@pytest.mark.parametrize("hosting_platform", PLATFORMS)
def test_readme_content(generate, hosting_platform):
    """README.md contains project name and description."""
    project = generate(hosting_platform=hosting_platform)
    readme = project / "README.md"
    assert readme.exists()
    content = readme.read_text()
    assert "test-project" in content
    assert "A test project" in content


@pytest.mark.parametrize(
    "repo_url,expected_platform,expected_org,expected_name",
    [
        (
            "https://github.com/myorg/myproject.git",
            "github",
            "myorg",
            "myproject",
        ),
        (
            "git@gitlab.com:mygroup/myrepo.git",
            "gitlab",
            "mygroup",
            "myrepo",
        ),
    ],
)
def test_repo_url_derivation(
    generate, repo_url, expected_platform, expected_org, expected_name
):
    """Copier regex derivation correctly parses repo URLs."""
    project = generate(
        repo_url=repo_url,
        project_name=expected_name,
        hosting_platform=expected_platform,
        hosting_org=expected_org,
    )
    answers = parse_yaml(project / ".copier-answers.yaml")
    assert answers["project_name"] == expected_name
    assert answers["hosting_platform"] == expected_platform
    assert answers["hosting_org"] == expected_org


def test_flake_exists(generate):
    """flake.nix is rendered from template."""
    project = generate()
    assert (project / "flake.nix").exists()


def test_base_nix_exists(generate):
    """lib/nix/base.nix is rendered from template."""
    project = generate()
    assert (project / "lib" / "nix" / "base.nix").exists()


def test_project_nix_exists(generate):
    """lib/nix/project.nix stub is rendered from template."""
    project = generate()
    assert (project / "lib" / "nix" / "project.nix").exists()


def test_envrc_exists(generate):
    """.envrc is rendered from template."""
    project = generate()
    envrc = project / ".envrc"
    assert envrc.exists()
    assert "use flake" in envrc.read_text()


def test_empty_url_uses_explicit(generate):
    """Empty repo_url falls back to explicitly provided values."""
    project = generate(
        repo_url="",
        project_name="explicit-name",
        hosting_platform="github",
        hosting_org="explicit-org",
    )
    answers = parse_yaml(project / ".copier-answers.yaml")
    assert answers["project_name"] == "explicit-name"
    assert answers["hosting_platform"] == "github"
    assert answers["hosting_org"] == "explicit-org"


# --- Phase 3: Developer Experience ---


def test_justfile_exists(generate):
    """justfile and base.just exist."""
    project = generate()
    assert (project / "justfile").exists()
    assert (project / "lib" / "just" / "base.just").exists()


def test_justfile_imports_base(generate):
    """justfile imports lib/just/base.just."""
    project = generate()
    content = (project / "justfile").read_text()
    assert "import 'lib/just/base.just'" in content


@pytest.mark.parametrize("hosting_platform", PLATFORMS)
def test_prek_valid_toml(generate, hosting_platform):
    """prek.toml renders as valid TOML for all platforms."""
    project = generate(hosting_platform=hosting_platform)
    parse_toml(project / "prek.toml")


def test_prek_github_hooks(generate):
    """GitHub platform includes actionlint hook."""
    project = generate(hosting_platform="github")
    content = (project / "prek.toml").read_text()
    assert "actionlint" in content


@pytest.mark.parametrize("hosting_platform", ["gitlab", "other"])
def test_prek_no_github_hooks(generate, hosting_platform):
    """Non-GitHub platforms do not include actionlint hook."""
    project = generate(hosting_platform=hosting_platform)
    content = (project / "prek.toml").read_text()
    assert "actionlint" not in content


@pytest.mark.parametrize("hosting_platform", PLATFORMS)
def test_cog_valid_toml(generate, hosting_platform):
    """cog.toml renders as valid TOML for all platforms."""
    project = generate(hosting_platform=hosting_platform)
    parse_toml(project / "cog.toml")


def test_cog_branch(generate):
    """cog.toml branch_whitelist contains main."""
    project = generate()
    data = parse_toml(project / "cog.toml")
    assert "main" in data["branch_whitelist"]


def test_editorconfig_exists(generate):
    """.editorconfig exists with expected content."""
    project = generate()
    content = (project / ".editorconfig").read_text()
    assert "root = true" in content
    assert "end_of_line = lf" in content
    assert "indent_style = tab" in content  # justfile override


def test_gitignore_exists(generate):
    """.gitignore exists with expected content."""
    project = generate()
    content = (project / ".gitignore").read_text()
    assert ".direnv/" in content
    assert "result/" in content
