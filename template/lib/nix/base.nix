# Managed by copier — changes may be overwritten by `copier update`
{
  lib,
  pkgs,
  config,
  ...
}:
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
      pkgs.prek
    ];
  };
}
