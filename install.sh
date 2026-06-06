#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/pyproject.toml" ]]; then
  ROOT_DIR="$SCRIPT_DIR"
elif [[ -f "$SCRIPT_DIR/../pyproject.toml" ]]; then
  ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  echo "Could not locate repository root from $SCRIPT_DIR" >&2
  exit 1
fi

USER_CONFIG_BASE="${HIPPOS_USER_CONFIG_DIR:-$HOME/.hippos}"
if [[ -n "${HIPPOS_LLM_CONFIG:-}" ]]; then
  LLM_CONFIG_PATH="${HIPPOS_LLM_CONFIG}"
else
  LLM_CONFIG_PATH="$USER_CONFIG_BASE/config.yaml"
fi
LLM_CONFIG_BASE="$(dirname "$LLM_CONFIG_PATH")"

LLMGATEWAY_USER_CONFIG_BASE="${LLMGATEWAY_USER_CONFIG_DIR:-$HOME/.llmgateway}"
if [[ -n "${LLMGATEWAY_CONFIG:-}" ]]; then
  LLMGATEWAY_CONFIG_PATH="${LLMGATEWAY_CONFIG}"
else
  LLMGATEWAY_CONFIG_PATH="$LLMGATEWAY_USER_CONFIG_BASE/config.yaml"
fi
LLMGATEWAY_CONFIG_BASE="$(dirname "$LLMGATEWAY_CONFIG_PATH")"
LLMGATEWAY_PIP_SPEC="${LLMGATEWAY_PIP_SPEC:-seemseam-llmgateway>=0.1.2}"

cd "$ROOT_DIR"

is_interactive() {
  [[ -t 0 && -t 1 ]]
}

prompt_with_default() {
  local var_name="$1"
  local prompt_text="$2"
  local default_value="${3:-}"
  local value="${!var_name:-}"

  if [[ -n "$value" ]]; then
    printf -v "$var_name" '%s' "$value"
    return 0
  fi

  if ! is_interactive; then
    printf -v "$var_name" '%s' "$default_value"
    return 0
  fi

  read -r -p "$prompt_text" value
  if [[ -z "$value" ]]; then
    value="$default_value"
  fi
  printf -v "$var_name" '%s' "$value"
}

prompt_optional() {
  local var_name="$1"
  local prompt_text="$2"
  local secret="${3:-0}"
  local default_value="${4:-}"
  local value="${!var_name:-}"

  if [[ -n "$value" ]]; then
    printf -v "$var_name" '%s' "$value"
    return 0
  fi

  if ! is_interactive; then
    printf -v "$var_name" '%s' "$default_value"
    return 0
  fi

  if [[ "$secret" == "1" ]]; then
    read -r -s -p "$prompt_text" value
    echo
  else
    read -r -p "$prompt_text" value
  fi
  if [[ -z "$value" ]]; then
    value="$default_value"
  fi
  printf -v "$var_name" '%s' "$value"
}

