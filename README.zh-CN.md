# Hippos

[English README](README.md)

Hippos 是代码库索引、导航和结构分析工具。它会把一个仓库整理成适合人和
LLM 使用的产物：源码签名、目录树、统一代码索引、结构提示词、导航片段、
快照、差异、统计信息和交互式 HTML 可视化页面。

公开身份全面使用 `hippos`。早期重构版本里残留的 `hippocampus` 名称只属于
迁移细节，不是新集成应该依赖的稳定 API 名称。

## 功能介绍

- 生成代码库结构地图，帮助人或 LLM 快速理解项目。
- 基于 tree-sitter 提取多语言源码签名。
- 生成统一的 Hippos 索引，包含文件、模块、标签和依赖相关摘要。
- 支持 `map`、`deep`、`auto` 三种结构提示词渲染模式。
- 支持增量刷新，尽量复用缓存并只处理发生变化的内容。
- 提供搜索、展开、概览、统计、快照、差异对比等代码导航命令。
- 根据 Hippos 索引生成交互式 HTML 可视化页面。
- 可选接入 RepoMap 排名与上下文裁剪能力。
- 可选配合 `architec` 输出架构度量和架构审查工作流。
- 提供 MCP 导航工具，包括 `hippos.navigate`，方便 agent 集成。

## 环境要求

- Python 3.10 或更新版本。
- 只有源码安装时需要 Git。
- 仅使用 npm 启动器时需要 Node.js 18 或更新版本。
- 运行完整索引流水线时需要配置 LLM provider。

## 命名与迁移

全流程重构的目标命名是：

- Python distribution：`seemseam-hippos`
- npm package：`hippos`
- CLI command：`hippos`
- Python import package：`hippos`
- 项目输出目录：`.hippos/`
- 用户配置目录：`~/.hippos/`
- 主索引文件：`hippos-index.json`
- MCP tool namespace：`hippos.*`

`hippocampus`、`.hippocampus/`、`~/.hippocampus/`、
`hippocampus-index.json` 这些旧名称只保留为短期迁移窗口。迁移期内可以读
取或迁移旧状态，但新的文档、示例和集成都应该使用 `hippos` 命名。

## 安装

### Python 包安装

PyPI 包发布后使用：

```bash
python3 -m pip install seemseam-hippos
hippos --help
```

Python 依赖在 PyPI 上的 distribution 名称是 `seemseam-llmgateway`，import
模块名仍是 `llmgateway`。

发布配置中也可能写作 `seemseam_hippos`；Python packaging 会把下划线和连
字符归一化为同一个项目名。

### npm 全局安装

npm 分发暂缓。后续 npm 启动器发布后，它会从 PyPI 安装 Python 包，并暴露同
一个 `hippos` 命令：

```bash
npm install -g hippos
hippos --help
```

后续 npm 发布后的常用启动器覆盖项：

```bash
HIPPOS_NPM_PYTHON=python3.11 hippos --help
HIPPOS_NPM_CACHE_DIR=/tmp/hippos-cache hippos .
HIPPOS_NPM_PIP_SPEC='seemseam-hippos==0.1.9' hippos .
HIPPOS_NPM_LLMGATEWAY_PIP_SPEC='seemseam-llmgateway>=0.1.2' hippos .
```

### 源码安装

适合当前预发布测试和本地开发：

```bash
git clone https://github.com/SeemSeam/hippos.git
cd hippos
python3 -m pip install -e '.[dev,repomap]'
hippos --help
```

`./install.sh` 也会从 PyPI 安装 Python llmgateway 运行时。如需覆盖默认值，
可以设置 `LLMGATEWAY_PIP_SPEC='seemseam-llmgateway>=0.1.2'`。

如需交互式本地配置引导，可以运行：

```bash
./install.sh
```

## 快速开始

为当前仓库生成标准 Hippos 产物：

```bash
hippos .
```

分析其他仓库：

```bash
hippos /path/to/repo
```

增量刷新已有 Hippos 产物：

```bash
hippos update
```

强制全量刷新：

```bash
hippos refresh .
```

只生成本地索引阶段，不发起 LLM 调用：

```bash
hippos index --no-llm .
```

## 常用命令

```bash
# 创建项目配置和输出目录
hippos init .

# 提取代码签名
hippos sig-extract .

# 生成目录树数据
hippos tree .

# 构建统一索引
hippos index .

# 渲染结构提示词
hippos structure-prompt --profile map .
hippos structure-prompt --profile deep .
hippos structure-prompt-all .

# 查看和导航索引
hippos overview .
hippos search --pattern auth .
hippos search --tags api --tags config .
hippos expand src/your_package/cli .

# 可视化
hippos viz --open .

# 保存和对比历史
hippos snapshot save -m "baseline" .
hippos snapshot list .
hippos snapshot show latest .
hippos diff latest~1 latest .
hippos stats --history .
```

## 输出文件

目标输出目录是被分析仓库里的 `.hippos/`。迁移窗口内，构建版本可能仍会读
取或迁移旧的 `.hippocampus/` 状态。

- `hippos-index.json`：统一代码库索引。
- `code-signatures.json`：源码符号和文件签名。
- `tree.json`：规范化目录树。
- `structure-prompt.md`：默认结构提示词。
- `structure-prompt-map.md`：偏地图视角的紧凑结构提示词。
- `structure-prompt-deep.md`：偏实现细节的深度结构提示词。
- `hippos-viz.html`：交互式可视化页面。
- `architect-metrics.json`：接入 `architec` 时生成的架构度量。
- `snapshots/`：供 `snapshot`、`diff`、`stats` 使用的索引快照。

## LLM 配置

Hippos 通过 `llmgateway` 访问模型 provider。不要把 API key 提交进仓库，
建议使用用户级配置或环境变量。

常见配置位置：

- `~/.llmgateway/config.yaml`：provider、路由、API key、并发配置。
- `~/.hippos/config.yaml`：Hippos 任务到模型层级的映射。
- `.hippos/config.yaml`：可选的项目级覆盖配置。

迁移版本可以读取 `~/.hippocampus/config.yaml` 或
`.hippocampus/config.yaml`，并提示用户迁移到新位置。

最小示例：

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

目标 Python import 包名是 `hippos`：

```python
from hippos import build_tree, extract_signatures, generate_structure_prompt

extract_signatures("/path/to/repo")
build_tree("/path/to/repo")
generate_structure_prompt("/path/to/repo", profile="map")
```

早期迁移版本在包目录重命名完成前，可能仍暴露旧的 `hippocampus` 包名。新
的长期集成不要再依赖这个旧名称。

## 开发

```bash
python3 -m pip install -e '.[dev,repomap]'
PYTHONPATH=src pytest -q
npm run test
npm pack --dry-run
```

发布前需要保持以下版本一致：

- `package.json`
- `pyproject.toml`
- `src/hippos/__init__.py`

PyPI Trusted Publishing 配置为 repository `SeemSeam/hippos`、workflow
`.github/workflows/release.yml`、environment `pypi`。

npm 启动器发布说明见 [NPM_RELEASE.md](NPM_RELEASE.md)。

## License

MIT License. See [LICENSE](LICENSE).
