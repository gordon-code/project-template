# project-template

Swiss-army project template managed by Copier

## Getting Started

### From template

```shell
copier copy --trust https://github.com/gordon-code/project-template.git my-project
cd my-project
nix run nixpkgs#just -- install
```

### Development

```shell
direnv allow
# or: nix develop -c $SHELL
```

## Recipes

| Recipe | Description |
|--------|-------------|
| `just install` | Install dependencies and git hooks |
| `just update` | Pull in template updates |
| `just lint` | Run all linters |
| `just test` | Run tests |
| `just fmt` | Format code |
| `just clean` | Remove build artifacts |

<!-- ~~~ Add project-specific content below this line ~~~ -->
