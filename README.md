# project-template

Swiss-army project template managed by Copier

## Getting Started

### From template

```shell
copier copy --trust https://github.com/gordon-code/project-template.git my-project
cd my-project
nix run nixpkgs#just -- install
```

### With direnv

```shell
direnv allow
```

## Development

| Recipe | Description |
|--------|-------------|
| `just install` | Install dependencies and git hooks |
| `just lint` | Run all linters |
| `just test` | Run tests |
| `just fmt` | Format code |
| `just clean` | Remove build artifacts |

<!-- ~~~ Add project-specific content below this line ~~~ -->
