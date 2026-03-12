{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    copier-flake.url = "github:gordon-code/copier-flake";
  };

  outputs =
    {
      nixpkgs,
      copier-flake,
      ...
    }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forEachSupportedSystem =
        f:
        nixpkgs.lib.genAttrs supportedSystems (
          system:
          f {
            inherit system;
            pkgs = nixpkgs.legacyPackages.${system};
          }
        );
    in
    {
      devShells = forEachSupportedSystem (
        { pkgs, system, ... }:
        {
          default = pkgs.mkShell {
            packages = [
              (pkgs.python3.withPackages (ps: [
                ps.pytest
                ps.pyyaml
              ]))
              copier-flake.packages.${system}.copier
            ];
          };
        }
      );
    };
}
