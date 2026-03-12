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


def _get_env():
    """Build environment with git isolation vars."""
    env = os.environ.copy()
    env.update(GIT_ENV)
    return env


def _prepare_template_source(dest):
    """Copy template repo to dest and git-init it (copier needs a git repo source)."""
    shutil.copytree(
        TEMPLATE_ROOT,
        dest,
        ignore=shutil.ignore_patterns(
            ".git", "hack", "__pycache__", ".direnv", ".serena", ".pytest_cache"
        ),
    )
    env = _get_env()
    subprocess.run(["git", "init", "-b", "main"], cwd=dest, env=env, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=dest, env=env, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=dest, env=env, check=True, capture_output=True)
    return dest


def _run_copier(src, out, answers):
    """Run copier copy with the given answers."""
    env = _get_env()
    cmd = ["copier", "copy", "--trust", "--defaults"]
    for key, value in answers.items():
        cmd.extend(["-d", f"{key}={value}"])
    cmd.extend([str(src), str(out)])
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"copier copy failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return out


@pytest.fixture(scope="session")
def template_src(tmp_path_factory):
    """Session-scoped: prepared template source (copy + git init). Shared by all tests."""
    src = tmp_path_factory.mktemp("template") / "src"
    return _prepare_template_source(src)


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
def generate(tmp_path, template_src, default_answers):
    """Generate a project from the template.

    Returns a callable that accepts **answers overrides and returns the output Path.
    Uses session-scoped template_src to avoid re-copying the template on every test.
    """

    def _generate(**answers):
        merged = {**default_answers, **answers}
        project_name = merged.get("project_name", "test-project")
        out = tmp_path / project_name
        out.mkdir(parents=True, exist_ok=True)
        return _run_copier(template_src, out, merged)

    return _generate


@pytest.fixture(scope="session", params=PLATFORMS)
def generate_with_nix(tmp_path_factory, template_src, request):
    """Session-scoped: generate + nix flake update. READ-ONLY tests only."""
    platform = request.param
    base_tmp = tmp_path_factory.mktemp(f"nix-{platform}")

    answers = {
        "project_name": "test-project",
        "hosting_platform": platform,
        "hosting_org": "test-org",
        "project_description": "A test project",
        "repo_url": "",
    }

    out = base_tmp / "test-project"
    out.mkdir(parents=True, exist_ok=True)
    _run_copier(template_src, out, answers)

    # Git init + nix flake update in the generated project
    env = _get_env()
    subprocess.run(["git", "init", "-b", "main"], cwd=out, env=env, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=out, env=env, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=out, env=env, check=True, capture_output=True)
    subprocess.run(["nix", "flake", "update"], cwd=out, check=True, capture_output=True, timeout=300)
    subprocess.run(["git", "add", "flake.lock"], cwd=out, env=env, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "lock"], cwd=out, env=env, check=True, capture_output=True)

    return out


@pytest.fixture
def generate_with_nix_mutable(tmp_path, template_src, default_answers):
    """Function-scoped: generate + nix flake update. For mutation tests."""

    def _generate(**answers):
        merged = {**default_answers, **answers}
        project_name = merged.get("project_name", "test-project")
        out = tmp_path / project_name
        out.mkdir(parents=True, exist_ok=True)
        _run_copier(template_src, out, merged)

        env = _get_env()
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
    return subprocess.run(
        cmd,
        cwd=project_path,
        env=_get_env(),
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
