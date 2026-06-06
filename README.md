# Hippos

[中文文档](README.zh-CN.md)

Hippos is a code repository indexing, navigation, and structure-analysis
toolkit. It turns a repository into LLM-friendly artifacts: source signatures,
repository trees, a unified code index, structure prompts, navigation snippets,
snapshots, diffs, statistics, and an interactive HTML visualization.

The public identity is `hippos` end to end. Any remaining `hippocampus` names
in early refactor builds are migration-only details, not stable API names for
new integrations.

## Features

- Repository code maps for fast human and LLM onboarding.
- Source signature extraction across supported languages through tree-sitter.
- Unified Hippos index with files, modules, tags, and dependency-oriented
  summaries.
- Structure prompt rendering in `map`, `deep`, or automatic profiles.
- Incremental refresh that reuses caches and updates only changed work where
  possible.
- Search, expand, overview, stats, snapshot, and diff commands for codebase
  navigation.
- Interactive HTML visualization generated from the Hippos index.
- Optional RepoMap-backed ranking and trimming for context selection.
- Optional architecture metrics and review workflows when paired with
  `architec`.
- MCP navigation tools, including `hippos.navigate`, for agent integrations.

## Requirements

- Python 3.10 or newer.
- Git only for source installs.
- Node.js 18 or newer only when using the npm launcher.
- LLM provider configuration for commands that run the full index pipeline.

## Naming and Migration

The full refactor target is:

- Python distribution: `seemseam-hippos`
- npm package: `hippos`
- CLI command: `hippos`
- Python import package: `hippos`
- Project output directory: `.hippos/`
- User config directory: `~/.hippos/`
- Main index filename: `hippos-index.json`
- MCP tool namespace: `hippos.*`

Legacy names such as `hippocampus`, `.hippocampus/`,
`~/.hippocampus/`, and `hippocampus-index.json` should only be kept as a
short migration window. During that window, Hippos may read or migrate old
state, but new documentation, examples, and integrations should use the
`hippos` names.

## Install

### Python package install

Use this after the PyPI package is published:

```bash
python3 -m pip install seemseam-hippos
hippos --help
```

The Python dependency is published on PyPI as `seemseam-llmgateway`; the import
module remains `llmgateway`.

The PyPI project name may also appear as `seemseam_hippos` in release tooling;
Python packaging normalizes underscores and hyphens to the same project name.

### npm global install

npm distribution is deferred. When the npm launcher is published later, it will
install the Python package from PyPI and expose the same `hippos` command:

```bash
npm install -g hippos
hippos --help
```

Useful npm launcher overrides after npm publication:

```bash
HIPPOS_NPM_PYTHON=python3.11 hippos --help
HIPPOS_NPM_CACHE_DIR=/tmp/hippos-cache hippos .
HIPPOS_NPM_PIP_SPEC='seemseam-hippos==0.1.7' hippos .
HIPPOS_NPM_LLMGATEWAY_PIP_SPEC='seemseam-llmgateway>=0.1.2' hippos .
```

### Source install

This works for local development and current pre-release testing:

```bash
git clone https://github.com/SeemSeam/hippos.git
cd hippos
python3 -m pip install -e '.[dev,repomap]'
hippos --help
```

`./install.sh` also installs the Python llmgateway runtime from PyPI. Override
the default with `LLMGATEWAY_PIP_SPEC='seemseam-llmgateway>=0.1.2'` when needed.

For guided local configuration, run:

```bash
./install.sh
```

## Quick Start

Generate the standard Hippos artifacts for the current repository:

```bash
hippos .
```

Analyze another repository:

```bash
hippos /path/to/repo
```

Refresh an existing Hippos bundle:

```bash
hippos update
```

Force a full refresh:

```bash
hippos refresh .
```

Generate only the local index phases without LLM calls:

```bash
hippos index --no-llm .
```

## Common Commands

```bash
# Create project config and output directories
hippos init .

# Extract code signatures
hippos sig-extract .

# Generate repository tree data
hippos tree .

# Build the unified index
hippos index .

# Render structure prompts
hippos structure-prompt --profile map .
hippos structure-prompt --profile deep .
hippos structure-prompt-all .

# Inspect and navigate the index
hippos overview .
hippos search --pattern auth .
hippos search --tags api --tags config .
hippos expand src/your_package/cli .

# Visualize
hippos viz --open .

# Save and compare history
hippos snapshot save -m "baseline" .
hippos snapshot list .
hippos snapshot show latest .
hippos diff latest~1 latest .
hippos stats --history .
```

## Output Files

The target output directory is `.hippos/` in the analyzed repository. During
the migration window, builds may still read or migrate legacy `.hippocampus/`
state.

- `hippos-index.json`: unified repository index.
- `code-signatures.json`: extracted symbols and file signatures.
- `tree.json`: normalized repository tree.
- `structure-prompt.md`: default structure prompt.
- `structure-prompt-map.md`: compact map-oriented structure prompt.
- `structure-prompt-deep.md`: deeper implementation-oriented structure prompt.
- `hippos-viz.html`: interactive visualization.
- `architect-metrics.json`: architecture metrics when `architec` integration is
  available.
- `snapshots/`: archived index snapshots for `snapshot`, `diff`, and `stats`
  workflows.

## LLM Configuration

Hippos uses `llmgateway` for provider access. Keep API keys out of the
repository and configure them in your user environment or local config files.

Typical config locations:

- `~/.llmgateway/config.yaml`: providers, routing, API keys, concurrency.
- `~/.hippos/config.yaml`: Hippos task-to-model-tier mapping.
- `.hippos/config.yaml`: optional project-local override.

Migration builds may read `~/.hippocampus/config.yaml` or
`.hippocampus/config.yaml` and should guide users to move them to the new
locations.

Minimal example:

```yaml
# ~/.llmgateway/config.yaml
version: 1
settings:
  strong_model: gpt-4.1
  weak_model: gpt-4.1-mini
  max_concurrent: 30
provider:
  provider_type: openai
  api_key: ${OPENAI_API_KEY}
```

```yaml
# ~/.hippos/config.yaml
version: 1
tasks:
  phase_1:
    tier: weak
  phase_2a:
    tier: strong
  phase_3b:
    tier: strong
structure_prompt_profile: map
```

## Python API

The target Python import package is `hippos`:

```python
from hippos import build_tree, extract_signatures, generate_structure_prompt

extract_signatures("/path/to/repo")
build_tree("/path/to/repo")
generate_structure_prompt("/path/to/repo", profile="map")
```

Early migration builds may still expose the legacy `hippocampus` package while
the package directory rename is in progress. Do not use that name for new
long-lived integrations.

## Development

```bash
python3 -m pip install -e '.[dev,repomap]'
PYTHONPATH=src pytest -q
npm run test
npm pack --dry-run
```

Keep these versions synchronized for release work:

- `package.json`
- `pyproject.toml`
- `src/hippos/__init__.py`

PyPI Trusted Publishing is configured for repository `SeemSeam/hippos`,
workflow `.github/workflows/release.yml`, and environment `pypi`.

See [NPM_RELEASE.md](NPM_RELEASE.md) for npm launcher release notes.

## License

MIT License. See [LICENSE](LICENSE).
