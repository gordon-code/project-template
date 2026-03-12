"""Nix layer tests (require nix, session-scoped for performance)."""

from conftest import check_file_contents


def test_flake_exists(generate_with_nix):
    """Rendered flake.nix exists."""
    assert (generate_with_nix / "flake.nix").exists()


def test_flake_description(generate_with_nix):
    """Rendered flake.nix contains the project description."""
    check_file_contents(generate_with_nix / "flake.nix", expected=("A test project",))


def test_base_nix_exists(generate_with_nix):
    """lib/nix/base.nix exists in generated project."""
    assert (generate_with_nix / "lib" / "nix" / "base.nix").exists()