load_existing_gateway_config() {
  if [[ ! -f "$LLMGATEWAY_CONFIG_PATH" ]]; then
    return 0
  fi

  local loaded=""
  loaded="$(python3 - "$LLMGATEWAY_CONFIG_PATH" <<'PY'
import json
import sys
from pathlib import Path

from llmgateway.config import load_user_config, runtime_spec_from_dict

path = Path(sys.argv[1])
raw = load_user_config(path)
if not raw:
    print("\t\t\t\t\t\t\t\t\t\t")
    raise SystemExit(0)
runtime = runtime_spec_from_dict(raw)
print(
    "\t".join(
        [
            str(runtime.provider.provider_type or "").strip(),
            str(runtime.provider.api_style or "").strip(),
            str(runtime.provider.base_url or "").strip(),
            str(runtime.provider.api_key or "").strip(),
            str(runtime.max_concurrent or "").strip(),
            json.dumps(dict(runtime.provider.model_map or {}), ensure_ascii=True, sort_keys=True),
            str(runtime.retry_max or "").strip(),
            str(runtime.timeout or "").strip(),
            str(runtime.strong_model or "").strip(),
            str(runtime.weak_model or "").strip(),
            str(runtime.strong_reasoning_effort or "").strip().lower(),
            str(runtime.weak_reasoning_effort or "").strip().lower(),
        ]
    )
)
PY
)"

  local loaded_provider_type loaded_api_style loaded_url loaded_key loaded_max_concurrent loaded_model_map loaded_retry_max loaded_timeout loaded_strong_model loaded_weak_model loaded_strong_effort loaded_weak_effort
  IFS=$'\t' read -r loaded_provider_type loaded_api_style loaded_url loaded_key loaded_max_concurrent loaded_model_map loaded_retry_max loaded_timeout loaded_strong_model loaded_weak_model loaded_strong_effort loaded_weak_effort <<<"$loaded"
  if [[ -z "${gateway_provider_type:-}" && -n "$loaded_provider_type" ]]; then
    gateway_provider_type="$loaded_provider_type"
  fi
  if [[ -z "${gateway_api_style:-}" && -n "$loaded_api_style" ]]; then
    gateway_api_style="$loaded_api_style"
  fi
  if [[ -z "${gateway_base_url:-}" && -n "$loaded_url" ]]; then
    gateway_base_url="$loaded_url"
  fi
  if [[ -z "${gateway_api_key:-}" && -n "$loaded_key" ]]; then
    gateway_api_key="$loaded_key"
  fi
  if [[ -z "${gateway_max_concurrent:-}" && -n "$loaded_max_concurrent" ]]; then
    gateway_max_concurrent="$loaded_max_concurrent"
  fi
  if [[ -z "${gateway_model_map_json:-}" && -n "$loaded_model_map" ]]; then
    gateway_model_map_json="$loaded_model_map"
  fi
  if [[ -z "${gateway_retry_max:-}" && -n "$loaded_retry_max" ]]; then
    gateway_retry_max="$loaded_retry_max"
  fi
  if [[ -z "${gateway_timeout:-}" && -n "$loaded_timeout" ]]; then
    gateway_timeout="$loaded_timeout"
  fi
  if [[ -z "${hippos_llm_strong_model:-}" && -n "$loaded_strong_model" ]]; then
    hippos_llm_strong_model="$loaded_strong_model"
  fi
  if [[ -z "${hippos_llm_weak_model:-}" && -n "$loaded_weak_model" ]]; then
    hippos_llm_weak_model="$loaded_weak_model"
  fi
  if [[ -z "${hippos_llm_strong_reasoning_effort:-}" && -n "$loaded_strong_effort" ]]; then
    hippos_llm_strong_reasoning_effort="$loaded_strong_effort"
  fi
  if [[ -z "${hippos_llm_weak_reasoning_effort:-}" && -n "$loaded_weak_effort" ]]; then
    hippos_llm_weak_reasoning_effort="$loaded_weak_effort"
  fi
}

