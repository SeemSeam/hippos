#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const PACKAGE_JSON = JSON.parse(
  fs.readFileSync(path.join(PACKAGE_ROOT, "package.json"), "utf8"),
);
const VERSION = PACKAGE_JSON.version;
const DEFAULT_SOURCE = `seemseam-hippos==${VERSION}`;
const PYTHON_SPEC = process.env.HIPPOS_NPM_PIP_SPEC || DEFAULT_SOURCE;
const PYTHON_LLMGATEWAY_SPEC =
  process.env.HIPPOS_NPM_LLMGATEWAY_PIP_SPEC ||
  "seemseam-llmgateway>=0.1.2";
const CACHE_ROOT =
  process.env.HIPPOS_NPM_CACHE_DIR ||
  path.join(os.homedir(), ".cache", "hippos", "npm");
const VENV_DIR = path.join(CACHE_ROOT, VERSION, "venv");
const MARKER_PATH = path.join(CACHE_ROOT, VERSION, "install.json");

function fail(message, detail) {
  console.error(`hippos npm launcher: ${message}`);
  if (detail) {
    console.error(detail);
  }
  process.exit(1);
}

function run(command, args, options = {}) {
  return spawnSync(command, args, {
    stdio: options.stdio || "pipe",
    encoding: options.encoding === false ? undefined : "utf8",
    env: process.env,
  });
}

function commandWorks(command) {
  const result = run(command, ["--version"]);
  return !result.error && result.status === 0;
}

function pythonVersion(command) {
  const result = run(command, [
    "-c",
    "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
  ]);
  if (result.error || result.status !== 0) {
    return null;
  }
  const [major, minor] = String(result.stdout || "").trim().split(".").map(Number);
  if (!Number.isInteger(major) || !Number.isInteger(minor)) {
    return null;
  }
  return { major, minor };
}

function findPython() {
  const configured = process.env.HIPPOS_NPM_PYTHON;
  const candidates = configured ? [configured] : ["python3", "python"];
  for (const candidate of candidates) {
    if (!commandWorks(candidate)) {
      continue;
    }
    const version = pythonVersion(candidate);
    if (version && (version.major > 3 || (version.major === 3 && version.minor >= 10))) {
      return candidate;
    }
  }
  return null;
}

function venvPython() {
  if (process.platform === "win32") {
    return path.join(VENV_DIR, "Scripts", "python.exe");
  }
  return path.join(VENV_DIR, "bin", "python");
}

function installedMarkerMatches() {
  try {
    const marker = JSON.parse(fs.readFileSync(MARKER_PATH, "utf8"));
    return (
      marker.version === VERSION &&
      marker.pythonSpec === PYTHON_SPEC &&
      marker.pythonLlmgatewaySpec === PYTHON_LLMGATEWAY_SPEC
    );
  } catch {
    return false;
  }
}

function ensureVenv() {
  const targetPython = venvPython();
  if (fs.existsSync(targetPython) && installedMarkerMatches()) {
    return targetPython;
  }

  const python = findPython();
  if (!python) {
    fail(
      "Python 3.10+ is required.",
      "Set HIPPOS_NPM_PYTHON to a Python 3.10+ executable, or install the Python package directly with pip.",
    );
  }

  fs.mkdirSync(path.dirname(VENV_DIR), { recursive: true });
  let result = run(python, ["-m", "venv", VENV_DIR], { stdio: "inherit" });
  if (result.error || result.status !== 0) {
    fail("failed to create the Python virtual environment");
  }

  result = run(targetPython, ["-m", "pip", "install", "--upgrade", PYTHON_LLMGATEWAY_SPEC], {
    stdio: "inherit",
  });
  if (result.error || result.status !== 0) {
    fail(
      "failed to install the Python llmgateway runtime.",
      `Tried: ${targetPython} -m pip install --upgrade "${PYTHON_LLMGATEWAY_SPEC}"`,
    );
  }

  result = run(targetPython, ["-m", "pip", "install", "--upgrade", PYTHON_SPEC], {
    stdio: "inherit",
  });
  if (result.error || result.status !== 0) {
    fail(
      "failed to install the Hippos Python CLI.",
      `Tried: ${targetPython} -m pip install --upgrade "${PYTHON_SPEC}"`,
    );
  }

  fs.writeFileSync(
    MARKER_PATH,
    `${JSON.stringify(
      {
        version: VERSION,
        pythonSpec: PYTHON_SPEC,
        pythonLlmgatewaySpec: PYTHON_LLMGATEWAY_SPEC,
      },
      null,
      2,
    )}\n`,
  );
  return targetPython;
}

const python = ensureVenv();
const child = spawnSync(python, ["-m", "hippos.cli", ...process.argv.slice(2)], {
  stdio: "inherit",
  env: process.env,
});

if (child.error) {
  fail("failed to start the Hippos Python CLI", child.error.message);
}
process.exit(child.status === null ? 1 : child.status);
