"""Nix layer tests (require nix, session-scoped for performance)."""

import pytest

from conftest import check_file_contents, run_in_project


def test_flake_exists(generate_with_nix):
    """Rendered flake.nix exists."""
    assert (generate_with_nix / "flake.nix").exists()


def test_flake_description(generate_with_nix):
    """Rendered flake.nix contains the project description."""
    check_file_contents(generate_with_nix / "flake.nix", expected=("A test project",))


def test_base_nix_exists(generate_with_nix):
    """lib/nix/base.nix exists in generated project."""
    assert (generate_with_nix / "lib" / "nix" / "base.nix").exists()


def test_flake_check(generate_with_nix):
    """nix flake check validates the rendered flake structure."""
    result = run_in_project(generate_with_nix, ["nix", "flake", "check", "--no-build"], check=False)
    assert result.returncode == 0, f"nix flake check failed:\n{result.stderr}"


def test_flake_show(generate_with_nix):
    """nix flake show outputs devShells and formatter."""
    result = run_in_project(generate_with_nix, ["nix", "flake", "show"], check=False)
    assert result.returncode == 0, f"nix flake show failed:\n{result.stderr}"
    assert "devShells" in result.stdout
    assert "formatter" in result.stdout


def test_nix_fmt_clean(generate_with_nix):
    """Generated Nix code passes nixfmt formatting check."""
    result = run_in_project(
        generate_with_nix, ["nix", "fmt", "--", "--check", "."], check=False
    )
    assert result.returncode == 0, f"nix fmt check failed:\n{result.stderr}"


def test_justfile_valid(generate_with_nix):
    """just --list succeeds and shows expected recipes."""
    result = run_in_project(
        generate_with_nix, ["nix", "develop", "-c", "just", "--list"], check=False
    )
    assert result.returncode == 0, f"just --list failed:\n{result.stderr}"
    for recipe in ("install", "lint", "test", "fmt", "clean", "hooks-install"):
        assert recipe in result.stdout, f"Recipe '{recipe}' missing from just --list"


def test_justfile_recipes_runnable(generate_with_nix):
    """just test runs without error (no-op stub)."""
    result = run_in_project(
        generate_with_nix, ["nix", "develop", "-c", "just", "test"], check=False
    )
    assert result.returncode == 0, f"just test failed:\n{result.stderr}"


def test_just_install(generate_with_nix_mutable):
    """just install bootstraps a generated project end-to-end."""
    project = generate_with_nix_mutable()
    result = run_in_project(
        project, ["nix", "develop", "-c", "just", "install"], check=False
    )
    assert result.returncode == 0, f"just install failed:\n{result.stderr}\n{result.stdout}"
    assert (project / "flake.lock").exists()
    assert (project / ".git" / "hooks" / "pre-commit").exists()


@pytest.mark.xfail(reason="pr-checks.yaml trailing newline + base.just indent + no-commit-to-branch on main")
def test_prek_lint_clean(generate_with_nix_mutable):
    """Generated project passes its own lint checks."""
    project = generate_with_nix_mutable()
    # Install hooks first so prek config is set up
    run_in_project(project, ["nix", "develop", "-c", "prek", "install"], check=False)
    result = run_in_project(
        project, ["nix", "develop", "-c", "just", "lint"], check=False
    )
    assert result.returncode == 0, f"just lint failed:\n{result.stderr}\n{result.stdout}"


@pytest.mark.xfail(reason="fixture commits use non-conventional messages ('init', 'lock')")
def test_cog_verify(generate_with_nix_mutable):
    """cog verify passes on the initial commit."""
    project = generate_with_nix_mutable()
    result = run_in_project(
        project, ["nix", "develop", "-c", "cog", "check"], check=False
    )
    assert result.returncode == 0, f"cog check failed:\n{result.stderr}\n{result.stdout}"


def test_project_nix_extension(generate_with_nix_mutable):
    """Tier 3 project.nix can extend base.nix devPkgs via lib.mkAfter."""
    project = generate_with_nix_mutable()

    # Write a custom project.nix that adds pkgs.hello
    project_nix = project / "lib" / "nix" / "project.nix"
    project_nix.write_text(
        '{ lib, pkgs, ... }: { devPkgs = lib.mkAfter [ pkgs.hello ]; }\n'
    )

    # Verify hello is available in the devshell
    result = run_in_project(project, ["nix", "develop", "-c", "hello"], check=False)
    assert result.returncode == 0, f"nix develop -c hello failed:\n{result.stderr}"
    assert "Hello, world!" in result.stdout