write_gateway_config() {
  mkdir -p "$LLMGATEWAY_CONFIG_BASE"
  python3 - "$LLMGATEWAY_CONFIG_PATH" "$gateway_provider_type" "$gateway_api_style" "$gateway_base_url" "$gateway_api_key" "$gateway_max_concurrent" "$gateway_model_map_json" "$gateway_retry_max" "$gateway_timeout" "$hippos_llm_strong_model" "$hippos_llm_weak_model" "$hippos_llm_strong_reasoning_effort" "$hippos_llm_weak_reasoning_effort" <<'PY'
import json
import sys
from pathlib import Path

from llmgateway.config import write_user_config

config_path = Path(sys.argv[1])
provider_type = str(sys.argv[2] or "").strip()
api_style = str(sys.argv[3] or "").strip()
base_url = str(sys.argv[4] or "").strip()
api_key = str(sys.argv[5] or "").strip()
max_concurrent = max(1, int(sys.argv[6] or 20))
model_map = json.loads(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7] else {}
if not isinstance(model_map, dict):
    model_map = {}
retry_max = max(0, int(sys.argv[8] or 3))
timeout = float(sys.argv[9] or 30)
strong_model = str(sys.argv[10] or "").strip()
weak_model = str(sys.argv[11] or "").strip()
strong_reasoning_effort = str(sys.argv[12] or "").strip().lower()
weak_reasoning_effort = str(sys.argv[13] or "").strip().lower()

write_user_config(
    {
        "version": 1,
        "provider": {
            "provider_type": provider_type,
            "api_style": api_style,
            "base_url": base_url,
            "api_key": api_key,
            "headers": {},
            "model_map": model_map,
        },
        "settings": {
            "strong_model": strong_model,
            "weak_model": weak_model,
            "strong_reasoning_effort": strong_reasoning_effort,
            "weak_reasoning_effort": weak_reasoning_effort,
            "max_concurrent": max_concurrent,
            "retry_max": retry_max,
            "timeout": timeout,
        },
    },
    config_path,
)
PY
  chmod 600 "$LLMGATEWAY_CONFIG_PATH"
}

write_hippos_config() {
  mkdir -p "$LLM_CONFIG_BASE"
  python3 - "$LLM_CONFIG_PATH" "$hippos_llm_weak_model" "$hippos_llm_strong_model" "$hippos_llm_weak_reasoning_effort" "$hippos_llm_strong_reasoning_effort" <<'PY'
import sys
from pathlib import Path

from hippos.user_llm_config import write_user_llm_config

write_user_llm_config(
    Path(sys.argv[1]),
    model=sys.argv[2],
    weak_model=sys.argv[2],
    strong_model=sys.argv[3],
    weak_reasoning_effort=sys.argv[4],
    strong_reasoning_effort=sys.argv[5],
)
PY
  chmod 600 "$LLM_CONFIG_PATH"
}

validate_llm_config() {
  python3 - "$ROOT_DIR" <<'PY'
import sys
from pathlib import Path

from hippos.config import load_config, require_llm_configured

root = Path(sys.argv[1]).resolve()
cfg = load_config(None, project_root=root)
require_llm_configured(cfg)
assert str(cfg.llm.base_url or cfg.llm.api_base or "").strip()
assert str(cfg.llm.api_key or "").strip()
assert str(cfg.llm.phase_models.phase_1 or "").strip()
assert str(cfg.llm.phase_models.phase_2a or "").strip()
PY
}

print_manual_config_hint() {
  echo "Hippos model config written to $LLM_CONFIG_PATH"
  echo "Still missing gateway route config. Create $LLMGATEWAY_CONFIG_PATH"
  cat <<EOF
Minimal ~/.llmgateway/config.yaml:
version: 1
provider:
  provider_type: glm
  api_style: openai_responses
  base_url: https://your-backend.example
  api_key: your-api-key
  headers: {}
  model_map: {}
settings:
  strong_model: gpt-5.4
  weak_model: gpt-5.4
  strong_reasoning_effort: high
  weak_reasoning_effort: low
  max_concurrent: 20
  retry_max: 3
  timeout: 30

Minimal ~/.hippos/config.yaml:
version: 1
tasks:
  phase_1:
    tier: weak
  phase_2a:
    tier: strong
  phase_2b:
    tier: weak
  phase_3a:
    tier: weak
  phase_3b:
    tier: strong
  architect:
    tier: strong
EOF
}

