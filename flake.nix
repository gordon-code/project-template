# Managed by copier — changes may be overwritten by `copier update`
{
  description = "Swiss-army project template managed by Copier";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    copier-flake.url = "github:gordon-code/copier-flake";
  };

  outputs =
    inputs@{
      nixpkgs,
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
    let
      cfgFor =
        pkgs:
        (nixpkgs.lib.evalModules {
          specialArgs = {
            inherit pkgs;
            inherit (nixpkgs) lib;
            flakeInputs = inputs;
          };
          modules =
            let
              dir = builtins.readDir ./lib/nix;
              nixFiles = builtins.filter (n: builtins.match ".*\\.nix" n != null) (builtins.attrNames dir);
            in
            map (f: ./lib/nix + "/${f}") nixFiles;
        }).config;
    in
    {
      devShells = forEachSupportedSystem (
        { pkgs, ... }:
        let
          cfg = cfgFor pkgs;
        in
        {
          default = pkgs.mkShell {
            packages = cfg.devPkgs;
            inherit (cfg) shellHook env inputsFrom;
          };
        }
      );

      formatter = forEachSupportedSystem ({ pkgs, ... }: (cfgFor pkgs).formatter);
    }
    // (cfgFor nixpkgs.legacyPackages.${builtins.head supportedSystems}).extraFlakeOutputs;
}
