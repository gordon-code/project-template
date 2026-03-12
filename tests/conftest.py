"""Copier template test fixtures."""
import json
import os
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

# Flavor matrix
PLATFORMS = ["github", "gitlab", "other"]

# Git environment isolation
GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test Author",
    "GIT_COMMITTER_NAME": "Test Author",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_KEY_0": "init.defaultBranch",
    "GIT_CONFIG_VALUE_0": "main",
}

TEMPLATE_ROOT = Path(__file__).parent.parent


@pytest.fixture
def default_answers():
    """Default copier answers for test generation."""
    return {
        "project_name": "test-project",
        "hosting_platform": "github",
        "hosting_org": "test-org",
        "project_description": "A test project",
        "repo_url": "",
    }


@pytest.fixture
def generate(tmp_path, default_answers):
    """Generate a project from the template.

    Returns a callable that accepts **answers overrides and returns the output Path.
    """

    def _generate(**answers):
        merged = {**default_answers, **answers}
        project_name = merged.get("project_name", "test-project")

        # Create a temp copy of the template repo (copier needs a git repo)
        src = tmp_path / "template-copy"
        shutil.copytree(
            TEMPLATE_ROOT,
            src,
            ignore=shutil.ignore_patterns(
                ".git", "hack", "__pycache__", ".direnv", ".serena", ".pytest_cache"
            ),
        )

        # Git init the temp copy so copier sees it as a valid repo
        env = {**os.environ, **GIT_ENV}
        subprocess.run(
            ["git", "init", "-b", "main"], cwd=src, env=env, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "add", "."], cwd=src, env=env, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=src,
            env=env,
            check=True,
            capture_output=True,
        )

        # Output directory
        out = tmp_path / project_name
        out.mkdir(parents=True, exist_ok=True)

        # Build copier CLI args
        cmd = ["copier", "copy", "--trust", "--defaults"]
        for key, value in merged.items():
            cmd.extend(["-d", f"{key}={value}"])
        cmd.extend([str(src), str(out)])

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"copier copy failed (exit {result.returncode}):\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

        return out

    return _generate


@pytest.fixture(scope="session", params=PLATFORMS)
def generate_with_nix(tmp_path_factory, request):
    """Session-scoped: generate + nix flake update. READ-ONLY tests only."""
    platform = request.param
    tmp = tmp_path_factory.mktemp(f"nix-{platform}")

    src = tmp / "template-copy"
    shutil.copytree(
        TEMPLATE_ROOT,
        src,
        ignore=shutil.ignore_patterns(
            ".git", "hack", "__pycache__", ".direnv", ".serena", ".pytest_cache"
        ),
    )

    env = {**os.environ, **GIT_ENV}
    subprocess.run(["git", "init", "-b", "main"], cwd=src, env=env, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=src, env=env, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=src, env=env, check=True, capture_output=True)

    out = tmp / "test-project"
    out.mkdir(parents=True, exist_ok=True)

    cmd = [
        "copier", "copy", "--trust", "--defaults",
        "-d", "project_name=test-project",
        "-d", f"hosting_platform={platform}",
        "-d", "hosting_org=test-org",
        "-d", "project_description=A test project",
        "-d", "repo_url=",
        str(src), str(out),
    ]
    subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)

    # Git init + nix flake update in the generated project
    subprocess.run(["git", "init", "-b", "main"], cwd=out, env=env, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=out, env=env, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=out, env=env, check=True, capture_output=True)
    subprocess.run(["nix", "flake", "update"], cwd=out, check=True, capture_output=True, timeout=300)
    subprocess.run(["git", "add", "flake.lock"], cwd=out, env=env, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "lock"], cwd=out, env=env, check=True, capture_output=True)

    return out


@pytest.fixture
def generate_with_nix_mutable(tmp_path, default_answers):
    """Function-scoped: generate + nix flake update. For mutation tests."""

    def _generate(**answers):
        merged = {**default_answers, **answers}
        project_name = merged.get("project_name", "test-project")

        src = tmp_path / "template-copy"
        shutil.copytree(
            TEMPLATE_ROOT,
            src,
            ignore=shutil.ignore_patterns(
                ".git", "hack", "__pycache__", ".direnv", ".serena", ".pytest_cache"
            ),
        )

        env = {**os.environ, **GIT_ENV}
        subprocess.run(["git", "init", "-b", "main"], cwd=src, env=env, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=src, env=env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=src, env=env, check=True, capture_output=True)

        out = tmp_path / project_name
        out.mkdir(parents=True, exist_ok=True)

        cmd = ["copier", "copy", "--trust", "--defaults"]
        for key, value in merged.items():
            cmd.extend(["-d", f"{key}={value}"])
        cmd.extend([str(src), str(out)])

        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)

        # Git init + nix flake update
        subprocess.run(["git", "init", "-b", "main"], cwd=out, env=env, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=out, env=env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=out, env=env, check=True, capture_output=True)
        subprocess.run(["nix", "flake", "update"], cwd=out, check=True, capture_output=True, timeout=300)
        subprocess.run(["git", "add", "flake.lock"], cwd=out, env=env, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "lock"], cwd=out, env=env, check=True, capture_output=True)

        return out

    return _generate


# --- Helpers ---


def run_in_project(project_path, cmd, **kwargs):
    """Run a subprocess in the project directory."""
    env = {**os.environ, **GIT_ENV}
    return subprocess.run(
        cmd,
        cwd=project_path,
        env=env,
        capture_output=True,
        text=True,
        **kwargs,
    )


def check_file_contents(path, expected=(), unexpected=()):
    """Assert file exists and check string content."""
    assert path.exists(), f"File not found: {path}"
    content = path.read_text()
    for exp in expected:
        assert exp in content, f"Expected '{exp}' in {path.name}"
    for unexp in unexpected:
        assert unexp not in content, f"Unexpected '{unexp}' in {path.name}"


def assert_files_present(project, *relpaths):
    """Assert multiple files exist."""
    for relpath in relpaths:
        p = project / relpath
        assert p.exists(), f"Expected file not found: {relpath}"


def assert_files_absent(project, *relpaths):
    """Assert multiple files do NOT exist."""
    for relpath in relpaths:
        p = project / relpath
        assert not p.exists(), f"Unexpected file found: {relpath}"


def parse_toml(path):
    """Parse a TOML file."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def parse_yaml(path):
    """Parse a YAML file."""
    return yaml.safe_load(path.read_text())


def parse_json(path):
    """Parse a JSON file."""
    return json.loads(path.read_text())
