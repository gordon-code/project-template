# Managed by copier — changes may be overwritten by `copier update`
{
  lib,
  pkgs,
  config,
  ...
}:
let
  # TODO: Remove this override once nixpkgs updates prek past v0.3.2
  # prek.toml support was added in v0.3.2; nixpkgs-unstable is at v0.3.0
  # Track: https://github.com/NixOS/nixpkgs/blob/nixos-unstable/pkgs/by-name/pr/prek/package.nix
  prek =
    let
      version = "0.3.4";
      sources = {
        x86_64-linux = pkgs.fetchurl {
          url = "https://github.com/j178/prek/releases/download/v${version}/prek-x86_64-unknown-linux-gnu.tar.gz";
          hash = "sha256-qoY+dBMaw1SAqLVQ65+wkmI2tQSeXv1tPTbcVz16+zg=";
        };
        aarch64-linux = pkgs.fetchurl {
          url = "https://github.com/j178/prek/releases/download/v${version}/prek-aarch64-unknown-linux-gnu.tar.gz";
          hash = "sha256-WnoAAAI1xpAVY9qSH9jMZZfzLZVgdT+CsBD93q10EWY=";
        };
        x86_64-darwin = pkgs.fetchurl {
          url = "https://github.com/j178/prek/releases/download/v${version}/prek-x86_64-apple-darwin.tar.gz";
          hash = "sha256-YKjQkwErzUDo/sNIRQ112PWwnYVSnxH8XWBrhCc7eXg=";
        };
        aarch64-darwin = pkgs.fetchurl {
          url = "https://github.com/j178/prek/releases/download/v${version}/prek-aarch64-apple-darwin.tar.gz";
          hash = "sha256-8KQWE56vh1PetgOZMxQHejkWCZ0j3mcocIaiE0kVHvA=";
        };
      };
    in
    pkgs.stdenv.mkDerivation {
      pname = "prek";
      inherit version;
      src = sources.${pkgs.stdenv.hostPlatform.system};
      sourceRoot = ".";
      nativeBuildInputs = lib.optionals pkgs.stdenv.hostPlatform.isLinux [ pkgs.autoPatchelfHook ];
      buildInputs = lib.optionals pkgs.stdenv.hostPlatform.isLinux [ pkgs.stdenv.cc.cc.lib ];
      installPhase = ''
        install -Dm755 */prek $out/bin/prek
      '';
      meta = {
        description = "Better pre-commit, re-engineered in Rust";
        homepage = "https://github.com/j178/prek";
        license = lib.licenses.mit;
        platforms = builtins.attrNames sources;
      };
    };
in
{
  options = {
    devPkgs = lib.mkOption {
      type = lib.types.listOf lib.types.package;
      default = [ ];
      description = "List of packages to include in the dev shell.";
    };

    formatter = lib.mkOption {
      type = lib.types.package;
      default = pkgs.nixfmt-rfc-style;
      description = "Nix formatter package.";
    };

    shellHook = lib.mkOption {
      type = lib.types.lines;
      default = "";
      description = "Shell hook commands for dev shell.";
    };

    env = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      default = { };
      description = "Environment variables for dev shell.";
    };

    inputsFrom = lib.mkOption {
      type = lib.types.listOf lib.types.package;
      default = [ ];
      description = "Packages whose build inputs are added to dev shell.";
    };

    extraFlakeOutputs = lib.mkOption {
      type = lib.types.attrsOf lib.types.anything;
      default = { };
      description = "Additional flake outputs merged at top level.";
    };
  };

  config = {
    devPkgs = [
      pkgs.cocogitto
      pkgs.git
      pkgs.gnugrep
      pkgs.just
      prek
    ];
  };
}
