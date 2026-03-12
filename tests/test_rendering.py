"""Smoke tests for template rendering."""

import pytest

from conftest import (
    PLATFORMS,
    assert_files_absent,
    assert_files_present,
    check_file_contents,
    parse_json,
    parse_toml,
    parse_yaml,
)


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


# --- Phase 4: GitHub Integration ---


def test_nix_setup_action(generate):
    """GitHub projects have nix-setup composite action."""
    project = generate(hosting_platform="github")
    action = project / ".github" / "actions" / "nix-setup" / "action.yaml"
    assert action.exists()
    content = action.read_text()
    assert "composite" in content


def test_nix_setup_pinned(generate):
    """Actions in nix-setup are SHA-pinned."""
    project = generate(hosting_platform="github")
    content = (project / ".github" / "actions" / "nix-setup" / "action.yaml").read_text()
    assert "@" in content
    assert "nix-installer-action@" in content


@pytest.mark.parametrize("hosting_platform", ["gitlab", "other"])
def test_github_files_absent(generate, hosting_platform):
    """Non-GitHub platforms have no .github/ files."""
    project = generate(hosting_platform=hosting_platform)
    github_dir = project / ".github"
    if github_dir.exists():
        assert not any(github_dir.rglob("*")), "Unexpected files in .github/"


def test_no_template_artifacts(generate):
    """Generated projects don't contain template artifacts."""
    project = generate()
    assert_files_absent(project, "copier.yaml", "template", "includes", "hack", "tests", "pytest.ini")


def test_pr_checks_valid_yaml(generate):
    """pr-checks.yaml is valid YAML for GitHub."""
    project = generate(hosting_platform="github")
    data = parse_yaml(project / ".github" / "workflows" / "pr-checks.yaml")
    assert "jobs" in data
    assert "checks" in data["jobs"]


def test_pr_checks_has_steps(generate):
    """pr-checks has lint, test, and integration test steps."""
    project = generate(hosting_platform="github")
    content = (project / ".github" / "workflows" / "pr-checks.yaml").read_text()
    assert "just lint" in content
    assert "just test" in content
    assert "just test-integration" in content


def test_renovate_config_valid_json(generate):
    """renovate.json is valid JSON for GitHub."""
    project = generate(hosting_platform="github")
    data = parse_json(project / ".github" / "renovate.json")
    assert "extends" in data
    assert "customManagers" in data


def test_renovate_no_template_config(generate):
    """Default projects don't have template-specific Renovate config."""
    project = generate(hosting_platform="github")
    content = (project / ".github" / "renovate.json").read_text()
    assert "postUpgradeTasks" not in content


def test_security_md(generate):
    """GitHub projects have SECURITY.md with project name."""
    project = generate(hosting_platform="github")
    security = project / ".github" / "SECURITY.md"
    assert security.exists()
    check_file_contents(security, expected=("test-project",))


@pytest.mark.parametrize("hosting_platform", ["gitlab", "other"])
def test_security_md_absent(generate, hosting_platform):
    """Non-GitHub platforms don't have SECURITY.md."""
    project = generate(hosting_platform=hosting_platform)
    assert_files_absent(project, ".github/SECURITY.md")


# --- Phase 5: Documentation & Answers ---


def test_license_exists(generate):
    """LICENSE exists with year and hosting_org."""
    project = generate()
    license_file = project / "LICENSE"
    assert license_file.exists()
    content = license_file.read_text()
    assert "test-org" in content
    assert "MIT License" in content


def test_contributing_exists(generate):
    """CONTRIBUTING.md exists with Conventional Commits reference."""
    project = generate()
    contributing = project / "CONTRIBUTING.md"
    assert contributing.exists()
    assert "Conventional Commits" in contributing.read_text()


@pytest.mark.parametrize("hosting_platform", PLATFORMS)
def test_readme_sections(generate, hosting_platform):
    """README has Getting Started and Development sections."""
    project = generate(hosting_platform=hosting_platform)
    content = (project / "README.md").read_text()
    assert "Getting Started" in content
    assert "Development" in content


def test_copier_answers_valid_yaml(generate):
    """.copier-answers.yaml is valid YAML with expected keys."""
    project = generate()
    answers = parse_yaml(project / ".copier-answers.yaml")
    assert "project_name" in answers
    assert "hosting_platform" in answers


def test_idea_files(generate):
    """JetBrains .idea files are rendered."""
    project = generate()
    assert (project / ".idea" / "modules.xml").exists()
    assert (project / ".idea" / "test-project.iml").exists()


# --- Phase 7: Renovate Integration ---


def test_renovate_no_template_config_default(generate):
    """Default projects have no template-specific Renovate managers."""
    project = generate(hosting_platform="github")
    content = (project / ".github" / "renovate.json").read_text()
    assert "template/" not in content


def test_renovate_has_template_config(generate):
    """Template repo (_is_template=True) has template-specific managers."""
    project = generate(hosting_platform="github", _is_template=True)
    content = (project / ".github" / "renovate.json").read_text()
    assert "template/" in content


def test_no_consistency_job_default(generate):
    """Default projects have no consistency job in pr-checks."""
    project = generate(hosting_platform="github")
    content = (project / ".github" / "workflows" / "pr-checks.yaml").read_text()
    assert "consistency" not in content


def test_has_consistency_job_template(generate):
    """Template repo (_is_template=True) has consistency job."""
    project = generate(hosting_platform="github", _is_template=True)
    content = (project / ".github" / "workflows" / "pr-checks.yaml").read_text()
    assert "consistency" in content
