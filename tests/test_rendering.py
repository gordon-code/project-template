"""Smoke tests for template rendering."""

import pytest

from conftest import (
    assert_files_absent,
    assert_files_present,
    check_file_contents,
    parse_json,
    parse_toml,
    parse_yaml,
)


# --- Core rendering (session-scoped, all platforms) ---


def test_renders_without_error(generated_project):
    """Template renders without error for all platforms."""
    assert generated_project.exists()
    assert any(generated_project.iterdir()), "Output directory is empty"


def test_readme_content(generated_project):
    """README.md contains project name and description."""
    readme = generated_project / "README.md"
    assert readme.exists()
    content = readme.read_text()
    assert "test-project" in content
    assert "A test project" in content


# --- URL derivation (needs custom answers, uses generate) ---


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
    """Copier answers reflect expected values for different repo URLs."""
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


# --- Default project structure (session-scoped github) ---


def test_default_project_structure(generate):
    """Default github project has all expected files."""
    project = generate()
    assert_files_present(
        project,
        "flake.nix",
        "lib/nix/base.nix",
        "lib/nix/project.nix",
        "lib/just/base.just",
        ".envrc",
        "justfile",
        "prek.toml",
        "cog.toml",
        ".editorconfig",
        ".gitignore",
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        ".copier-answers.yaml",
        ".idea/modules.xml",
        ".idea/test-project.iml",
    )
    assert_files_absent(
        project, "copier.yaml", "template", "includes", "hack", "tests", "pytest.ini"
    )


def test_justfile_imports_base(generate):
    """justfile imports lib/just/base.just."""
    project = generate()
    assert "import 'lib/just/base.just'" in (project / "justfile").read_text()


def test_envrc_content(generate):
    """`.envrc` contains `use flake`."""
    project = generate()
    assert "use flake" in (project / ".envrc").read_text()


def test_copier_answers_valid_yaml(generate):
    """.copier-answers.yaml is valid YAML with expected keys."""
    project = generate()
    answers = parse_yaml(project / ".copier-answers.yaml")
    assert "project_name" in answers
    assert "hosting_platform" in answers


# --- Platform-conditional rendering ---


def test_prek_valid_toml(generated_project):
    """prek.toml renders as valid TOML for all platforms."""
    parse_toml(generated_project / "prek.toml")


def test_cog_valid_toml(generated_project):
    """cog.toml renders as valid TOML for all platforms."""
    parse_toml(generated_project / "cog.toml")


def test_cog_branch(generate):
    """cog.toml branch_whitelist contains main."""
    project = generate()
    data = parse_toml(project / "cog.toml")
    assert "main" in data["branch_whitelist"]


def test_prek_github_hooks(generate):
    """GitHub platform includes actionlint hook."""
    project = generate(hosting_platform="github")
    assert "actionlint" in (project / "prek.toml").read_text()


@pytest.mark.parametrize("hosting_platform", ["gitlab", "other"])
def test_prek_no_github_hooks(generate, hosting_platform):
    """Non-GitHub platforms do not include actionlint hook."""
    project = generate(hosting_platform=hosting_platform)
    assert "actionlint" not in (project / "prek.toml").read_text()


def test_editorconfig_content(generate):
    """.editorconfig has expected settings."""
    project = generate()
    content = (project / ".editorconfig").read_text()
    assert "root = true" in content
    assert "end_of_line = lf" in content
    assert "indent_style = tab" in content


def test_gitignore_content(generate):
    """.gitignore has expected entries."""
    project = generate()
    content = (project / ".gitignore").read_text()
    assert ".direnv/" in content
    assert "result/" in content


def test_readme_sections(generated_project):
    """README has Getting Started and Development sections."""
    content = (generated_project / "README.md").read_text()
    assert "Getting Started" in content
    assert "Development" in content


def test_license_content(generate):
    """LICENSE has MIT license with hosting_org."""
    project = generate()
    content = (project / "LICENSE").read_text()
    assert "test-org" in content
    assert "MIT License" in content


def test_contributing_content(generate):
    """CONTRIBUTING.md references Conventional Commits."""
    project = generate()
    assert "Conventional Commits" in (project / "CONTRIBUTING.md").read_text()


# --- GitHub integration ---


def test_nix_setup_action(generate):
    """GitHub projects have SHA-pinned nix-setup composite action."""
    project = generate(hosting_platform="github")
    action = project / ".github" / "actions" / "nix-setup" / "action.yaml"
    assert action.exists()
    content = action.read_text()
    assert "composite" in content
    assert "nix-installer-action@" in content


@pytest.mark.parametrize("hosting_platform", ["gitlab", "other"])
def test_github_files_absent(generate, hosting_platform):
    """Non-GitHub platforms have no .github/ files."""
    project = generate(hosting_platform=hosting_platform)
    github_dir = project / ".github"
    files = list(github_dir.rglob("*")) if github_dir.exists() else []
    assert not files, f"Unexpected .github/ files for {hosting_platform}: {files}"


def test_pr_checks_valid_yaml(generate):
    """pr-checks.yaml is valid YAML with expected structure."""
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


def test_pr_checks_pinned_actions(generate):
    """All uses: refs in pr-checks are SHA-pinned."""
    project = generate(hosting_platform="github")
    content = (project / ".github" / "workflows" / "pr-checks.yaml").read_text()
    for line in content.splitlines():
        if "uses:" in line and "@" in line:
            ref = line.split("@")[1].split()[0]
            assert len(ref) >= 40 or ref.startswith("./"), f"Unpinned action: {line.strip()}"


def test_renovate_config_valid_json(generate):
    """renovate.json is valid JSON with expected keys."""
    project = generate(hosting_platform="github")
    data = parse_json(project / ".github" / "renovate.json")
    assert "extends" in data
    assert "customManagers" in data


def test_renovate_no_template_config(generate):
    """Default projects don't have template-specific Renovate managers."""
    project = generate(hosting_platform="github")
    content = (project / ".github" / "renovate.json").read_text()
    assert "postUpgradeTasks" not in content
    assert "template/" not in content


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


# --- _is_template conditional ---


def test_renovate_has_template_config(generate):
    """Template repo (_is_template=True) has template-specific managers."""
    project = generate(hosting_platform="github", _is_template=True)
    data = parse_json(project / ".github" / "renovate.json")
    managers = data.get("customManagers", [])
    template_managers = [m for m in managers if any("template/" in f for f in m.get("fileMatch", []))]
    assert template_managers, "No template-specific customManagers found"


def test_no_consistency_job_default(generate):
    """Default projects have no consistency job in pr-checks."""
    project = generate(hosting_platform="github")
    assert "consistency" not in (project / ".github" / "workflows" / "pr-checks.yaml").read_text()


def test_has_consistency_job_template(generate):
    """Template repo (_is_template=True) has consistency job."""
    project = generate(hosting_platform="github", _is_template=True)
    assert "consistency" in (project / ".github" / "workflows" / "pr-checks.yaml").read_text()


def test_idea_xml_valid(generate):
    """JetBrains modules.xml is valid XML."""
    import xml.etree.ElementTree as ET
    project = generate()
    ET.parse(project / ".idea" / "modules.xml")
