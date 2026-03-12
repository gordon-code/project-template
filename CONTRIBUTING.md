<!-- Managed by copier — changes may be overwritten by `copier update` -->
# Contributing

## Development environments

Development environments are defined in `flake.nix` and automatically activated when `direnv`
is installed and configured.

- Install [`nix`](https://determinate.systems/nix-installer/)
- Then use `nix develop -c $SHELL`, or use `direnv`:
  - Install [`direnv`](https://direnv.net/docs/installation.html)
  - [Setup](https://direnv.net/docs/hook.html) `direnv`
  - Install and setup [`nix-direnv`][nix-direnv]
  - Run `direnv allow`
- Finally, run `just hooks-install`

## Commits

Commits should follow the [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/) and
strive to be all lowercase with no trailing period. This is enforced by prek.

[Cocogitto][cog-commit] is installed by default and can help when
writing Conventional Commits using the `cog` command.

### Examples

```shell
cog commit feat "add awesome feature"
# Creates the commit: "feat: add awesome feature"
cog commit fix -B "fix a nasty bug" cli
# Creates a breaking commit: "fix(cli)!: fix a nasty bug"
```

## Releases

Release versions should follow the [SemVer specification](https://semver.org).

- Release _tags_ will be prefixed with `v`
- Release _versions_ should follow SemVer and _not_ be prefixed with `v`

Example: `git tag -a v1.2.3 -m "Release 1.2.3"`

[Cocogitto][cog-bump] can perform automatic, versioned releases
with the above conventions.

### Examples

```shell
cog bump --dry-run --auto
# Check the next calculated version
cog bump --auto
# Automatically bump the version to the next calculated version
cog bump --major
# Increment the MAJOR version value
```

## Updating from template

To pull in template updates:

    copier update --trust

## Dependency Updates

This project uses [Renovate](https://docs.renovatebot.com/) for automated dependency updates.
Set the `RENOVATE_TOKEN` repository secret to a GitHub PAT
with `repo` scope.

[nix-direnv]: https://github.com/nix-community/nix-direnv
[cog-commit]: https://docs.cocogitto.io/guide/commit.html
[cog-bump]: https://docs.cocogitto.io/guide/bump.html
