# Template repo project.nix — adds test dependencies to devshell
{
  pkgs,
  lib,
  flakeInputs,
  ...
}:
{
  devPkgs = lib.mkAfter [
    pkgs.python3Packages.pytest
    pkgs.python3Packages.pyyaml
    flakeInputs.copier-flake.packages.${pkgs.system}.copier
  ];
}