install_llmgateway() {
  echo "Installing Python llmgateway runtime from PyPI: $LLMGATEWAY_PIP_SPEC"
  python3 -m pip install --upgrade "$LLMGATEWAY_PIP_SPEC"
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage: ./install.sh

Installs hippos from the current source checkout into the active Python
environment as an editable package, including dev and repomap dependencies.
Also installs the Python llmgateway dependency from PyPI
(default: seemseam-llmgateway>=0.1.2).
Writes ~/.llmgateway/config.yaml for provider/API/concurrency settings and
LLMGateway strong/weak model settings, plus ~/.hippos/config.yaml for
Hippos task-tier routing.
If you skip URL or API key, install still writes the Hippos task-tier config and
prints the manual gateway config path.
Existing llmgateway, Hippos, or Architec configs are reused as defaults.
EOF
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "install.sh takes no arguments." >&2
  exit 1
fi

python3 -m pip install --upgrade pip
install_llmgateway
python3 -m pip install -e ".[dev,repomap]"

gateway_provider_type="${gateway_provider_type:-${hippos_llm_provider_type:-glm}}"
gateway_api_style="${gateway_api_style:-${hippos_llm_api_style:-openai_responses}}"
gateway_base_url="${gateway_base_url:-${hippos_llm_base_url:-}}"
gateway_api_key="${gateway_api_key:-${hippos_llm_api_key:-}}"
gateway_max_concurrent="${gateway_max_concurrent:-${hippos_llm_max_concurrent:-20}}"
gateway_model_map_json="${gateway_model_map_json:-${hippos_llm_model_map_json:-}}"
gateway_retry_max="${gateway_retry_max:-3}"
gateway_timeout="${gateway_timeout:-30}"

hippos_llm_weak_model="${hippos_llm_weak_model:-${hippos_llm_model:-gpt-5.4}}"
hippos_llm_strong_model="${hippos_llm_strong_model:-gpt-5.4}"
hippos_llm_weak_reasoning_effort="${hippos_llm_weak_reasoning_effort:-low}"
hippos_llm_strong_reasoning_effort="${hippos_llm_strong_reasoning_effort:-high}"

load_existing_gateway_config
if is_interactive; then
  prompt_optional gateway_base_url "LLMGateway base URL (leave blank to skip): " 0 "$gateway_base_url"
  prompt_optional gateway_api_key "LLMGateway API key (leave blank to skip): " 1 "$gateway_api_key"
  if [[ -n "$gateway_base_url" && -n "$gateway_api_key" ]]; then
    prompt_with_default gateway_provider_type "LLMGateway provider type [$gateway_provider_type]: " "$gateway_provider_type"
    prompt_with_default gateway_api_style "LLMGateway API style [$gateway_api_style]: " "$gateway_api_style"
    prompt_with_default gateway_max_concurrent "LLMGateway max concurrent [$gateway_max_concurrent]: " "$gateway_max_concurrent"
    prompt_with_default gateway_retry_max "LLMGateway retry max [$gateway_retry_max]: " "$gateway_retry_max"
    prompt_with_default gateway_timeout "LLMGateway timeout [$gateway_timeout]: " "$gateway_timeout"
  fi
  prompt_with_default hippos_llm_weak_model "LLMGateway weak model [$hippos_llm_weak_model]: " "$hippos_llm_weak_model"
  prompt_with_default hippos_llm_strong_model "LLMGateway strong model [$hippos_llm_strong_model]: " "$hippos_llm_strong_model"
  prompt_with_default hippos_llm_weak_reasoning_effort "LLMGateway weak reasoning effort [$hippos_llm_weak_reasoning_effort]: " "$hippos_llm_weak_reasoning_effort"
  prompt_with_default hippos_llm_strong_reasoning_effort "LLMGateway strong reasoning effort [$hippos_llm_strong_reasoning_effort]: " "$hippos_llm_strong_reasoning_effort"
fi

write_hippos_config

if [[ -z "$gateway_base_url" || -z "$gateway_api_key" ]]; then
  print_manual_config_hint
  exit 0
fi

write_gateway_config
validate_llm_config

echo "Saved LLMGateway config to $LLMGATEWAY_CONFIG_PATH"
echo "Saved Hippos LLM config to $LLM_CONFIG_PATH"
