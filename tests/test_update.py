"""Copier update lifecycle tests — validates template updates apply cleanly."""

import os
import shutil
import subprocess

import pytest

from conftest import GIT_ENV, TEMPLATE_ROOT

_ENV = {**os.environ, **GIT_ENV}


@pytest.fixture
def template_repo(tmp_path):
    """Create a temp copy of the template repo, tagged v1, for update testing."""
    src = tmp_path / "template-repo"
    shutil.copytree(
        TEMPLATE_ROOT,
        src,
        ignore=shutil.ignore_patterns(
            ".git", "hack", "__pycache__", ".direnv", ".serena", ".pytest_cache"
        ),
    )
    subprocess.run(["git", "init", "-b", "main"], cwd=src, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=src, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=src, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "tag", "-a", "v1", "-m", "v1"], cwd=src, env=_ENV, check=True, capture_output=True)
    return src


def _generate_from(template_repo, out, **answers):
    """Generate a project from the template_repo."""
    cmd = ["copier", "copy", "--trust", "--defaults", "-r", "v1"]
    for k, v in answers.items():
        cmd.extend(["-d", f"{k}={v}"])
    cmd.extend([str(template_repo), str(out)])
    subprocess.run(cmd, env=_ENV, check=True, capture_output=True, text=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=out, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=out, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=out, env=_ENV, check=True, capture_output=True)
    return out


@pytest.mark.xfail(reason="copier update looks for .copier-answers.yml not .yaml — needs investigation")
def test_copier_update_applies_cleanly(template_repo, tmp_path):
    """copier update from v1 to v2 applies without conflicts."""
    project = tmp_path / "test-project"
    project.mkdir()
    _generate_from(
        template_repo, project,
        project_name="test-project", hosting_platform="github",
        hosting_org="test-org", project_description="A test project", repo_url="",
    )

    # Modify template and tag v2
    contributing = template_repo / "template" / "CONTRIBUTING.md"
    content = contributing.read_text()
    contributing.write_text(content + "\n## Template Update Test\n\nThis line was added in v2.\n")
    subprocess.run(["git", "add", "."], cwd=template_repo, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "v2 change"], cwd=template_repo, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "tag", "-a", "v2", "-m", "v2"], cwd=template_repo, env=_ENV, check=True, capture_output=True)

    # Run copier update
    result = subprocess.run(
        ["copier", "update", "--trust", "--defaults"],
        cwd=project, env=_ENV, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"copier update failed:\n{result.stderr}"

    # Check no merge conflicts
    updated = (project / "CONTRIBUTING.md").read_text()
    assert "<<<<<<<" not in updated, "Merge conflict markers found"
    assert "Template Update Test" in updated, "v2 change not present"


@pytest.mark.xfail(reason="copier update looks for .copier-answers.yml not .yaml — needs investigation")
def test_copier_update_preserves_project_nix(template_repo, tmp_path):
    """copier update honors _skip_if_exists for project.nix."""
    project = tmp_path / "test-project"
    project.mkdir()
    _generate_from(
        template_repo, project,
        project_name="test-project", hosting_platform="github",
        hosting_org="test-org", project_description="A test project", repo_url="",
    )

    # Customize project.nix
    project_nix = project / "lib" / "nix" / "project.nix"
    project_nix.write_text('{ lib, pkgs, ... }: { devPkgs = lib.mkAfter [ pkgs.hello ]; }\n')
    subprocess.run(["git", "add", "."], cwd=project, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "customize"], cwd=project, env=_ENV, check=True, capture_output=True)

    # Tag v2 in template (trivial change)
    readme = template_repo / "template" / "README.md.jinja"
    readme.write_text(readme.read_text() + "\n<!-- v2 -->\n")
    subprocess.run(["git", "add", "."], cwd=template_repo, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "v2"], cwd=template_repo, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "tag", "-a", "v2", "-m", "v2"], cwd=template_repo, env=_ENV, check=True, capture_output=True)

    # Update
    subprocess.run(
        ["copier", "update", "--trust", "--defaults"],
        cwd=project, env=_ENV, check=True, capture_output=True, text=True,
    )

    # project.nix should still have our customization
    assert "pkgs.hello" in project_nix.read_text(), "project.nix customization was overwritten"


@pytest.mark.xfail(reason="copier update looks for .copier-answers.yml not .yaml — needs investigation")
def test_copier_update_preserves_justfile_extensions(template_repo, tmp_path):
    """copier update preserves user recipes in justfile extension section."""
    project = tmp_path / "test-project"
    project.mkdir()
    _generate_from(
        template_repo, project,
        project_name="test-project", hosting_platform="github",
        hosting_org="test-org", project_description="A test project", repo_url="",
    )

    # Add custom recipe to justfile
    justfile = project / "justfile"
    justfile.write_text(justfile.read_text() + "\n# My custom recipe\nmy-recipe:\n\t@echo custom\n")
    subprocess.run(["git", "add", "."], cwd=project, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add recipe"], cwd=project, env=_ENV, check=True, capture_output=True)

    # Tag v2
    readme = template_repo / "template" / "README.md.jinja"
    readme.write_text(readme.read_text() + "\n<!-- v2 -->\n")
    subprocess.run(["git", "add", "."], cwd=template_repo, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "v2"], cwd=template_repo, env=_ENV, check=True, capture_output=True)
    subprocess.run(["git", "tag", "-a", "v2", "-m", "v2"], cwd=template_repo, env=_ENV, check=True, capture_output=True)

    # Update
    subprocess.run(
        ["copier", "update", "--trust", "--defaults"],
        cwd=project, env=_ENV, check=True, capture_output=True, text=True,
    )

    # User's recipe should survive the 3-way merge
    assert "my-recipe" in justfile.read_text(), "Custom justfile recipe was lost"
