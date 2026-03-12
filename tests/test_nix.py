"""Nix layer tests (require nix, session-scoped for performance)."""

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
