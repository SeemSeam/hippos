# npm Release Notes

This repository is being refactored to use `hippos` end to end. Any remaining
`hippocampus` internal names are migration-only details and should not be
treated as stable public API names.

## Package Identity

- npm package name: `hippos`.
- Python distribution name: `seemseam-hippos` (`seemseam_hippos` normalizes to
  the same PyPI project).
- Python import module target: `hippos`.
- CLI command exposed by both package managers: `hippos`.
- Versions in `package.json`, `pyproject.toml`, and
  `src/hippos/__init__.py` must stay synchronized once the package directory
  rename lands.

Migration-only legacy names:

- Python import module: `hippocampus`.
- Project output directory: `.hippocampus/`.
- Main index filename: `hippocampus-index.json`.

These may be readable for a few versions to migrate existing state, then should
be removed.

## Runtime Strategy

The npm `hippos` bin uses Node.js only as a launcher. On first run it:

1. finds Python 3.10+;
2. creates a user-cache virtual environment under
   `~/.cache/hippos/npm/<version>/venv`;
3. installs `seemseam-llmgateway>=0.1.2` and the matching Hippos Python
   distribution from PyPI with pip:
   `seemseam-hippos==<version>`;
4. executes the packaged Python CLI with the original CLI arguments.

The launcher executes `python -m hippos.cli`. The legacy `hippocampus.cli`
entrypoint remains only as a migration shim.

Environment overrides:

- `HIPPOS_NPM_PYTHON`: Python 3.10+ executable to use.
- `HIPPOS_NPM_CACHE_DIR`: cache root for the managed virtual environment.
- `HIPPOS_NPM_LLMGATEWAY_PIP_SPEC`: Python `llmgateway` requirement spec for
  the managed virtual environment.
- `HIPPOS_NPM_PIP_SPEC`: alternate pip requirement spec for smoke tests or
  emergency repoints.

The npm package does not install the Node `@seemseam/llmgateway` package. The
Python runtime installs `seemseam-llmgateway>=0.1.2` from PyPI inside the
managed virtual environment. The Python import module remains `llmgateway`.

## Publication Preconditions

- npm publication is deferred until after the PyPI package is stable.
- `hippos` is currently unclaimed on npm based on local registry checks, but
  re-check immediately before publishing.
- Do not publish until `package.json`, `pyproject.toml`, and the active Python
  package `__init__.py` carry the same version.
- Run `npm pack --dry-run` and inspect the included files before publishing.
- Do not publish from a dirty or unreviewed release state.
